"""Signed, ascending USDC auction offers; payment is requested only after close."""
from __future__ import annotations

import base64
import binascii
import datetime as dt
import re
import secrets
import sqlite3
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core import USDC_MINT, b58decode, validate_pubkey, utc_now

AUCTION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def utc_iso(value: dt.datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("auction times must include a timezone")
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()


def usdc_raw(value: str) -> int:
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError("invalid USDC bid") from None
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("bid must be a positive amount with at most two decimals")
    return int(amount * 1_000_000)


def usdc_text(raw: int) -> str:
    return f"{Decimal(raw) / Decimal(1_000_000):.2f}"


@dataclass(frozen=True)
class AuctionConfig:
    auction_id: str
    starts_at: dt.datetime
    ends_at: dt.datetime
    opening_bid_raw: int
    increment_raw: int

    def __post_init__(self):
        if not AUCTION_ID_RE.fullmatch(self.auction_id):
            raise ValueError("invalid auction id")
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("auction times must include a timezone")
        if self.ends_at <= self.starts_at:
            raise ValueError("auction end must be after start")
        if self.opening_bid_raw <= 0 or self.increment_raw <= 0:
            raise ValueError("opening bid and increment must be positive")


def init_auction(db: sqlite3.Connection) -> None:
    db.executescript("""
      CREATE TABLE IF NOT EXISTS auction_bids (
        id TEXT PRIMARY KEY,
        auction_id TEXT NOT NULL,
        bidder_wallet TEXT NOT NULL,
        amount_raw INTEGER NOT NULL CHECK(amount_raw > 0),
        signed_message TEXT NOT NULL,
        signature TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('valid','selected','defaulted','paid')),
        created_at TEXT NOT NULL,
        UNIQUE(auction_id, bidder_wallet, amount_raw, signature)
      );
      CREATE INDEX IF NOT EXISTS auction_leader
        ON auction_bids(auction_id,status,amount_raw DESC,created_at ASC);
      CREATE TABLE IF NOT EXISTS bid_challenges (
        id TEXT PRIMARY KEY,
        auction_id TEXT NOT NULL,
        bidder_wallet TEXT NOT NULL,
        amount_raw INTEGER NOT NULL,
        message TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT
      );
      CREATE TABLE IF NOT EXISTS winner_order_challenges (
        id TEXT PRIMARY KEY,
        auction_id TEXT NOT NULL,
        bid_id TEXT NOT NULL,
        bidder_wallet TEXT NOT NULL,
        merchant_wallet TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        terms_sha256 TEXT NOT NULL,
        amount_raw INTEGER NOT NULL,
        message TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT
      );
    """)
    order_columns = {row[1] for row in db.execute("PRAGMA table_info(orders)")}
    if "auction_bid_id" not in order_columns:
        db.execute("ALTER TABLE orders ADD COLUMN auction_bid_id TEXT")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_order_per_auction_bid "
               "ON orders(auction_bid_id) WHERE auction_bid_id IS NOT NULL")


def auction_status(cfg: AuctionConfig, now: dt.datetime | None = None) -> str:
    now = now or utc_now()
    now = now.astimezone(dt.timezone.utc)
    if now < cfg.starts_at.astimezone(dt.timezone.utc):
        return "scheduled"
    if now < cfg.ends_at.astimezone(dt.timezone.utc):
        return "open"
    return "closed"


def _leader(db: sqlite3.Connection, cfg: AuctionConfig):
    return db.execute(
        "SELECT * FROM auction_bids WHERE auction_id=? AND status='valid' "
        "ORDER BY amount_raw DESC, created_at ASC, id ASC LIMIT 1",
        (cfg.auction_id,),
    ).fetchone()


def expire_unpaid_winner(db: sqlite3.Connection, product_id: str,
                         now: dt.datetime | None = None) -> None:
    now_text = utc_iso(now or utc_now())
    with db:
        overdue = db.execute(
            "SELECT id,auction_bid_id FROM orders WHERE product_id=? AND status='pending' AND expires_at<?",
            (product_id, now_text),
        ).fetchall()
        for order in overdue:
            db.execute("UPDATE orders SET status='expired' WHERE id=?", (order["id"],))
            if order["auction_bid_id"]:
                db.execute("UPDATE auction_bids SET status='defaulted' WHERE id=? AND status='selected'",
                           (order["auction_bid_id"],))


