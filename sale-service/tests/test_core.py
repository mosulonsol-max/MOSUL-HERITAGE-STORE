import base64
import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core import (MEMO_PROGRAM, MOSUL_MINT, TOKEN_2022_PROGRAM_ID, TOKEN_PROGRAM_ID,
                  Product, authorize_download, b58encode, confirm_order, connect,
                  create_order, seller_terms_message, validate_pubkey,
                  token_amount_raw, verify_seller_terms_signature, verify_transaction)

MERCHANT = "EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
BUYER = "So11111111111111111111111111111111111111112"
SIGNATURE = b58encode(bytes(range(64)))
TERMS = hashlib.sha256(b"signed terms").hexdigest()
PRODUCT = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                  "149.00", 149_000_000, "v1", TERMS)
SECRET = "s" * 48


class Rpc:
    def __init__(self, row, payment_amount=149_000_000):
        self.row = row
        self.payment_amount = payment_amount

    def transaction(self, signature):
        block_time = int(dt.datetime.fromisoformat(self.row["created_at"]).timestamp())
        return {
            "blockTime": block_time,
            "meta": {
                "err": None,
                "preTokenBalances": [{"accountIndex": 2, "mint": self.row["mint"],
                    "owner": MERCHANT, "programId": TOKEN_PROGRAM_ID, "uiTokenAmount": {"amount": "1000000"}},
                    {"accountIndex": 3, "mint": self.row["mint"],
                     "owner": BUYER, "programId": TOKEN_PROGRAM_ID, "uiTokenAmount": {"amount": "2000000"}}],
                "postTokenBalances": [{"accountIndex": 2, "mint": self.row["mint"],
                    "owner": MERCHANT, "programId": TOKEN_PROGRAM_ID, "uiTokenAmount": {"amount": str(1_000_000 + self.payment_amount)}},
                    {"accountIndex": 3, "mint": self.row["mint"],
                     "owner": BUYER, "programId": TOKEN_PROGRAM_ID, "uiTokenAmount": {"amount": str(2_000_000 - self.payment_amount)}}],
            },
            "transaction": {"message": {"accountKeys": [
                {"pubkey": BUYER}, {"pubkey": self.row["reference_key"]},
                {"pubkey": "11111111111111111111111111111111"},
            ], "instructions": [{"programId": MEMO_PROGRAM,
                                  "parsed": self.row["memo"]}]}},
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

    def test_auction_order_uses_the_winning_bid_not_a_catalog_price(self):
        order = create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key="checkout-auction-123", buyer_wallet=BUYER,
            accepted_terms_sha256=TERMS, price_usd="75.50", auction_bid_id="bid-123",
        )
        self.assertEqual(order["amount"], "75.50")
        self.assertEqual(order["amount_raw"], 75_500_000)
        self.assertIn("amount=75.50", order["solana_pay_uri"])

    def test_mosul_order_converts_usd_and_records_quote(self):
        product = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                          "149.00", 0, "v3", TERMS, payment_asset="MOSUL",
                          payment_mint=MOSUL_MINT, payment_program_id=TOKEN_2022_PROGRAM_ID,
                          payment_decimals=6)
        quoted_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        order = create_order(
            self.db, product=product, merchant_wallet=MERCHANT,
            idempotency_key="mosul-checkout-1234", buyer_wallet=BUYER,
            accepted_terms_sha256=TERMS, price_usd="75.50",
            token_price_usd="0.0000025", token_quote_at=quoted_at,
            quote_source="DEX Screener", quote_liquidity_usd="2500.00",
            quote_pair_address="pool-address",
        )
        self.assertEqual(order["amount_raw"], 30_200_000_000_000)
        self.assertEqual(order["amount"], "30200000.000000")
        self.assertEqual(order["asset"], "MOSUL")
        self.assertEqual(order["price_usd"], "75.50")
        self.assertEqual(order["quote_source"], "DEX Screener")
        self.assertIn("amount=30200000.000000", order["solana_pay_uri"])

    def test_mosul_quote_is_required_and_must_be_fresh(self):
        product = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                          "149.00", 0, "v3", TERMS, payment_asset="MOSUL",
                          payment_mint=MOSUL_MINT, payment_program_id=TOKEN_2022_PROGRAM_ID,
                          payment_decimals=6)
        with self.assertRaisesRegex(ValueError, "fresh MOSUL/USD quote"):
            create_order(self.db, product=product, merchant_wallet=MERCHANT,
                         idempotency_key="mosul-checkout-old1", buyer_wallet=BUYER,
                         accepted_terms_sha256=TERMS, price_usd="75.50")
        self.assertEqual(token_amount_raw("1.00", "3", 6), 333334)

    def test_transaction_rejects_wrong_token_program_for_same_mint(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        tx = Rpc(row).transaction(SIGNATURE)
        tx["meta"]["postTokenBalances"][0]["programId"] = TOKEN_2022_PROGRAM_ID
        with self.assertRaisesRegex(ValueError, "wrong Solana token program"):
            verify_transaction(tx, row)

    def test_dynamic_winning_bid_is_the_settled_and_recorded_price(self):
        order = create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key="checkout-auction-dynamic", buyer_wallet=BUYER,
            accepted_terms_sha256=TERMS, price_usd="75.50",
        )
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        result = confirm_order(
            self.db, order_id=order["id"], signature=SIGNATURE,
            claim_secret=order["claim_secret"], product=PRODUCT,
            rpc=Rpc(row, payment_amount=75_500_000), delivery_secret=SECRET,
        )
        self.assertEqual(result["status"], "paid")
        self.assertEqual(self.db.execute(
            "SELECT price_usd FROM completed_sales WHERE order_id=?", (order["id"],)
        ).fetchone()[0], 75.50)

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

    def test_payment_from_another_wallet_is_rejected(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        tx = Rpc(row).transaction(SIGNATURE)
        for balance in tx["meta"]["preTokenBalances"] + tx["meta"]["postTokenBalances"]:
            if balance["accountIndex"] == 3:
                balance["owner"] = "11111111111111111111111111111111"
        with self.assertRaisesRegex(ValueError, "not paid by the winning bidder"):
            verify_transaction(tx, row)
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["accountKeys"] = []
        with self.assertRaises(ValueError):
            verify_transaction(tx, row)

    def test_payment_requires_exact_on_chain_order_memo(self):
        order = self.order()
        row = self.db.execute("SELECT * FROM orders WHERE id=?", (order["id"],)).fetchone()
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["instructions"] = []
        with self.assertRaisesRegex(ValueError, "exact order memo"):
            verify_transaction(tx, row)
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["instructions"][0]["parsed"] = "MOSUL-SALE:wrong"
        with self.assertRaisesRegex(ValueError, "exact order memo"):
            verify_transaction(tx, row)
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["instructions"][0]["programId"] = "11111111111111111111111111111111"
        with self.assertRaisesRegex(ValueError, "exact order memo"):
            verify_transaction(tx, row)
        tx = Rpc(row).transaction(SIGNATURE)
        tx["transaction"]["message"]["instructions"][0] = {
            "programId": MEMO_PROGRAM, "data": b58encode(row["memo"].encode("utf-8")),
        }
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

    def test_seller_terms_signature_binds_identity_wallet_and_hash(self):
        private = Ed25519PrivateKey.generate()
        wallet = b58encode(private.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))
        signed_at = "2026-10-13T12:00:00.000Z"
        message = seller_terms_message(
            legal_name="Example Seller", trade_name="MOSUL HERITAGE STORE",
            wallet=wallet, product=PRODUCT, signed_at=signed_at)
        signature = base64.b64encode(private.sign(message.encode("utf-8"))).decode()
        self.assertEqual(message, verify_seller_terms_signature(
            legal_name="Example Seller", trade_name="MOSUL HERITAGE STORE",
            wallet=wallet, product=PRODUCT, signed_at=signed_at,
            signature_b64=signature))
        with self.assertRaises(PermissionError):
            verify_seller_terms_signature(
                legal_name="Another Seller", trade_name="MOSUL HERITAGE STORE",
                wallet=wallet, product=PRODUCT, signed_at=signed_at,
                signature_b64=signature)

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
