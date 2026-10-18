"""Synthetic end-to-end rehearsal. No real wallet or funds are used."""
import base64
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from auction import (AuctionConfig, create_bid_challenge, submit_bid,
                     usdc_raw, winning_bid)
from core import (Product, authorize_download, b58encode, confirm_order,
                  connect, create_order)


UTC = dt.timezone.utc
NOW = dt.datetime.now(UTC).replace(microsecond=0)
END = NOW + dt.timedelta(seconds=2)
TERMS = "8" * 64
MERCHANT = "EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
PRODUCT = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                  "0.00", 0, "2026-10-13-v2", TERMS)
DELIVERY_SECRET = "simulation-only-secret-0123456789abcdef"
TX_SIGNATURE = b58encode(bytes(range(64)))


class SyntheticRpc:
    """Return a finalized-looking synthetic USDC transaction for the test only."""
    def __init__(self, row):
        self.row = row

    def transaction(self, signature):
        amount = self.row["amount_raw"]
        block_time = int(dt.datetime.fromisoformat(self.row["created_at"]).timestamp())
        return {
            "blockTime": block_time,
            "meta": {
                "err": None,
                "preTokenBalances": [
                    {"accountIndex": 0, "mint": self.row["mint"], "owner": MERCHANT,
                     "uiTokenAmount": {"amount": "5000000"}},
                    {"accountIndex": 1, "mint": self.row["mint"], "owner": self.row["buyer_wallet"],
                     "uiTokenAmount": {"amount": "2000000000"}},
                ],
                "postTokenBalances": [
                    {"accountIndex": 0, "mint": self.row["mint"], "owner": MERCHANT,
                     "uiTokenAmount": {"amount": str(5000000 + amount)}},
                    {"accountIndex": 1, "mint": self.row["mint"], "owner": self.row["buyer_wallet"],
                     "uiTokenAmount": {"amount": str(2000000000 - amount)}},
                ],
            },
            "transaction": {"message": {"accountKeys": [
                {"pubkey": self.row["buyer_wallet"]},
                {"pubkey": self.row["reference_key"]},
            ]}},
        }


class FullAuctionSimulation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.tmp.name) / "simulation.sqlite")
        self.cfg = AuctionConfig(
            "simulation-auction-001", NOW - dt.timedelta(minutes=1), END,
            usdc_raw("100"), usdc_raw("10"))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    @staticmethod
    def bidder_key():
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        return private, b58encode(public)

    def place_bid(self, private, wallet, amount):
        challenge = create_bid_challenge(
            self.db, self.cfg, wallet, amount, TERMS, NOW)
        signature = base64.b64encode(private.sign(challenge["message"].encode())).decode()
        return submit_bid(self.db, self.cfg, challenge["challenge_id"], signature, NOW)

    def test_complete_synthetic_auction_to_settlement_and_delivery(self):
        bidders = [self.bidder_key() for _ in range(3)]
        self.place_bid(*bidders[0], "100")
        self.place_bid(*bidders[1], "110")
        winner_bid = self.place_bid(*bidders[2], "120")

        close = END + dt.timedelta(seconds=1)
        winner = winning_bid(self.db, self.cfg, PRODUCT.id, close)
        self.assertEqual(winner["bidder_wallet"], bidders[2][1])
        self.assertEqual(winner["amount_raw"], usdc_raw("120"))

        with self.db:
            self.db.execute("UPDATE auction_bids SET status='selected' WHERE id=?",
                             (winner["id"],))
        order = create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key="simulation-checkout-0001",
            buyer_wallet=bidders[2][1], accepted_terms_sha256=TERMS,
            ttl_minutes=1440, price_usdc="120.00", auction_bid_id=winner["id"])
        self.assertEqual(order["amount"], "120.00")

        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        paid = confirm_order(
            self.db, order_id=order["id"], signature=TX_SIGNATURE,
            claim_secret=order["claim_secret"], product=PRODUCT,
            rpc=SyntheticRpc(row), delivery_secret=DELIVERY_SECRET)
        self.assertEqual(paid["status"], "paid")
        self.assertEqual(self.db.execute(
            "SELECT status FROM auction_bids WHERE id=?", (winner["id"],)).fetchone()[0], "paid")
        self.assertEqual(self.db.execute(
            "SELECT price_usd FROM completed_sales WHERE order_id=?", (order["id"],)
        ).fetchone()[0], 120.0)

        # The one-time link authorizes only the configured number of downloads.
        for _ in range(3):
            authorize_download(self.db, order["id"], paid["download_token"], DELIVERY_SECRET)
        with self.assertRaisesRegex(PermissionError, "download limit"):
            authorize_download(self.db, order["id"], paid["download_token"], DELIVERY_SECRET)

        # Retrying the same confirmation is idempotent and cannot create a second sale.
        retried = confirm_order(
            self.db, order_id=order["id"], signature=TX_SIGNATURE,
            claim_secret=order["claim_secret"], product=PRODUCT,
            rpc=SyntheticRpc(row), delivery_secret=DELIVERY_SECRET)
        self.assertEqual(retried["status"], "paid")
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM completed_sales").fetchone()[0], 1)

        # “No discretionary refunds” is only a terms statement; no refund operation exists.
        self.assertNotIn("refund", {r[0] for r in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")})


if __name__ == "__main__":
    unittest.main()
