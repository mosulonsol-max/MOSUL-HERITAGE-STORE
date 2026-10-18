#!/usr/bin/env python3
"""HTTP adapter for the fail-closed Mainnet sale service."""
from __future__ import annotations

import hmac
import datetime as dt
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import (MainnetRpc, authorize_download, comparable_sales, confirm_order,
                  connect, create_order, load_product, validate_pubkey,
                  verify_seller_terms_signature)
from auction import (AuctionConfig, auction_snapshot, create_bid_challenge,
                    init_auction, submit_bid, usdc_raw, usdc_text, winning_bid)
from readiness import evaluate_readiness

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SALE_DB", "data/sales.sqlite3"))
PRODUCT_PATH = Path(os.environ.get(
    "SALE_PRODUCT", str(ROOT / "products" / "MOSUL-GENESIS-000001.json")))
ASSET_MANIFEST_PATH = Path(os.environ.get(
    "SALE_ASSET_MANIFEST",
    str(ROOT / "products" / "MOSUL-GENESIS-000001.assets.json")))
DELIVERY_SECRET = os.environ.get("DELIVERY_TOKEN_SECRET", "")
DELIVERY_PACKAGE = Path(os.environ.get("DELIVERY_PACKAGE_PATH", ""))
RPC_URL = os.environ.get("SOLANA_MAINNET_RPC", "https://api.mainnet-beta.solana.com")
ALLOWED_ORIGIN = os.environ.get("SALE_ALLOWED_ORIGIN", "")
ADMIN_TOKEN = os.environ.get("SALE_ADMIN_TOKEN", "")
SELLER_LEGAL_NAME = os.environ.get("SELLER_LEGAL_NAME", "")
SELLER_TRADE_NAME = os.environ.get("SELLER_TRADE_NAME", "MOSUL HERITAGE STORE")
SELLER_COUNTRY = os.environ.get("SELLER_COUNTRY", "")
SELLER_ADDRESS = os.environ.get("SELLER_ADDRESS", "")
SELLER_ONLINE_ONLY = os.environ.get("SELLER_ONLINE_ONLY", "0") == "1"
SELLER_SUPPORT_EMAIL = os.environ.get("SELLER_SUPPORT_EMAIL", "")
SELLER_TERMS_SIGNED_AT = os.environ.get("SELLER_TERMS_SIGNED_AT", "")
SELLER_TERMS_SIGNATURE_B64 = os.environ.get("SELLER_TERMS_SIGNATURE_B64", "")
SALES_ENABLED = os.environ.get("SALES_ENABLED", "0") == "1"
PRODUCT = load_product(PRODUCT_PATH)
MERCHANT_WALLET = os.environ.get("SALES_MERCHANT_WALLET", PRODUCT.merchant_wallet)


def load_auction_config() -> AuctionConfig | None:
    names = ("SALE_AUCTION_ID", "SALE_AUCTION_STARTS_AT", "SALE_AUCTION_ENDS_AT")
    if not all(os.environ.get(name) for name in names):
        return None
    try:
        starts = dt.datetime.fromisoformat(os.environ[names[1]].replace("Z", "+00:00"))
        ends = dt.datetime.fromisoformat(os.environ[names[2]].replace("Z", "+00:00"))
        opening = PRODUCT.auction_opening_bid_usdc
        increment = PRODUCT.auction_increment_usdc
        if usdc_raw(os.environ.get("SALE_AUCTION_OPENING_BID_USDC", opening)) != usdc_raw(opening):
            raise ValueError("opening bid differs from the signed product terms")
        if usdc_raw(os.environ.get("SALE_AUCTION_INCREMENT_USDC", increment)) != usdc_raw(increment):
            raise ValueError("bid increment differs from the signed product terms")
        return AuctionConfig(os.environ[names[0]], starts, ends,
                             usdc_raw(opening), usdc_raw(increment))
    except (ValueError, TypeError) as exc:
        raise SystemExit(f"invalid auction configuration: {exc}") from None


AUCTION = load_auction_config()


def seller_signature_valid() -> bool:
    try:
        verify_seller_terms_signature(
            legal_name=SELLER_LEGAL_NAME, trade_name=SELLER_TRADE_NAME,
            wallet=MERCHANT_WALLET, product=PRODUCT,
            signed_at=SELLER_TERMS_SIGNED_AT,
            signature_b64=SELLER_TERMS_SIGNATURE_B64,
        )
        return True
    except (ValueError, PermissionError):
        return False


