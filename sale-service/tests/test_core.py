import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path

from core import (Product, authorize_download, b58encode, confirm_order, connect,
                  create_order, validate_pubkey, verify_transaction)

MERCHANT = "EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
BUYER = "So11111111111111111111111111111111111111112"
SIGNATURE = b58encode(bytes(range(64)))
TERMS = hashlib.sha256(b"signed terms").hexdigest()
PRODUCT = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                  "149.00", 149_000_000, "v1", TERMS)
SECRET = "s" * 48


class Rpc:
    def __init__(self, row):
        self.row = row

    def transaction(self, signature):
        block_time = int(dt.datetime.fromisoformat(self.row["created_at"]).timestamp())
        return {
            "blockTime": block_time,
            "meta": {
                "err": None,
                "preTokenBalances": [{"accountIndex": 2, "mint": self.row["mint"],
                    "owner": MERCHANT, "uiTokenAmount": {"amount": "1000000"}}],
                "postTokenBalances": [{"accountIndex": 2, "mint": self.row["mint"],
                    "owner": MERCHANT, "uiTokenAmount": {"amount": "150000000"}}],
            },
            "transaction": {"message": {"accountKeys": [
                {"pubkey": BUYER}, {"pubkey": self.row["reference_key"]},
                {"pubkey": "11111111111111111111111111111111"},
            ]}},
        }


class SaleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "sale.db")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def order(self, key="checkout-12345678"):
        return create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key=key, buyer_wallet=BUYER, accepted_terms_sha256=TERMS)

    def test_order_is_idempotent_and_contains_solana_pay_uri(self):
        first = self.order()
        again = self.order()
        self.assertEqual(first["id"], again["id"])
        self.assertIn("spl-token=", first["solana_pay_uri"])
        self.assertIn("reference=", first["solana_pay_uri"])

    def test_one_of_one_reservation_blocks_second_order(self):
        self.order()
        with self.assertRaises(ValueError):
            self.order("checkout-87654321")

    def test_terms_hash_must_match(self):
        with self.assertRaises(PermissionError):
            create_order(self.db, product=PRODUCT, merchant_wallet=MERCHANT,
                         idempotency_key="checkout-12345678", buyer_wallet=None,
                         accepted_terms_sha256="0" * 64)

    def test_exact_finalized_payment_settles_and_issues_download(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        result = confirm_order(self.db, order_id=order["id"], signature=SIGNATURE,
                               claim_secret=order["claim_secret"], product=PRODUCT,
                               rpc=Rpc(row), delivery_secret=SECRET)
        self.assertEqual(result["status"], "paid")
        authorize_download(self.db, order["id"], result["download_token"], SECRET)
        self.assertEqual(self.db.execute(
            "SELECT download_count FROM orders WHERE id=?", (order["id"],)
        ).fetchone()[0], 1)

    def test_wrong_amount_and_missing_reference_are_rejected(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        tx = Rpc(row).transaction(SIGNATURE)
        tx["meta"]["postTokenBalances"][0]["uiTokenAmount"]["amount"] = "149999999"
        with self.assertRaises(ValueError):
            verify_transaction(tx, row)
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["accountKeys"] = []
        with self.assertRaises(ValueError):
            verify_transaction(tx, row)

    def test_signature_cannot_be_replayed_for_second_sale(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        confirm_order(self.db, order_id=order["id"], signature=SIGNATURE,
                      claim_secret=order["claim_secret"], product=PRODUCT,
                      rpc=Rpc(row), delivery_secret=SECRET)
        with self.assertRaises(ValueError):
            self.order("checkout-new-123456")

    def test_invalid_pubkey_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_pubkey("not-a-wallet")

    def test_download_token_limit(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        result = confirm_order(self.db, order_id=order["id"], signature=SIGNATURE,
                               claim_secret=order["claim_secret"], product=PRODUCT,
                               rpc=Rpc(row), delivery_secret=SECRET)
        for _ in range(3):
            authorize_download(self.db, order["id"], result["download_token"], SECRET)
        with self.assertRaises(PermissionError):
            authorize_download(self.db, order["id"], result["download_token"], SECRET)

    def test_public_transaction_data_cannot_claim_delivery(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        with self.assertRaises(PermissionError):
            confirm_order(
                self.db,
                order_id=order["id"],
                signature=SIGNATURE,
                claim_secret="not-the-buyers-secret",
                product=PRODUCT,
                rpc=Rpc(row),
                delivery_secret=SECRET,
            )


if __name__ == "__main__":
    unittest.main()
