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
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
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
        asset_mint TEXT, asset_decimals INTEGER NOT NULL DEFAULT 9,
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
    columns = {row[1] for row in db.execute("PRAGMA table_info(payment_intents)")}
    if "asset_mint" not in columns:
        db.execute("ALTER TABLE payment_intents ADD COLUMN asset_mint TEXT")
    if "asset_decimals" not in columns:
        db.execute("ALTER TABLE payment_intents ADD COLUMN asset_decimals INTEGER NOT NULL DEFAULT 9")
    return db


def create_intent(db: sqlite3.Connection, *, idempotency_key: str, item_id: str,
                  category: str, amount_lamports: int, price_usd: str,
                  merchant: str, buyer: str | None = None, ttl_minutes: int = 30,
                  asset_mint: str | None = None, asset_decimals: int = 9) -> dict:
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
    if asset_mint is not None:
        asset_mint = validate_pubkey(asset_mint)
        if not isinstance(asset_decimals, int) or not 0 <= asset_decimals <= 9:
            raise ValueError("invalid token decimals")
    elif asset_decimals != 9:
        raise ValueError("native SOL uses 9 decimals")
    existing = db.execute("SELECT * FROM payment_intents WHERE idempotency_key=?", (idempotency_key,)).fetchone()
    if existing:
        public = dict(existing)
        public.pop("refund_token_hash", None)
        return public | {"refund_token": None, "network": "devnet"}
    intent_id = secrets.token_urlsafe(18)
    refund_token = secrets.token_urlsafe(32)
    token_hash = __import__("hashlib").sha256(refund_token.encode()).hexdigest()
    now = utc_now()
    expires = now + dt.timedelta(minutes=max(5, min(ttl_minutes, 120)))
    memo = "MOSUL:" + intent_id
    db.execute(
        """INSERT INTO payment_intents
        (id,idempotency_key,item_id,category,buyer,merchant,amount_lamports,asset_mint,asset_decimals,
         price_usd,memo,refund_token_hash,status,created_at,expires_at,payment_signature,refund_signature)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (intent_id, idempotency_key, item_id, category, buyer, merchant, amount_lamports,
         asset_mint, asset_decimals, str(usd), memo, token_hash, "pending", now.isoformat(),
         expires.isoformat(), None, None),
    )
    db.commit()
    return {
        "id": intent_id, "item_id": item_id, "category": category, "buyer": buyer,
        "merchant": merchant, "amount_lamports": amount_lamports, "asset_mint": asset_mint,
        "asset_decimals": asset_decimals, "price_usd": str(usd),
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

    def token_mint(self, mint: str) -> dict | None:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo", "params": [mint, {
            "encoding": "jsonParsed", "commitment": "finalized"
        }]}
        request = urllib.request.Request(DEVNET_RPC, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read(1_000_000))
        if data.get("error"):
            raise RuntimeError("Solana devnet RPC rejected the mint lookup")
        return data.get("result", {}).get("value")


def _verified_transfer(transaction: dict, intent: sqlite3.Row) -> bool:
    if not transaction or transaction.get("meta", {}).get("err") is not None:
        return False
    if not _inside_intent_window(transaction, intent):
        return False
    message = transaction.get("transaction", {}).get("message", {})
    instructions = message.get("instructions", [])
    account_keys = message.get("accountKeys", [])
    signers = {item.get("pubkey") for item in account_keys if isinstance(item, dict) and item.get("signer")}
    transfer_ok = memo_ok = False
    for instruction in instructions:
        parsed = instruction.get("parsed")
        if instruction.get("program") == "system" and isinstance(parsed, dict) and parsed.get("type") == "transfer":
            info = parsed.get("info", {})
            transfer_ok = transfer_ok or (
                info.get("destination") == intent["merchant"]
                and info.get("lamports") == intent["amount_lamports"]
                and (not intent["buyer"] or info.get("source") == intent["buyer"])
                and info.get("source") in signers
            )
        if instruction.get("program") == "spl-memo":
            memo_ok = memo_ok or parsed == intent["memo"]
    return transfer_ok and memo_ok


def _verified_token_transfer(transaction: dict, intent: sqlite3.Row) -> bool:
    """Verify an exact Token-2022 transfer by parsed instruction and token balance deltas."""
    if (not transaction or transaction.get("meta", {}).get("err") is not None
            or not intent["asset_mint"] or not _inside_intent_window(transaction, intent)):
        return False
    meta = transaction.get("meta", {})
    message = transaction.get("transaction", {}).get("message", {})
    instructions = message.get("instructions", [])
    balances = {}
    for field in ("preTokenBalances", "postTokenBalances"):
        for entry in meta.get(field, []):
            if entry.get("mint") != intent["asset_mint"]:
                continue
            amount = entry.get("uiTokenAmount", {}).get("amount")
            decimals = entry.get("uiTokenAmount", {}).get("decimals")
            if not isinstance(amount, str) or decimals != intent["asset_decimals"]:
                return False
            key = entry.get("accountIndex")
            if key is not None:
                balances.setdefault(key, {})[field] = (entry.get("owner"), int(amount))
    debit_ok = credit_ok = transfer_ok = memo_ok = False
    for instruction in instructions:
        parsed = instruction.get("parsed")
        if instruction.get("programId") == TOKEN_2022_PROGRAM:
            if not isinstance(parsed, dict) or parsed.get("type") != "transferChecked":
                continue
            info = parsed.get("info", {})
            token_amount = info.get("tokenAmount", {})
            transfer_ok = transfer_ok or (
                info.get("mint") == intent["asset_mint"]
                and info.get("authority") == intent["buyer"]
                and token_amount.get("amount") == str(intent["amount_lamports"])
                and token_amount.get("decimals") == intent["asset_decimals"]
            )
            source_index = destination_index = None
            for index, key in enumerate(message.get("accountKeys", [])):
                address = key.get("pubkey") if isinstance(key, dict) else key
                if address == info.get("source"):
                    source_index = index
                if address == info.get("destination"):
                    destination_index = index
            source = balances.get(source_index, {})
            destination = balances.get(destination_index, {})
            source_owner = (source.get("preTokenBalances") or source.get("postTokenBalances") or (None, 0))[0]
            destination_owner = (destination.get("preTokenBalances") or destination.get("postTokenBalances") or (None, 0))[0]
            source_before = source.get("preTokenBalances", (None, 0))[1]
            source_after = source.get("postTokenBalances", (None, 0))[1]
            dest_before = destination.get("preTokenBalances", (None, 0))[1]
            dest_after = destination.get("postTokenBalances", (None, 0))[1]
            debit_ok = debit_ok or (source_owner == intent["buyer"] and source_before - source_after == intent["amount_lamports"])
            credit_ok = credit_ok or (destination_owner == intent["merchant"] and dest_after - dest_before == intent["amount_lamports"])
        if instruction.get("program") == "spl-memo" and parsed == intent["memo"]:
            memo_ok = True
    return transfer_ok and debit_ok and credit_ok and memo_ok


def _inside_intent_window(transaction: dict, intent: sqlite3.Row) -> bool:
    block_time = transaction.get("blockTime")
    if not isinstance(block_time, int):
        return False
    created = dt.datetime.fromisoformat(intent["created_at"]).timestamp()
    expires = dt.datetime.fromisoformat(intent["expires_at"]).timestamp()
    return created <= block_time <= expires


def _verified_refund(transaction: dict, intent: sqlite3.Row) -> bool:
    if not transaction or transaction.get("meta", {}).get("err") is not None:
        return False
    instructions = transaction.get("transaction", {}).get("message", {}).get("instructions", [])
    transfer_ok = memo_ok = False
    for instruction in instructions:
        parsed = instruction.get("parsed")
        if instruction.get("program") == "system" and isinstance(parsed, dict) and parsed.get("type") == "transfer":
            info = parsed.get("info", {})
            transfer_ok = transfer_ok or (
                info.get("source") == intent["merchant"]
                and info.get("destination") == intent["buyer"]
                and info.get("lamports") == intent["amount_lamports"]
            )
        if instruction.get("program") == "spl-memo" and parsed == "REFUND:" + intent["id"]:
            memo_ok = True
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
    verified = (_verified_token_transfer(transaction, intent) if intent["asset_mint"]
                else _verified_transfer(transaction, intent))
    if verified and intent["asset_mint"]:
        mint_account = rpc.token_mint(intent["asset_mint"])
        parsed_mint = (mint_account or {}).get("data", {}).get("parsed", {})
        mint_info = parsed_mint.get("info", {})
        verified = ((mint_account or {}).get("owner") == TOKEN_2022_PROGRAM
                    and parsed_mint.get("type") == "mint"
                    and mint_info.get("isInitialized") is True
                    and mint_info.get("decimals") == intent["asset_decimals"])
    if not verified:
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
    return {"id": intent_id, "status": "refund_requested", "network": "devnet"}


def process_refunds(db: sqlite3.Connection, keypair_path: str, rpc: DevnetRpc | None = None) -> list[dict]:
    keypair = Path(keypair_path)
    if not keypair.is_file():
        raise ValueError("devnet refund keypair file is missing")
    results = []
    rpc = rpc or DevnetRpc()
    rows = db.execute("SELECT * FROM payment_intents WHERE status='refund_requested' ORDER BY created_at").fetchall()
    for intent in rows:
        if not intent["buyer"]:
            continue
        with db:
            claimed = db.execute("UPDATE payment_intents SET status='refund_processing' WHERE id=? AND status='refund_requested'",
                                 (intent["id"],)).rowcount
        if not claimed:
            continue
        command = ["solana", "transfer", "--url", DEVNET_RPC, "--keypair", str(keypair),
                   "--lamports", str(intent["amount_lamports"]), "--allow-unfunded-recipient",
                   "--with-memo", "REFUND:" + intent["id"], intent["buyer"]]
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
        if completed.returncode:
            with db:
                db.execute("UPDATE payment_intents SET status='refund_requested' WHERE id=? AND status='refund_processing'",
                           (intent["id"],))
            results.append({"id": intent["id"], "status": "failed"})
            continue
        matches = SIGNATURE_RE.findall(completed.stdout)
        if not matches:
            with db:
                db.execute("UPDATE payment_intents SET status='refund_requested' WHERE id=? AND status='refund_processing'",
                           (intent["id"],))
            results.append({"id": intent["id"], "status": "ambiguous"})
            continue
        signature = matches[-1]
        try:
            signature = validate_signature(signature)
            refund_tx = rpc.transaction(signature)
        except (ValueError, RuntimeError, OSError, TimeoutError):
            # Keep the claim so a transfer whose RPC result is delayed cannot be sent twice.
            results.append({"id": intent["id"], "status": "unverified"})
            continue
        if not _verified_refund(refund_tx, intent):
            # The signature exists but its outcome is not yet proven. Do not retry automatically.
            results.append({"id": intent["id"], "status": "unverified"})
            continue
        with db:
            db.execute("UPDATE payment_intents SET status='refunded', refund_signature=? WHERE id=?",
                       (signature, intent["id"]))
        results.append({"id": intent["id"], "status": "refunded", "signature": signature})
    return results


def comparable_sales(db: sqlite3.Connection) -> dict:
    cutoff = (utc_now() - dt.timedelta(days=90)).isoformat()
    rows = db.execute("""SELECT s.* FROM completed_sales AS s
      JOIN payment_intents AS i ON i.id=s.intent_id
      WHERE s.sold_at>=? AND i.status='paid' ORDER BY s.sold_at DESC LIMIT 500""", (cutoff,)).fetchall()
    return {"comparables": [dict(row) for row in rows]}
