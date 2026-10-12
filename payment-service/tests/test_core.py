import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import comparable_sales, confirm_payment, connect, create_intent, process_refunds, request_refund

MERCHANT = "11111111111111111111111111111111"
BUYER = "So11111111111111111111111111111111111111112"
SIGNATURE = "1" * 64


class Rpc:
    def __init__(self, intent): self.intent = intent
    def transaction(self, signature):
        return {"meta": {"err": None}, "transaction": {"message": {"instructions": [
            {"program": "system", "parsed": {"type": "transfer", "info": {
                "source": BUYER, "destination": MERCHANT, "lamports": 1000}}},
            {"program": "spl-memo", "parsed": self.intent["memo"]},
        ]}}}


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.db = connect(Path(self.temp.name) / "p.db")
        self.intent = create_intent(self.db, idempotency_key="one", item_id="art-1", category="digital-art-one-of-one",
            amount_lamports=1000, price_usd="25", merchant=MERCHANT, buyer=BUYER)
    def tearDown(self): self.db.close(); self.temp.cleanup()
    def test_idempotent_intent(self):
        again = create_intent(self.db, idempotency_key="one", item_id="art-1", category="digital-art-one-of-one",
            amount_lamports=1000, price_usd="25", merchant=MERCHANT, buyer=BUYER)
        self.assertEqual(again["id"], self.intent["id"])
    def test_confirm_and_first_party_sale(self):
        result = confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        self.assertEqual(result["status"], "paid")
        self.assertEqual(len(comparable_sales(self.db)["comparables"]), 1)
    def test_wrong_transfer_rejected(self):
        bad = Rpc(self.intent); bad.transaction = lambda _: {"meta":{"err":None},"transaction":{"message":{"instructions":[]}}}
        with self.assertRaises(ValueError): confirm_payment(self.db, self.intent["id"], SIGNATURE, bad)
    def test_refund_removes_comparable(self):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        result = request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        self.assertEqual(result["status"], "refund_requested")
        self.assertEqual(comparable_sales(self.db)["comparables"], [])
    def test_bad_refund_token(self):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        with self.assertRaises(PermissionError): request_refund(self.db, self.intent["id"], "wrong")
    @patch("core.subprocess.run")
    def test_automatic_refund_is_idempotent(self, run):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent)); request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        keypair = Path(self.temp.name) / "key.json"; keypair.write_text("[]")
        run.return_value.returncode = 0; run.return_value.stdout = "Signature: " + "3" * 64
        self.assertEqual(process_refunds(self.db, str(keypair))[0]["status"], "refunded")
        self.assertEqual(process_refunds(self.db, str(keypair)), [])


if __name__ == "__main__": unittest.main()
