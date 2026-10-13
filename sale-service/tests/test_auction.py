import base64
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from auction import (AuctionConfig, auction_snapshot, create_bid_challenge,
                     submit_bid, usdc_raw, winning_bid)
from core import b58encode, connect

UTC = dt.timezone.utc
NOW = dt.datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
CFG = AuctionConfig("genesis-000001", NOW - dt.timedelta(hours=1),
                    NOW + dt.timedelta(days=7), usdc_raw("50"), usdc_raw("5"))
TERMS = "a" * 64


class AuctionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / "sales.db")

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def key(self):
        private = Ed25519PrivateKey.generate()
        pub = private.public_key().public_bytes(serialization.Encoding.Raw,
                                               serialization.PublicFormat.Raw)
        return private, b58encode(pub)

    def bid(self, key, wallet, amount):
        challenge = create_bid_challenge(self.db, CFG, wallet, amount, TERMS, NOW)
        signature = key.sign(challenge["message"].encode())
        return submit_bid(self.db, CFG, challenge["challenge_id"],
                          base64.b64encode(signature).decode(), NOW)

    def test_wallet_signed_bid_sets_auction_leader_without_collecting_money(self):
        key, wallet = self.key()
        bid = self.bid(key, wallet, "50")
        self.assertEqual(bid["status"], "accepted")
        snapshot = auction_snapshot(self.db, CFG, NOW)
        self.assertEqual(snapshot["highest_bid_usdc"], "50.00")
        self.assertNotIn(wallet, str(snapshot))

    def test_minimum_increment_and_tampered_signature_are_rejected(self):
        key, wallet = self.key()
        self.bid(key, wallet, "50")
        other_key, other_wallet = self.key()
        with self.assertRaises(ValueError):
            create_bid_challenge(self.db, CFG, other_wallet, "54.99", TERMS, NOW)
        challenge = create_bid_challenge(self.db, CFG, other_wallet, "55", TERMS, NOW)
        with self.assertRaises(PermissionError):
            submit_bid(self.db, CFG, challenge["challenge_id"],
                       base64.b64encode(key.sign(challenge["message"].encode())).decode(), NOW)

    def test_used_challenge_cannot_be_replayed(self):
        key, wallet = self.key()
        challenge = create_bid_challenge(self.db, CFG, wallet, "50", TERMS, NOW)
        signature = base64.b64encode(key.sign(challenge["message"].encode())).decode()
        submit_bid(self.db, CFG, challenge["challenge_id"], signature, NOW)
        with self.assertRaises(ValueError):
            submit_bid(self.db, CFG, challenge["challenge_id"], signature, NOW)

    def test_highest_valid_bid_is_selected_only_after_close(self):
        key1, wallet1 = self.key()
        key2, wallet2 = self.key()
        self.bid(key1, wallet1, "50")
        self.bid(key2, wallet2, "55")
        with self.assertRaises(ValueError):
            winning_bid(self.db, CFG, "MOSUL-GENESIS-000001", NOW)
        bid = winning_bid(self.db, CFG, "MOSUL-GENESIS-000001",
                          CFG.ends_at + dt.timedelta(seconds=1))
        self.assertEqual(bid["bidder_wallet"], wallet2)
        self.assertEqual(bid["amount_raw"], usdc_raw("55"))

    def test_auction_configuration_and_bid_amount_are_validated(self):
        with self.assertRaises(ValueError):
            AuctionConfig("bad", NOW, NOW - dt.timedelta(minutes=1), 1, 1)
        with self.assertRaises(ValueError):
            usdc_raw("0.001")


if __name__ == "__main__":
    unittest.main()
