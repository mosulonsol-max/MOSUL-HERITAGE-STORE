#!/usr/bin/env python3
"""Minimal JSON API for the Devnet-only payment core; deploy behind HTTPS."""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import DevnetRpc, comparable_sales, confirm_payment, connect, create_intent, request_refund

DB_PATH = os.environ.get("PAYMENT_DB", "data/payments.sqlite3")
SERVICE_TOKEN = os.environ.get("PAYMENT_SERVICE_TOKEN", "")
MERCHANT = os.environ.get("DEVNET_MERCHANT_PUBKEY", "")
DEVNET_MOSUL_MINT = os.environ.get("DEVNET_MOSUL_MINT", "")


class Handler(BaseHTTPRequestHandler):
    server_version = "MosulDevnetPayments/0.1"

    def _json(self, status: int, value: dict) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers(); self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 65536:
            raise ValueError("invalid request size")
        value = json.loads(self.rfile.read(length))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value

    def _admin(self) -> bool:
        import hmac
        expected = "Bearer " + SERVICE_TOKEN
        return bool(SERVICE_TOKEN) and hmac.compare_digest(self.headers.get("Authorization", ""), expected)

    def do_GET(self):
        if self.path != "/comparables" or not self._admin():
            return self._json(404, {"error": "not found"})
        with connect(DB_PATH) as db:
            self._json(200, comparable_sales(db))

    def do_POST(self):
        try:
            body = self._body()
            with connect(DB_PATH) as db:
                if self.path == "/intents" and self._admin():
                    asset = body.get("asset", "SOL")
                    if asset not in {"SOL", "MOSUL"}:
                        return self._json(400, {"error": "unsupported devnet payment asset"})
                    if asset == "MOSUL" and not DEVNET_MOSUL_MINT:
                        return self._json(503, {"error": "Devnet MOSUL test mint is not configured"})
                    result = create_intent(db, idempotency_key=body["idempotency_key"], item_id=body["item_id"],
                        category=body["category"], amount_lamports=body["amount_lamports"],
                        price_usd=str(body["price_usd"]), merchant=MERCHANT, buyer=body.get("buyer"),
                        asset_mint=DEVNET_MOSUL_MINT if asset == "MOSUL" else None,
                        asset_decimals=6 if asset == "MOSUL" else 9)
                elif self.path.startswith("/intents/") and self.path.endswith("/confirm"):
                    intent_id = self.path.split("/")[2]
                    result = confirm_payment(db, intent_id, body["signature"], DevnetRpc())
                elif self.path.startswith("/intents/") and self.path.endswith("/refund"):
                    intent_id = self.path.split("/")[2]
                    result = request_refund(db, intent_id, body["refund_token"])
                else:
                    return self._json(404, {"error": "not found"})
            self._json(200, result)
        except (KeyError, ValueError, PermissionError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception:
            self._json(503, {"error": "service unavailable"})


def main() -> int:
    if not SERVICE_TOKEN or not MERCHANT:
        raise SystemExit("PAYMENT_SERVICE_TOKEN and DEVNET_MERCHANT_PUBKEY are required")
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    host, port = os.environ.get("PAYMENT_BIND", "127.0.0.1"), int(os.environ.get("PAYMENT_PORT", "8080"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