def auction_snapshot(db: sqlite3.Connection, cfg: AuctionConfig,
                     now: dt.datetime | None = None,
                     product_id: str | None = None) -> dict:
    init_auction(db)
    state = auction_status(cfg, now)
    if state == "closed" and product_id:
        expire_unpaid_winner(db, product_id, now)
    leader = db.execute(
        "SELECT * FROM auction_bids WHERE auction_id=? AND status IN ('valid','selected','paid') "
        "ORDER BY amount_raw DESC, created_at ASC, id ASC LIMIT 1",
        (cfg.auction_id,),
    ).fetchone()
    open_leader = _leader(db, cfg) if state == "open" else None
    next_minimum = (cfg.opening_bid_raw if not open_leader
                    else open_leader["amount_raw"] + cfg.increment_raw)
    return {
        "auction_id": cfg.auction_id,
        "status": state,
        "starts_at": utc_iso(cfg.starts_at),
        "ends_at": utc_iso(cfg.ends_at),
        "opening_bid_usdc": usdc_text(cfg.opening_bid_raw),
        "minimum_increment_usdc": usdc_text(cfg.increment_raw),
        "next_minimum_bid_usdc": usdc_text(next_minimum) if state == "open" else None,
        "highest_bid_usdc": usdc_text(leader["amount_raw"]) if leader else None,
        "bid_count": db.execute(
            "SELECT COUNT(*) FROM auction_bids WHERE auction_id=? AND status IN ('valid','selected','paid')",
            (cfg.auction_id,),
        ).fetchone()[0],
    }


def create_bid_challenge(db: sqlite3.Connection, cfg: AuctionConfig,
                         bidder_wallet: str, amount: str,
                         accepted_terms_sha256: str,
                         now: dt.datetime | None = None) -> dict:
    init_auction(db)
    now = now or utc_now()
    bidder_wallet = validate_pubkey(bidder_wallet)
    if auction_status(cfg, now) != "open":
        raise ValueError("auction is not open for bids")
    amount_raw = usdc_raw(amount)
    leader = _leader(db, cfg)
    minimum = cfg.opening_bid_raw if not leader else leader["amount_raw"] + cfg.increment_raw
    if amount_raw < minimum:
        raise ValueError(f"bid must be at least {usdc_text(minimum)} USDC")
    challenge_id = secrets.token_urlsafe(24)
    expires = now.astimezone(dt.timezone.utc).replace(microsecond=0) + dt.timedelta(minutes=5)
    message = (
        "MOSUL HERITAGE AUCTION BID\n"
        f"Auction: {cfg.auction_id}\n"
        f"Bidder: {bidder_wallet}\n"
        f"Amount: {usdc_text(amount_raw)} USDC\n"
        f"Starts: {utc_iso(cfg.starts_at)}\n"
        f"Ends: {utc_iso(cfg.ends_at)}\n"
        f"Opening bid: {usdc_text(cfg.opening_bid_raw)} USDC\n"
        f"Minimum increment: {usdc_text(cfg.increment_raw)} USDC\n"
        f"Terms SHA-256: {accepted_terms_sha256}\n"
        f"Challenge: {challenge_id}\n"
        f"Expires: {utc_iso(expires)}\n"
        "This signed message records a bid offer; it does not transfer or escrow funds."
    )
    with db:
        db.execute("INSERT INTO bid_challenges VALUES (?,?,?,?,?,?,NULL)",
                   (challenge_id, cfg.auction_id, bidder_wallet, amount_raw,
                    message, utc_iso(expires)))
    return {"challenge_id": challenge_id, "message": message,
            "expires_at": utc_iso(expires)}


