import datetime as dt
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from solders.keypair import Keypair

from core import TOKEN_2022_PROGRAM, comparable_sales, confirm_payment, connect, create_intent, process_refunds, request_refund

MERCHANT = "11111111111111111111111111111111"
BUYER = "So11111111111111111111111111111111111111112"
SIGNATURE = "1" * 64


class Rpc:
    def __init__(self, intent): self.intent = intent
    def transaction(self, signature):
        refund = self.intent["status"] == "refund_requested"
        source = self.intent["merchant"] if refund else BUYER
        destination = BUYER if refund else self.intent["merchant"]
        memo = "REFUND:" + self.intent["id"] if refund else self.intent["memo"]
        return {"meta": {"err": None}, "transaction": {"message": {"accountKeys": [
            {"pubkey": source, "signer": True}], "instructions": [
            {"program": "system", "parsed": {"type": "transfer", "info": {
                "source": source, "destination": destination, "lamports": 1000}}},
            {"program": "spl-memo", "parsed": memo},
        ]}}, "blockTime": int(time.time())}


class TokenRpc(Rpc):
    def __init__(self, intent): self.intent = intent
    def transaction(self, signature):
        i = self.intent
        return {"blockTime": int(time.time()), "meta": {"err": None,
            "preTokenBalances": [
                {"accountIndex": 0, "mint": i["asset_mint"], "owner": i["buyer"],
                 "uiTokenAmount": {"amount": "9000000", "decimals": 6}},
                {"accountIndex": 1, "mint": i["asset_mint"], "owner": i["merchant"],
                 "uiTokenAmount": {"amount": "0", "decimals": 6}},
            ], "postTokenBalances": [
                {"accountIndex": 0, "mint": i["asset_mint"], "owner": i["buyer"],
                 "uiTokenAmount": {"amount": "4000000", "decimals": 6}},
                {"accountIndex": 1, "mint": i["asset_mint"], "owner": i["merchant"],
                 "uiTokenAmount": {"amount": "5000000", "decimals": 6}},
            ]}, "transaction": {"message": {
                "accountKeys": [{"pubkey": "buyer-token-account"}, {"pubkey": "seller-token-account"}],
                "instructions": [
                    {"programId": TOKEN_2022_PROGRAM, "parsed": {"type": "transferChecked", "info": {
                        "source": "buyer-token-account", "destination": "seller-token-account",
                        "mint": i["asset_mint"], "authority": i["buyer"],
                        "tokenAmount": {"amount": "5000000", "decimals": 6}}}},
                    {"program": "spl-memo", "parsed": i["memo"]},
                ]}}}
    def token_mint(self, mint):
        return {"owner": TOKEN_2022_PROGRAM, "data": {"parsed": {"type": "mint", "info": {
            "decimals": 6, "isInitialized": True}}}}