def readiness_snapshot() -> dict:
    seller_contact = SELLER_ADDRESS or ("Online-only store; no customer-facing physical storefront"
                                        if SELLER_ONLINE_ONLY else "")
    return evaluate_readiness(
        product_path=PRODUCT_PATH,
        asset_manifest_path=ASSET_MANIFEST_PATH,
        delivery_package_path=DELIVERY_PACKAGE,
        seller_signature_valid=seller_signature_valid(),
        auction_configured=AUCTION is not None,
        seller_disclosure_complete=all((
            SELLER_LEGAL_NAME, SELLER_TRADE_NAME, SELLER_COUNTRY,
            seller_contact, SELLER_SUPPORT_EMAIL,
        )) and (bool(SELLER_ADDRESS) or SELLER_ONLINE_ONLY),
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "MosulSaleService/1.0"

    def log_message(self, _format: str, *args) -> None:
        # Requests may contain short-lived download tokens in their query string.
        # The reverse proxy must also redact those query strings from access logs.
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
            self.send_header("Vary", "Origin")
        super().end_headers()

    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 16384:
            raise ValueError("invalid request size")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def _same_origin(self) -> bool:
        return bool(ALLOWED_ORIGIN) and self.headers.get("Origin") == ALLOWED_ORIGIN

    def _admin(self) -> bool:
        return bool(ADMIN_TOKEN) and hmac.compare_digest(
            self.headers.get("Authorization", ""), "Bearer " + ADMIN_TOKEN)

    def do_OPTIONS(self) -> None:
        if not self._same_origin():
            return self._json(403, {"error": "origin not allowed"})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return self._json(200, {"status": "ready" if SALES_ENABLED else "sales_disabled",
                                    "sales_enabled": SALES_ENABLED,
                                    "network": "mainnet-beta",
                                    "product_id": PRODUCT.id,
                                    "seller": ({"trade_name": SELLER_TRADE_NAME,
                                               "name": SELLER_LEGAL_NAME,
                                               "country": SELLER_COUNTRY,
                                               "contact_location": SELLER_ADDRESS or (
                                                   "Online-only store; no customer-facing physical storefront"
                                                   if SELLER_ONLINE_ONLY else ""),
                                               "support_email": SELLER_SUPPORT_EMAIL}
                                               if SALES_ENABLED else None)})
        if parsed.path == "/readiness":
            return self._json(200, readiness_snapshot())
        if not SALES_ENABLED:
            return self._json(503, {"error": "sales are not enabled"})
        if parsed.path == "/auction" and AUCTION:
            with connect(DB_PATH) as db:
                return self._json(200, auction_snapshot(db, AUCTION, product_id=PRODUCT.id))
        if parsed.path == "/comparables" and self._admin():
            with connect(DB_PATH) as db:
                return self._json(200, comparable_sales(db))
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "orders" and parts[2] == "download":
            token = parse_qs(parsed.query).get("token", [""])[0]
            try:
                with connect(DB_PATH) as db:
                    authorize_download(db, parts[1], token, DELIVERY_SECRET)
                size = DELIVERY_PACKAGE.stat().st_size
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(DELIVERY_PACKAGE.name)[0]
                                 or "application/octet-stream")
                self.send_header("Content-Disposition",
                                 'attachment; filename="MOSUL-GENESIS-000001.zip"')
                self.send_header("Content-Length", str(size))
                self.end_headers()
                with DELIVERY_PACKAGE.open("rb") as handle:
                    while chunk := handle.read(1024 * 1024):
                        self.wfile.write(chunk)
                return
            except (PermissionError, OSError):
                return self._json(403, {"error": "download unavailable"})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if not SALES_ENABLED:
            return self._json(503, {"error": "sales are not enabled"})
        if not self._same_origin():
            return self._json(403, {"error": "origin not allowed"})
        try:
            body = self._body()
            with connect(DB_PATH) as db:
                if self.path == "/bids/challenge" and AUCTION:
                    accepted = str(body["accepted_terms_sha256"])
                    if not hmac.compare_digest(accepted, PRODUCT.terms_sha256):
                        raise PermissionError("accept the current auction terms first")
                    bidder = str(body["bidder_wallet"])
                    if hmac.compare_digest(bidder, MERCHANT_WALLET):
                        raise PermissionError("the seller cannot bid on this auction")
                    result = create_bid_challenge(
                        db, AUCTION, bidder, str(body["amount_usdc"]),
                        accepted,
                    )
                elif self.path == "/bids" and AUCTION:
                    result = submit_bid(db, AUCTION, str(body["challenge_id"]),
                                        str(body["signature_base64"]))
                elif self.path == "/orders" and AUCTION:
                    accepted = str(body["accepted_terms_sha256"])
                    if not hmac.compare_digest(accepted, PRODUCT.terms_sha256):
                        raise PermissionError("accept the current auction terms first")
                    winner = winning_bid(db, AUCTION, PRODUCT.id)
                    if not winner:
                        raise ValueError("auction ended without a valid bid")
                    buyer_wallet = str(body.get("buyer_wallet", ""))
                    if not hmac.compare_digest(buyer_wallet, winner["bidder_wallet"]):
                        raise PermissionError("only the highest bidder can pay this order")
                    result = create_order(
                        db, product=PRODUCT, merchant_wallet=MERCHANT_WALLET,
                        idempotency_key=str(body["idempotency_key"]),
                        buyer_wallet=buyer_wallet, accepted_terms_sha256=accepted,
                        ttl_minutes=1440, price_usdc=usdc_text(winner["amount_raw"]),
                        auction_bid_id=winner["id"],
                    )
                    with db:
                        db.execute("UPDATE auction_bids SET status='selected' WHERE id=? AND status='valid'",
                                   (winner["id"],))
                elif self.path == "/orders" and not AUCTION:
                    return self._json(503, {"error": "auction configuration is unavailable"})
                elif self.path.startswith("/orders/") and self.path.endswith("/confirm"):
                    order_id = self.path.split("/")[2]
                    result = confirm_order(
                        db, order_id=order_id, signature=str(body["signature"]),
                        claim_secret=str(body["claim_secret"]),
                        product=PRODUCT, rpc=MainnetRpc(RPC_URL),
                        delivery_secret=DELIVERY_SECRET,
                    )
                    result["download_url"] = (
                        f"/orders/{order_id}/download?token={result['download_token']}")
                else:
                    return self._json(404, {"error": "not found"})
            self._json(200, result)
        except (KeyError, ValueError, PermissionError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception:
            self._json(503, {"error": "service unavailable"})


def validate_startup() -> None:
    enabled = os.environ.get("SALES_ENABLED", "0")
    if enabled not in {"0", "1"}:
        raise SystemExit("SALES_ENABLED must be exactly 0 or 1")
    if enabled == "0":
        # Allow a health-checked, fail-closed deployment before the owner has
        # installed the private delivery ZIP and completed auction settings.
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with connect(DB_PATH) as db:
            init_auction(db)
        return
    if not MERCHANT_WALLET or len(DELIVERY_SECRET) < 32:
        raise SystemExit("SALES_MERCHANT_WALLET and a strong DELIVERY_TOKEN_SECRET are required")
    try:
        validate_pubkey(MERCHANT_WALLET)
    except ValueError:
        raise SystemExit("SALES_MERCHANT_WALLET must be a valid Solana public key") from None
    if not DELIVERY_PACKAGE.is_file():
        raise SystemExit("DELIVERY_PACKAGE_PATH must point to the private product ZIP")
    if PRODUCT.terms_sha256 == "0" * 64 or PRODUCT.terms_version == "owner-signature-required":
        raise SystemExit("replace the draft buyer terms with the signed version and its SHA-256")
    try:
        verify_seller_terms_signature(
            legal_name=SELLER_LEGAL_NAME, trade_name=SELLER_TRADE_NAME,
            wallet=MERCHANT_WALLET, product=PRODUCT,
            signed_at=SELLER_TERMS_SIGNED_AT,
            signature_b64=SELLER_TERMS_SIGNATURE_B64,
        )
    except (ValueError, PermissionError) as exc:
        raise SystemExit(f"valid seller wallet signature over the exact terms is required: {exc}") from None
    readiness = readiness_snapshot()
    if not readiness["auction_ready"]:
        raise SystemExit("auction readiness gates failed: " + ", ".join(readiness["blockers"]))
    if not ALLOWED_ORIGIN.startswith("https://"):
        raise SystemExit("SALE_ALLOWED_ORIGIN must be the HTTPS storefront origin")
    if not AUCTION:
        raise SystemExit("complete the auction id, dates, opening bid, and increment")
    if not SELLER_LEGAL_NAME or not SELLER_TRADE_NAME or not SELLER_COUNTRY or not SELLER_ADDRESS or not SELLER_SUPPORT_EMAIL:
        raise SystemExit("seller name, country, address, and support email are required for buyer disclosure")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect(DB_PATH) as db:
        init_auction(db)


def main() -> int:
    validate_startup()
    host = os.environ.get("SALE_BIND", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