def submit_bid(db: sqlite3.Connection, cfg: AuctionConfig, challenge_id: str,
               signature_b64: str, now: dt.datetime | None = None) -> dict:
    init_auction(db)
    now = now or utc_now()
    if auction_status(cfg, now) != "open":
        raise ValueError("auction is not open for bids")
    challenge = db.execute(
        "SELECT * FROM bid_challenges WHERE id=? AND auction_id=?",
        (challenge_id, cfg.auction_id),
    ).fetchone()
    if not challenge or challenge["used_at"]:
        raise ValueError("bid challenge is missing or already used")
    if utc_iso(now) > challenge["expires_at"]:
        raise ValueError("bid challenge expired")
    leader = _leader(db, cfg)
    minimum = cfg.opening_bid_raw if not leader else leader["amount_raw"] + cfg.increment_raw
    if challenge["amount_raw"] < minimum:
        raise ValueError(f"another bid was accepted; new minimum is {usdc_text(minimum)} USDC")
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        key = Ed25519PublicKey.from_public_bytes(b58decode(challenge["bidder_wallet"]))
        key.verify(signature, challenge["message"].encode("utf-8"))
    except (ValueError, binascii.Error, InvalidSignature):
        raise PermissionError("wallet signature did not verify") from None
    bid_id = secrets.token_urlsafe(18)
    created = utc_iso(now)
    with db:
        cursor = db.execute("UPDATE bid_challenges SET used_at=? WHERE id=? AND used_at IS NULL",
                            (created, challenge_id))
        if cursor.rowcount != 1:
            raise ValueError("bid challenge was already used")
        db.execute("INSERT INTO auction_bids VALUES (?,?,?,?,?,?, 'valid',?)",
                   (bid_id, cfg.auction_id, challenge["bidder_wallet"],
                    challenge["amount_raw"], challenge["message"], signature_b64, created))
    return {"bid_id": bid_id, "status": "accepted",
            "amount_usdc": usdc_text(challenge["amount_raw"]), "created_at": created}


def winning_bid(db: sqlite3.Connection, cfg: AuctionConfig,
                product_id: str, now: dt.datetime | None = None):
    if auction_status(cfg, now) != "closed":
        raise ValueError("auction has not closed")
    expire_unpaid_winner(db, product_id, now)
    active = db.execute(
        "SELECT b.* FROM auction_bids b JOIN orders o ON o.auction_bid_id=b.id "
        "WHERE b.auction_id=? AND o.status='pending' LIMIT 1", (cfg.auction_id,)
    ).fetchone()
    if active:
        raise ValueError("winning bidder already has an active payment window")
    return db.execute(
        "SELECT * FROM auction_bids WHERE auction_id=? AND status='valid' "
        "ORDER BY amount_raw DESC, created_at ASC, id ASC LIMIT 1",
        (cfg.auction_id,),
    ).fetchone()


def payable_winner(db: sqlite3.Connection, cfg: AuctionConfig,
                   product_id: str, now: dt.datetime | None = None):
    """Return the current winner and any pending order that can be recovered."""
    if auction_status(cfg, now) != "closed":
        raise ValueError("auction has not closed")
    expire_unpaid_winner(db, product_id, now)
    if db.execute("SELECT 1 FROM completed_sales WHERE product_id=?", (product_id,)).fetchone():
        raise ValueError("this one-of-one product has been sold")
    active = db.execute(
        "SELECT o.*,b.bidder_wallet,b.amount_raw AS bid_amount_raw "
        "FROM orders o JOIN auction_bids b ON o.auction_bid_id=b.id "
        "WHERE o.product_id=? AND o.status='pending' AND b.auction_id=? "
        "AND b.status='selected' LIMIT 1",
        (product_id, cfg.auction_id),
    ).fetchone()
    if active:
        bid = db.execute("SELECT * FROM auction_bids WHERE id=?", (active["auction_bid_id"],)).fetchone()
        return bid, active
    return winning_bid(db, cfg, product_id, now), None