class TokenRefundRpc:
    def __init__(self, intent): self.intent = intent
    def transaction(self, signature):
        i = self.intent
        return {"blockTime": int(time.time()), "meta": {"err": None,
            "preTokenBalances": [
                {"accountIndex": 0, "mint": i["asset_mint"], "owner": i["merchant"],
                 "uiTokenAmount": {"amount": "5000000", "decimals": 6}},
                {"accountIndex": 1, "mint": i["asset_mint"], "owner": i["buyer"],
                 "uiTokenAmount": {"amount": "0", "decimals": 6}},
            ], "postTokenBalances": [
                {"accountIndex": 0, "mint": i["asset_mint"], "owner": i["merchant"],
                 "uiTokenAmount": {"amount": "0", "decimals": 6}},
                {"accountIndex": 1, "mint": i["asset_mint"], "owner": i["buyer"],
                 "uiTokenAmount": {"amount": "5000000", "decimals": 6}},
            ]}, "transaction": {"message": {
                "accountKeys": ["merchant-token-account", "buyer-token-account"],
                "instructions": [
                    {"programId": TOKEN_2022_PROGRAM, "parsed": {"type": "transferChecked", "info": {
                        "source": "merchant-token-account", "destination": "buyer-token-account",
                        "mint": i["asset_mint"], "authority": i["merchant"],
                        "tokenAmount": {"amount": "5000000", "decimals": 6}}}},
                    {"program": "spl-memo", "parsed": "REFUND:" + i["id"]},
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
        self.assertNotIn("refund_token_hash", again)
    def test_confirm_and_first_party_sale(self):
        result = confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        self.assertEqual(result["status"], "paid")
        self.assertEqual(len(comparable_sales(self.db)["comparables"]), 1)
    def test_mosul_token_2022_exact_finalized_transfer(self):
        mint = "So11111111111111111111111111111111111111112"
        intent = create_intent(self.db, idempotency_key="mosul-one", item_id="art-1", category="digital-art-one-of-one",
            amount_lamports=5_000_000, price_usd="25", merchant=MERCHANT, buyer=BUYER,
            asset_mint=mint, asset_decimals=6)
        result = confirm_payment(self.db, intent["id"], SIGNATURE, TokenRpc(intent))
        self.assertEqual(result["status"], "paid")
        self.assertEqual(len(comparable_sales(self.db)["comparables"]), 1)
    def test_mosul_token_wrong_credit_or_mint_rejected(self):
        mint = "So11111111111111111111111111111111111111112"
        intent = create_intent(self.db, idempotency_key="mosul-bad", item_id="art-1", category="digital-art-one-of-one",
            amount_lamports=5_000_000, price_usd="25", merchant=MERCHANT, buyer=BUYER,
            asset_mint=mint, asset_decimals=6)
        bad = TokenRpc(intent)
        original = bad.transaction
        bad.transaction = lambda signature: original(signature) | {"meta": original(signature)["meta"] | {
            "postTokenBalances": [
                {"accountIndex": 0, "mint": mint, "owner": BUYER, "uiTokenAmount": {"amount": "4000000", "decimals": 6}},
                {"accountIndex": 1, "mint": mint, "owner": MERCHANT, "uiTokenAmount": {"amount": "4999999", "decimals": 6}},
            ]}}
        with self.assertRaises(ValueError): confirm_payment(self.db, intent["id"], SIGNATURE, bad)
    def test_wrong_transfer_rejected(self):
        bad = Rpc(self.intent); bad.transaction = lambda _: {"meta":{"err":None},"transaction":{"message":{"instructions":[]}}}
        with self.assertRaises(ValueError): confirm_payment(self.db, self.intent["id"], SIGNATURE, bad)
    def test_expired_transaction_window_rejected(self):
        bad = Rpc(self.intent)
        bad.transaction = lambda _: {"meta": {"err": None}, "blockTime": 1,
            "transaction": {"message": {"instructions": [], "accountKeys": []}}}
        with self.assertRaises(ValueError): confirm_payment(self.db, self.intent["id"], SIGNATURE, bad)
    def test_refund_stays_comparable_until_chain_confirmation(self):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        result = request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        self.assertEqual(result["status"], "refund_requested")
        self.assertEqual(len(comparable_sales(self.db)["comparables"]), 0)
    @patch("core.subprocess.run")
    def test_token_refund_uses_exact_devnet_token_transfer_and_verifies_finality(self, run):
        merchant_key = Keypair()
        mint = str(Keypair().pubkey())
        intent = create_intent(self.db, idempotency_key="mosul-refund-exact", item_id="art-1",
            category="digital-art-one-of-one", amount_lamports=5_000_000, price_usd="25",
            merchant=str(merchant_key.pubkey()), buyer=BUYER, asset_mint=mint, asset_decimals=6)
        confirm_payment(self.db, intent["id"], SIGNATURE, TokenRpc(intent))
        request_refund(self.db, intent["id"], intent["refund_token"])
        keypair_path = Path(self.temp.name) / "merchant.json"
        keypair_path.write_text(merchant_key.to_json(), encoding="utf-8")
        run.return_value.returncode = 0
        run.return_value.stdout = "Signature: " + "1" * 64
        result = process_refunds(self.db, str(keypair_path), TokenRefundRpc(intent))
        self.assertEqual(result[0]["status"], "refunded")
        command = run.call_args.args[0]
        self.assertEqual(command[0:4], ["spl-token", "--program-id", TOKEN_2022_PROGRAM, "--owner"])
        self.assertEqual(command[7:12], ["transfer", "--fund-recipient", mint, "5", BUYER])
        self.assertIn("--program-id", command)
        self.assertIn("--with-memo", command)
        row = self.db.execute("SELECT status FROM payment_intents WHERE id=?", (intent["id"],)).fetchone()
        self.assertEqual(row["status"], "refunded")
    @patch("core.subprocess.run")
    def test_ambiguous_cli_failure_cannot_be_retried_automatically(self, run):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        keypair = Path(self.temp.name) / "key.json"
        keypair.write_text("[]", encoding="utf-8")
        run.return_value.returncode = 1
        run.return_value.stdout = ""
        result = process_refunds(self.db, str(keypair), Rpc(self.intent))
        self.assertEqual(result[0]["status"], "needs_reconciliation")
        status = self.db.execute("SELECT status FROM payment_intents WHERE id=?", (self.intent["id"],)).fetchone()[0]
        self.assertEqual(status, "refund_processing")
    def test_bad_refund_token(self):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent))
        with self.assertRaises(PermissionError): request_refund(self.db, self.intent["id"], "wrong")
    @patch("core.subprocess.run")
    def test_automatic_refund_verifies_chain_before_marking_refunded(self, run):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent)); request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        keypair = Path(self.temp.name) / "key.json"; keypair.write_text("[]")
        run.return_value.returncode = 0; run.return_value.stdout = "Signature: " + "1" * 64
        self.assertEqual(process_refunds(self.db, str(keypair), Rpc(self.db.execute("SELECT * FROM payment_intents").fetchone()))[0]["status"], "refunded")
        self.assertEqual(process_refunds(self.db, str(keypair)), [])
    @patch("core.subprocess.run")
    def test_refund_cli_signature_is_not_enough(self, run):
        confirm_payment(self.db, self.intent["id"], SIGNATURE, Rpc(self.intent)); request_refund(self.db, self.intent["id"], self.intent["refund_token"])
        keypair = Path(self.temp.name) / "key.json"; keypair.write_text("[]")
        run.return_value.returncode = 0; run.return_value.stdout = "Signature: " + "1" * 64
        class WrongRefundRpc:
            def transaction(self, _): return {"meta": {"err": None}, "transaction": {"message": {"instructions": []}}}
        self.assertEqual(process_refunds(self.db, str(keypair), WrongRefundRpc())[0]["status"], "unverified")
        row = self.db.execute("SELECT status FROM payment_intents WHERE id=?", (self.intent["id"],)).fetchone()
        self.assertEqual(row["status"], "refund_processing")


if __name__ == "__main__": unittest.main()
