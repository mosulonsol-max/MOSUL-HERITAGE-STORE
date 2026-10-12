#!/usr/bin/env python3
"""HTTP adapter for the fail-closed Mainnet sale service."""
from __future__ import annotations

import hmac
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import (MainnetRpc, authorize_download, comparable_sales, confirm_order,
                  connect, create_order, load_product)

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("SALE_DB", "data/sales.sqlite3"))
PRODUCT_PATH = Path(os.environ.get(
    "SALE_PRODUCT", str(ROOT / "products" / "MOSUL-GENESIS-000001.json")))
MERCHANT_WALLET = os.environ.get("SALES_MERCHANT_WALLET", "")
DELIVERY_SECRET = os.environ.get("DELIVERY_TOKEN_SECRET", "")
DELIVERY_PACKAGE = Path(os.environ.get("DELIVERY_PACKAGE_PATH", ""))
RPC_URL = os.environ.get("SOLANA_MAINNET_RPC", "https://api.mainnet-beta.solana.com")
ALLOWED_ORIGIN = os.environ.get("SALE_ALLOWED_ORIGIN", "")
ADMIN_TOKEN = os.environ.get("SALE_ADMIN_TOKEN", "")
PRODUCT = load_product(PRODUCT_PATH)


class Handler(BaseHTTPRequestHandler):
    server_version = "MosulSaleService/1.0"

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
            return self._json(200, {"status": "ready", "network": "mainnet-beta",
                                    "product_id": PRODUCT.id})
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
        if not self._same_origin():
            return self._json(403, {"error": "origin not allowed"})
        try:
            body = self._body()
            with connect(DB_PATH) as db:
                if self.path == "/orders":
                    result = create_order(
                        db, product=PRODUCT, merchant_wallet=MERCHANT_WALLET,
                        idempotency_key=str(body["idempotency_key"]),
                        buyer_wallet=body.get("buyer_wallet"),
                        accepted_terms_sha256=str(body["accepted_terms_sha256"]),
                    )
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
    if os.environ.get("SALES_ENABLED") != "1":
        raise SystemExit("SALES_ENABLED=1 is required")
    if os.environ.get("SELLER_TERMS_ACCEPTED") != "1":
        raise SystemExit("SELLER_TERMS_ACCEPTED=1 is required")
    if not MERCHANT_WALLET or len(DELIVERY_SECRET) < 32:
        raise SystemExit("SALES_MERCHANT_WALLET and a strong DELIVERY_TOKEN_SECRET are required")
    if not DELIVERY_PACKAGE.is_file():
        raise SystemExit("DELIVERY_PACKAGE_PATH must point to the private product ZIP")
    if PRODUCT.terms_sha256 == "0" * 64 or PRODUCT.terms_version == "owner-signature-required":
        raise SystemExit("replace the draft buyer terms with the signed version and its SHA-256")
    if not ALLOWED_ORIGIN.startswith("https://"):
        raise SystemExit("SALE_ALLOWED_ORIGIN must be the HTTPS storefront origin")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def main() -> int:
    validate_startup()
    host = os.environ.get("SALE_BIND", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