def create_winner_order_challenge(db: sqlite3.Connection, cfg: AuctionConfig,
                                  product_id: str, merchant_wallet: str,
                                  idempotency_key: str, terms_sha256: str,
                                  now: dt.datetime | None = None) -> dict:
    """Request fresh wallet consent before reserving a winning bidder's order."""
    init_auction(db)
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,100}", idempotency_key or ""):
        raise ValueError("invalid idempotency key")
    if not re.fullmatch(r"[0-9a-f]{64}", terms_sha256 or ""):
        raise ValueError("invalid terms hash")
    merchant_wallet = validate_pubkey(merchant_wallet)
    winner, _ = payable_winner(db, cfg, product_id, now)
    if not winner:
        raise ValueError("auction ended without a valid bid")
    now = now or utc_now()
    expires = now.astimezone(dt.timezone.utc).replace(microsecond=0) + dt.timedelta(minutes=5)
    challenge_id = secrets.token_urlsafe(24)
    message = (
        "MOSUL HERITAGE WINNER ORDER REQUEST\n"
        f"Auction: {cfg.auction_id}\n"
        f"Product: {product_id}\n"
        f"Winning bid: {winner['id']}\n"
        f"Bidder: {winner['bidder_wallet']}\n"
        f"Amount: {usdc_text(winner['amount_raw'])} USDC\n"
        f"Payment mint: {USDC_MINT}\n"
        f"Merchant wallet: {merchant_wallet}\n"
        f"Terms SHA-256: {terms_sha256}\n"
        f"Idempotency key: {idempotency_key}\n"
        f"Challenge: {challenge_id}\n"
        f"Expires: {utc_iso(expires)}\n"
        "This signature requests a payment order; it does not transfer funds."
    )
    with db:
        db.execute(
            "INSERT INTO winner_order_challenges VALUES (?,?,?,?,?,?,?,?,?,?,NULL)",
            (challenge_id, cfg.auction_id, winner["id"], winner["bidder_wallet"],
             merchant_wallet, idempotency_key, terms_sha256, winner["amount_raw"],
             message, utc_iso(expires)),
        )
    return {"challenge_id": challenge_id, "message": message,
            "expires_at": utc_iso(expires), "bidder_wallet": winner["bidder_wallet"]}


def consume_winner_order_challenge(db: sqlite3.Connection, cfg: AuctionConfig,
                                   challenge_id: str, signature_b64: str,
                                   *, winner: sqlite3.Row, merchant_wallet: str,
                                   idempotency_key: str, terms_sha256: str,
                                   now: dt.datetime | None = None) -> None:
    """Accept the exact current winner, terms, merchant, amount and one-time signature."""
    init_auction(db)
    challenge = db.execute(
        "SELECT * FROM winner_order_challenges WHERE id=? AND auction_id=?",
        (challenge_id, cfg.auction_id),
    ).fetchone()
    if not challenge or challenge["used_at"]:
        raise PermissionError("winner order challenge is missing or already used")
    now = now or utc_now()
    if utc_iso(now) > challenge["expires_at"]:
        raise PermissionError("winner order challenge expired")
    if (challenge["bid_id"] != winner["id"]
            or challenge["bidder_wallet"] != winner["bidder_wallet"]
            or challenge["amount_raw"] != winner["amount_raw"]
            or challenge["merchant_wallet"] != merchant_wallet
            or challenge["idempotency_key"] != idempotency_key
            or challenge["terms_sha256"] != terms_sha256):
        raise PermissionError("winner order challenge does not match the current order")
    try:
        signature = base64.b64decode(signature_b64, validate=True)
        key = Ed25519PublicKey.from_public_bytes(b58decode(challenge["bidder_wallet"]))
        key.verify(signature, challenge["message"].encode("utf-8"))
    except (ValueError, binascii.Error, InvalidSignature):
        raise PermissionError("winner wallet signature did not verify") from None
    with db:
        cursor = db.execute(
            "UPDATE winner_order_challenges SET used_at=? WHERE id=? AND used_at IS NULL",
            (utc_iso(now), challenge_id),
        )
        if cursor.rowcount != 1:
            raise PermissionError("winner order challenge was already used")
