"""Fail-closed Solana Mainnet checkout for a single digital product."""
from __future__ import annotations

import base64
import datetime as dt
import decimal
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

MAINNET_RPC = "https://api.mainnet-beta.solana.com"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
SIGNATURE_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{64,100}$")
ORDER_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,80}$")
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def b58encode(raw: bytes) -> str:
    number = int.from_bytes(raw, "big")
    encoded = ""
    while number:
        number, rem = divmod(number, 58)
        encoded = BASE58[rem] + encoded
    zeroes = len(raw) - len(raw.lstrip(b"\0"))
    return "1" * zeroes + (encoded or ("" if zeroes else "1"))


def b58decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError("invalid base58 value")
    number = 0
    for char in value:
        try:
            number = number * 58 + BASE58.index(char)
        except ValueError:
            raise ValueError("invalid base58 value") from None
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    return b"\0" * (len(value) - len(value.lstrip("1"))) + raw


def validate_pubkey(value: str) -> str:
    if len(b58decode(value)) != 32:
        raise ValueError("invalid Solana public key")
    return value


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    category: str
    price_usdc: str
    amount_raw: int
    terms_version: str
    terms_sha256: str
    merchant_wallet: str = ""


def load_product(path: str | Path) -> Product:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = ("id", "title", "category", "price_usdc", "amount_raw",
                "terms_version", "terms_sha256")
    if any(name not in data or data[name] is None for name in required):
        raise ValueError("product configuration is incomplete")
    amount = int(data["amount_raw"])
    auction_only = data.get("sale_type") == "timed_ascending_auction"
    if amount < 0 or (amount == 0 and not auction_only):
        raise ValueError("product amount must be positive unless configured for auction")
    if not re.fullmatch(r"[0-9a-f]{64}", data["terms_sha256"]):
        raise ValueError("invalid terms hash")
    return Product(
        id=str(data["id"]), title=str(data["title"]), category=str(data["category"]),
        price_usdc=str(data["price_usdc"]), amount_raw=amount,
        terms_version=str(data["terms_version"]), terms_sha256=data["terms_sha256"],
        merchant_wallet=str(data.get("merchant_wallet", "")),
    )


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        idempotency_key TEXT UNIQUE NOT NULL,
        product_id TEXT NOT NULL,
        buyer_wallet TEXT,
        merchant_wallet TEXT NOT NULL,
        mint TEXT NOT NULL,
        amount_raw INTEGER NOT NULL,
        price_usd TEXT NOT NULL,
        reference_key TEXT UNIQUE NOT NULL,
        memo TEXT UNIQUE NOT NULL,
        claim_secret_hash TEXT NOT NULL,
        terms_version TEXT NOT NULL,
        terms_sha256 TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        payment_signature TEXT UNIQUE,
        paid_at TEXT,
        download_count INTEGER NOT NULL DEFAULT 0,
        auction_bid_id TEXT
      );
      CREATE TABLE IF NOT EXISTS completed_sales (
        transaction_id TEXT PRIMARY KEY,
        order_id TEXT UNIQUE NOT NULL,
        product_id TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        price_usd REAL NOT NULL,
        sold_at TEXT NOT NULL,
        source TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status='sold'),
        FOREIGN KEY(order_id) REFERENCES orders(id)
      );
      CREATE UNIQUE INDEX IF NOT EXISTS one_active_order_per_product
        ON orders(product_id) WHERE status IN ('pending','paid');
    """)
    columns = {row[1] for row in db.execute("PRAGMA table_info(orders)")}
    if "auction_bid_id" not in columns:
        db.execute("ALTER TABLE orders ADD COLUMN auction_bid_id TEXT")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_order_per_auction_bid "
               "ON orders(auction_bid_id) WHERE auction_bid_id IS NOT NULL")
    return db


def expire_stale(db: sqlite3.Connection, product_id: str) -> None:
    db.execute(
        "UPDATE orders SET status='expired' WHERE product_id=? AND status='pending' AND expires_at<?",
        (product_id, utc_now().isoformat()),
    )


def create_order(db: sqlite3.Connection, *, product: Product, merchant_wallet: str,
                 idempotency_key: str, buyer_wallet: str | None,
                 accepted_terms_sha256: str, ttl_minutes: int = 30,
                 price_usdc: str | None = None, auction_bid_id: str | None = None) -> dict:
    merchant_wallet = validate_pubkey(merchant_wallet)
    buyer_wallet = validate_pubkey(buyer_wallet) if buyer_wallet else None
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,100}", idempotency_key or ""):
        raise ValueError("invalid idempotency key")
    if not hmac.compare_digest(accepted_terms_sha256 or "", product.terms_sha256):
        raise PermissionError("the current buyer terms must be accepted")
    selected_price = price_usdc if price_usdc is not None else product.price_usdc
    try:
        amount = decimal.Decimal(selected_price)
    except (decimal.InvalidOperation, TypeError):
        raise ValueError("a valid price or winning bid is required") from None
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("payment must be a positive USDC amount with at most two decimals")
    amount_raw = int(amount * 1_000_000)
    formatted_price = str(amount.quantize(decimal.Decimal("0.01")))
    existing = db.execute(
        "SELECT * FROM orders WHERE idempotency_key=?", (idempotency_key,)
    ).fetchone()
    if existing:
        return public_order(existing, product)
    now = utc_now()
    expires = now + dt.timedelta(minutes=max(5, min(int(ttl_minutes), 1440)))
    order_id = secrets.token_urlsafe(24)
    claim_secret = secrets.token_urlsafe(32)
    claim_secret_hash = hashlib.sha256(claim_secret.encode()).hexdigest()
    reference = b58encode(secrets.token_bytes(32))
    memo = "MOSUL-SALE:" + order_id
    with db:
        expire_stale(db, product.id)
        sold = db.execute(
            "SELECT 1 FROM completed_sales WHERE product_id=?", (product.id,)
        ).fetchone()
        pending = db.execute(
            "SELECT 1 FROM orders WHERE product_id=? AND status='pending'", (product.id,)
        ).fetchone()
        if sold:
            raise ValueError("this one-of-one product has been sold")
        if pending:
            raise ValueError("this product is reserved by another active checkout")
        db.execute(
            """INSERT INTO orders
            (id,idempotency_key,product_id,buyer_wallet,merchant_wallet,mint,amount_raw,
             price_usd,reference_key,memo,claim_secret_hash,terms_version,terms_sha256,status,created_at,
             expires_at,payment_signature,paid_at,download_count,auction_bid_id)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?)""",
            (order_id, idempotency_key, product.id, buyer_wallet, merchant_wallet,
             USDC_MINT, amount_raw, formatted_price, reference, memo, claim_secret_hash,
             product.terms_version, product.terms_sha256, "pending", now.isoformat(),
             expires.isoformat(), None, None, auction_bid_id),
        )
    row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return public_order(row, product) | {"claim_secret": claim_secret}


def solana_pay_uri(order: sqlite3.Row, product: Product) -> str:
    query = urllib.parse.urlencode({
        "amount": order["price_usd"],
        "spl-token": order["mint"],
        "reference": order["reference_key"],
        "label": "MOSUL HERITAGE",
        "message": product.title,
        "memo": order["memo"],
    })
    return f"solana:{order['merchant_wallet']}?{query}"


def public_order(order: sqlite3.Row, product: Product) -> dict:
    result = {
        "id": order["id"], "product_id": order["product_id"],
        "title": product.title, "status": order["status"],
        "network": "mainnet-beta", "asset": "USDC", "mint": order["mint"],
        "amount_raw": order["amount_raw"], "amount": order["price_usd"],
        "merchant_wallet": order["merchant_wallet"],
        "reference": order["reference_key"], "memo": order["memo"],
        "terms_version": order["terms_version"],
        "terms_sha256": order["terms_sha256"], "expires_at": order["expires_at"],
    }
    if order["status"] == "pending":
        result["solana_pay_uri"] = solana_pay_uri(order, product)
    if order["payment_signature"]:
        result["payment_signature"] = order["payment_signature"]
    return result


class MainnetRpc:
    def __init__(self, url: str = MAINNET_RPC):
        if not url.startswith("https://"):
            raise ValueError("Mainnet RPC must use HTTPS")
        self.url = url

    def transaction(self, signature: str) -> dict | None:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [
            signature, {"encoding": "jsonParsed", "commitment": "finalized",
                        "maxSupportedTransactionVersion": 0}
        ]}
        request = urllib.request.Request(
            self.url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read(8_000_000))
        if data.get("error"):
            raise RuntimeError("Solana RPC rejected the transaction lookup")
        return data.get("result")


def _account_keys(transaction: dict) -> set[str]:
    keys = transaction.get("transaction", {}).get("message", {}).get("accountKeys", [])
    return {str(k.get("pubkey")) if isinstance(k, dict) else str(k) for k in keys}


def _token_amounts(balances: list[dict], mint: str, owner: str) -> dict[int, int]:
    result: dict[int, int] = {}
    for item in balances or []:
        if item.get("mint") != mint or item.get("owner") != owner:
            continue
        try:
            result[int(item["accountIndex"])] = int(item["uiTokenAmount"]["amount"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("malformed token balance in transaction") from None
    return result


def verify_transaction(transaction: dict | None, order: sqlite3.Row) -> None:
    if not transaction or transaction.get("meta", {}).get("err") is not None:
        raise ValueError("transaction is missing or failed")
    if order["reference_key"] not in _account_keys(transaction):
        raise ValueError("transaction does not contain the unique order reference")
    block_time = transaction.get("blockTime")
    if not isinstance(block_time, int):
        raise ValueError("transaction has no block time")
    created = int(dt.datetime.fromisoformat(order["created_at"]).timestamp()) - 60
    expires = int(dt.datetime.fromisoformat(order["expires_at"]).timestamp()) + 300
    if not created <= block_time <= expires:
        raise ValueError("transaction is outside the order validity window")
    meta = transaction.get("meta", {})
    before = _token_amounts(meta.get("preTokenBalances", []), order["mint"],
                            order["merchant_wallet"])
    after = _token_amounts(meta.get("postTokenBalances", []), order["mint"],
                           order["merchant_wallet"])
    received = sum(after.get(i, 0) - before.get(i, 0) for i in set(before) | set(after))
    if received != order["amount_raw"]:
        raise ValueError("finalized transaction does not contain the exact token payment")


def confirm_order(db: sqlite3.Connection, *, order_id: str, signature: str,
                  claim_secret: str, product: Product, rpc: MainnetRpc,
                  delivery_secret: str) -> dict:
    if not ORDER_ID_RE.fullmatch(order_id or ""):
        raise ValueError("invalid order id")
    if not SIGNATURE_RE.fullmatch(signature or "") or len(b58decode(signature)) != 64:
        raise ValueError("invalid Solana transaction signature")
    row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not row:
        raise KeyError("order not found")
    supplied = hashlib.sha256((claim_secret or "").encode()).hexdigest()
    if not hmac.compare_digest(supplied, row["claim_secret_hash"]):
        raise PermissionError("invalid order claim secret")
    if row["status"] == "paid" and row["payment_signature"] == signature:
        return paid_response(row, delivery_secret)
    if row["status"] != "pending":
        raise ValueError("order cannot be confirmed in its current state")
    if utc_now() > dt.datetime.fromisoformat(row["expires_at"]):
        with db:
            db.execute("UPDATE orders SET status='expired' WHERE id=?", (order_id,))
        raise ValueError("order expired")
    verify_transaction(rpc.transaction(signature), row)
    paid_at = utc_now().isoformat()
    with db:
        cursor = db.execute(
            "UPDATE orders SET status='paid',payment_signature=?,paid_at=? WHERE id=? AND status='pending'",
            (signature, paid_at, order_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("order changed while payment was being confirmed")
        db.execute(
            "INSERT INTO completed_sales VALUES (?,?,?,?,?,?,?,'sold')",
            (signature, order_id, product.id, product.category, float(row["price_usd"]),
             paid_at, "https://solscan.io/tx/" + signature),
        )
        if row["auction_bid_id"]:
            db.execute("UPDATE auction_bids SET status='paid' WHERE id=?",
                       (row["auction_bid_id"],))
    paid = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return paid_response(paid, delivery_secret)


def _download_token(order_id: str, secret: str, expires: int) -> str:
    if len(secret) < 32:
        raise ValueError("delivery secret must contain at least 32 characters")
    payload = f"{order_id}.{expires}"
    mac = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(mac).decode().rstrip("=")
    return f"{payload}.{signature}"


def paid_response(order: sqlite3.Row, secret: str) -> dict:
    expires = int((utc_now() + dt.timedelta(minutes=15)).timestamp())
    return {
        "id": order["id"], "status": "paid", "network": "mainnet-beta",
        "payment_signature": order["payment_signature"],
        "receipt": "https://solscan.io/tx/" + order["payment_signature"],
        "download_token": _download_token(order["id"], secret, expires),
        "download_token_expires_at": dt.datetime.fromtimestamp(
            expires, dt.timezone.utc).isoformat(),
    }


def authorize_download(db: sqlite3.Connection, order_id: str, token: str,
                       secret: str, max_downloads: int = 3) -> None:
    try:
        token_order, expires_text, supplied = token.split(".", 2)
        expires = int(expires_text)
    except (AttributeError, ValueError):
        raise PermissionError("invalid delivery token") from None
    expected = _download_token(token_order, secret, expires)
    if token_order != order_id or not hmac.compare_digest(expected, token):
        raise PermissionError("invalid delivery token")
    if utc_now().timestamp() > expires:
        raise PermissionError("delivery token expired")
    with db:
        row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row or row["status"] != "paid":
            raise PermissionError("order is not paid")
        if row["download_count"] >= max_downloads:
            raise PermissionError("download limit reached; contact support")
        db.execute("UPDATE orders SET download_count=download_count+1 WHERE id=?", (order_id,))


def comparable_sales(db: sqlite3.Connection) -> dict:
    cutoff = (utc_now() - dt.timedelta(days=90)).isoformat()
    rows = db.execute(
        "SELECT * FROM completed_sales WHERE sold_at>=? ORDER BY sold_at DESC LIMIT 500",
        (cutoff,),
    ).fetchall()
    return {"comparables": [dict(row) for row in rows]}
