"""Devnet-only payment, settlement, refund, and first-party sales ledger."""
from __future__ import annotations

import datetime as dt
import json
import re
import secrets
import sqlite3
import subprocess
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

DEVNET_RPC = "https://api.devnet.solana.com"
MAX_LAMPORTS = 1_000_000_000_000
SIGNATURE_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{64,100}")


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def _base58_decode(value: str) -> bytes:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = 0
    for char in value:
        if char not in alphabet:
            raise ValueError("invalid base58")
        number = number * 58 + alphabet.index(char)
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    return b"\x00" * (len(value) - len(value.lstrip("1"))) + raw


def validate_pubkey(value: str) -> str:
    if not isinstance(value, str) or len(_base58_decode(value)) != 32:
        raise ValueError("invalid Solana public key")
    return value


def validate_signature(value: str) -> str:
    if not isinstance(value, str) or len(_base58_decode(value)) != 64:
        raise ValueError("invalid Solana transaction signature")
    return value


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS payment_intents (
        id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL,
        item_id TEXT NOT NULL, category TEXT NOT NULL, buyer TEXT,
        merchant TEXT NOT NULL, amount_lamports INTEGER NOT NULL,
        price_usd TEXT NOT NULL, memo TEXT UNIQUE NOT NULL,
        refund_token_hash TEXT NOT NULL, status TEXT NOT NULL,
        created_at TEXT NOT NULL, expires_at TEXT NOT NULL,
        payment_signature TEXT UNIQUE, refund_signature TEXT UNIQUE
      );
      CREATE TABLE IF NOT EXISTS completed_sales (
        transaction_id TEXT PRIMARY KEY, intent_id TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL, price_usd REAL NOT NULL, sold_at TEXT NOT NULL,
        source TEXT NOT NULL, status TEXT NOT NULL CHECK(status='sold'),
        FOREIGN KEY(intent_id) REFERENCES payment_intents(id)
      );
    """)
    return db


def create_intent(db: sqlite3.Connection, *, idempotency_key: str, item_id: str,
                  category: str, amount_lamports: int, price_usd: str,
                  merchant: str, buyer: str | None = None, ttl_minutes: int = 30) -> dict:
    if not idempotency_key or len(idempotency_key) > 100:
        raise ValueError("invalid idempotency key")
    if not item_id or not category:
        raise ValueError("item_id and category are required")
    if not isinstance(amount_lamports, int) or not 0 < amount_lamports <= MAX_LAMPORTS:
        raise ValueError("amount_lamports is outside the allowed devnet range")
    try:
        usd = Decimal(price_usd)
    except InvalidOperation:
        raise ValueError("invalid USD record price") from None
    if not Decimal("0") < usd <= Decimal("1000000"):
        raise ValueError("USD record price is outside the allowed range")
    merchant = validate_pubkey(merchant)
    buyer = validate_pubkey(buyer) if buyer else None
    existing = db.execute("SELECT * FROM payment_intents WHERE idempotency_key=?", (idempotency_key,)).fetchone()
    if existing:
        return dict(existing) | {"refund_token": None, "network": "devnet"}
    intent_id = secrets.token_urlsafe(18)
    refund_token = secrets.token_urlsafe(32)
    token_hash = __import__("hashlib").sha256(refund_token.encode()).hexdigest()
    now = utc_now()
    expires = now + dt.timedelta(minutes=max(5, min(ttl_minutes, 120)))
    memo = "MOSUL:" + intent_id
    db.execute(
        "INSERT INTO payment_intents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (intent_id, idempotency_key, item_id, category, buyer, merchant, amount_lamports,
         str(usd), memo, token_hash, "pending", now.isoformat(), expires.isoformat(), None, None),
    )
    db.commit()
    return {
        "id": intent_id, "item_id": item_id, "category": category, "buyer": buyer,
        "merchant": merchant, "amount_lamports": amount_lamports, "price_usd": str(usd),
        "memo": memo, "refund_token": refund_token, "status": "pending",
        "expires_at": expires.isoformat(), "network": "devnet",
    }


class DevnetRpc:
    def transaction(self, signature: str) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [signature, {
            "encoding": "jsonParsed", "commitment": "finalized", "maxSupportedTransactionVersion": 0
        }]}
        request = urllib.request.Request(DEVNET_RPC, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read(8_000_000))
        if data.get("error"):
            raise RuntimeError("Solana devnet RPC rejected the transaction lookup")
        return data.get("result")


def _verified_transfer(transaction: dict, intent: sqlite3.Row) -> bool:
    if not transaction or transaction.get("meta", {}).get("err") is not None:
        return False
    instructions = transaction.get("transaction", {}).get("message", {}).get("instructions", [])
    transfer_ok = memo_ok = False
    for instruction in instructions:
        parsed = instruction.get("parsed")
        if instruction.get("program") == "system" and isinstance(parsed, dict) and parsed.get("type") == "transfer":
            info = parsed.get("info", {})
            transfer_ok = transfer_ok or (
                info.get("destination") == intent["merchant"]
                and info.get("lamports") == intent["amount_lamports"]
                and (not intent["buyer"] or info.get("source") == intent["buyer"])
            )
        if instruction.get("program") == "spl-memo":
            memo_ok = memo_ok or parsed == intent["memo"]
    return transfer_ok and memo_ok


def confirm_payment(db: sqlite3.Connection, intent_id: str, signature: str, rpc: DevnetRpc) -> dict:
    signature = validate_signature(signature)
    intent = db.execute("SELECT * FROM payment_intents WHERE id=?", (intent_id,)).fetchone()
    if not intent:
        raise KeyError("payment intent not found")
    if intent["status"] == "paid" and intent["payment_signature"] == signature:
        return {"id": intent_id, "status": "paid", "signature": signature, "network": "devnet"}
    if intent["status"] != "pending":
        raise ValueError("payment intent cannot be confirmed in its current state")
    if utc_now() > dt.datetime.fromisoformat(intent["expires_at"]):
        db.execute("UPDATE payment_intents SET status='expired' WHERE id=?", (intent_id,)); db.commit()
        raise ValueError("payment intent expired")
    transaction = rpc.transaction(signature)
    if not _verified_transfer(transaction, intent):
        raise ValueError("finalized transaction does not match the exact devnet payment intent")
    sold_at = utc_now().isoformat()
    source = "https://solscan.io/tx/" + signature + "?cluster=devnet"
    with db:
        db.execute("UPDATE payment_intents SET status='paid', payment_signature=? WHERE id=?", (signature, intent_id))
        db.execute("INSERT INTO completed_sales VALUES (?,?,?,?,?,?, 'sold')",
                   (signature, intent_id, intent["category"], float(intent["price_usd"]), sold_at, source))
    return {"id": intent_id, "status": "paid", "signature": signature, "network": "devnet"}


def request_refund(db: sqlite3.Connection, intent_id: str, refund_token: str) -> dict:
    import hashlib, hmac
    intent = db.execute("SELECT * FROM payment_intents WHERE id=?", (intent_id,)).fetchone()
    if not intent:
        raise KeyError("payment intent not found")
    supplied = hashlib.sha256(refund_token.encode()).hexdigest()
    if not hmac.compare_digest(supplied, intent["refund_token_hash"]):
        raise PermissionError("invalid refund token")
    if intent["status"] == "refunded":
        return {"id": intent_id, "status": "refunded", "network": "devnet"}
    if intent["status"] != "paid":
        raise ValueError("only a paid intent can request a refund")
    with db:
        db.execute("UPDATE payment_intents SET status='refund_requested' WHERE id=?", (intent_id,))
        db.execute("DELETE FROM completed_sales WHERE intent_id=?", (intent_id,))
    return {"id": intent_id, "status": "refund_requested", "network": "devnet"}


def process_refunds(db: sqlite3.Connection, keypair_path: str) -> list[dict]:
    keypair = Path(keypair_path)
    if not keypair.is_file():
        raise ValueError("devnet refund keypair file is missing")
    results = []
    rows = db.execute("SELECT * FROM payment_intents WHERE status='refund_requested' ORDER BY created_at").fetchall()
    for intent in rows:
        if not intent["buyer"]:
            continue
        command = ["solana", "transfer", "--url", DEVNET_RPC, "--keypair", str(keypair),
                   "--lamports", str(intent["amount_lamports"]), "--allow-unfunded-recipient",
                   "--with-memo", "REFUND:" + intent["id"], intent["buyer"]]
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
        if completed.returncode:
            results.append({"id": intent["id"], "status": "failed"})
            continue
        matches = SIGNATURE_RE.findall(completed.stdout)
        if not matches:
            results.append({"id": intent["id"], "status": "ambiguous"})
            continue
        signature = matches[-1]
        with db:
            db.execute("UPDATE payment_intents SET status='refunded', refund_signature=? WHERE id=?",
                       (signature, intent["id"]))
        results.append({"id": intent["id"], "status": "refunded", "signature": signature})
    return results


def comparable_sales(db: sqlite3.Connection) -> dict:
    cutoff = (utc_now() - dt.timedelta(days=90)).isoformat()
    rows = db.execute("SELECT * FROM completed_sales WHERE sold_at>=? ORDER BY sold_at DESC LIMIT 500", (cutoff,)).fetchall()
    return {"comparables": [dict(row) for row in rows]}
