import base64
import datetime as dt
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from auction import (AuctionConfig, auction_snapshot, consume_winner_order_challenge,
                     create_bid_challenge, create_winner_order_challenge,
                     payable_winner, submit_bid, usdc_raw, winning_bid)
from core import Product, b58encode, connect, create_order, renew_pending_order_claim

UTC = dt.timezone.utc
NOW = dt.datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
CFG = AuctionConfig("genesis-000001", NOW - dt.timedelta(hours=1),
                    NOW + dt.timedelta(days=7), usdc_raw("50"), usdc_raw("5"))
TERMS = "a" * 64
MERCHANT = "EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
PRODUCT = Product("MOSUL-GENESIS-000001", "Mosul 1932", "digital-art-one-of-one",
                  "0.00", 0, "v1", TERMS)


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

    def test_expired_winner_defaults_and_next_bidder_can_pay(self):
        key1, wallet1 = self.key()
        key2, wallet2 = self.key()
        self.bid(key1, wallet1, "50")
        self.bid(key2, wallet2, "55")
        winner = winning_bid(self.db, CFG, "MOSUL-GENESIS-000001",
                             CFG.ends_at + dt.timedelta(seconds=1))
        self.db.execute("UPDATE auction_bids SET status='selected' WHERE id=?", (winner["id"],))
        expiry = CFG.ends_at + dt.timedelta(hours=24)
        order = create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key="auction-selection-001", buyer_wallet=wallet2,
            accepted_terms_sha256=TERMS, price_usdc="55", auction_bid_id=winner["id"],
        )
        self.db.execute("UPDATE orders SET expires_at=? WHERE id=?",
                        (expiry.isoformat(), order["id"]))
        next_bid = winning_bid(self.db, CFG, "MOSUL-GENESIS-000001",
                               expiry + dt.timedelta(seconds=1))
        self.assertEqual(next_bid["bidder_wallet"], wallet1)
        statuses = dict(self.db.execute("SELECT bidder_wallet,status FROM auction_bids"))
        self.assertEqual(statuses[wallet2], "defaulted")

    def test_auction_configuration_and_bid_amount_are_validated(self):
        with self.assertRaises(ValueError):
            AuctionConfig("bad", NOW, NOW - dt.timedelta(minutes=1), 1, 1)
        with self.assertRaises(ValueError):
            usdc_raw("0.001")

    def test_winner_order_requires_fresh_wallet_signature_and_single_use(self):
        winner_key, winner_wallet = self.key()
        attacker_key, _ = self.key()
        self.bid(winner_key, winner_wallet, "50")
        closed = CFG.ends_at + dt.timedelta(seconds=1)
        winner = winning_bid(self.db, CFG, PRODUCT.id, closed)
        challenge = create_winner_order_challenge(
            self.db, CFG, PRODUCT.id, MERCHANT, "winner-order-123", TERMS, closed,
        )
        self.assertEqual(challenge["bidder_wallet"], winner_wallet)
        forged = base64.b64encode(attacker_key.sign(challenge["message"].encode())).decode()
        with self.assertRaisesRegex(PermissionError, "signature did not verify"):
            consume_winner_order_challenge(
                self.db, CFG, challenge["challenge_id"], forged, winner=winner,
                merchant_wallet=MERCHANT, idempotency_key="winner-order-123",
                terms_sha256=TERMS, now=closed,
            )
        signed = base64.b64encode(winner_key.sign(challenge["message"].encode())).decode()
        with self.assertRaisesRegex(PermissionError, "does not match"):
            consume_winner_order_challenge(
                self.db, CFG, challenge["challenge_id"], signed, winner=winner,
                merchant_wallet=MERCHANT, idempotency_key="different-order-123",
                terms_sha256=TERMS, now=closed,
            )
        consume_winner_order_challenge(
            self.db, CFG, challenge["challenge_id"], signed, winner=winner,
            merchant_wallet=MERCHANT, idempotency_key="winner-order-123",
            terms_sha256=TERMS, now=closed,
        )
        with self.assertRaisesRegex(PermissionError, "already used"):
            consume_winner_order_challenge(
                self.db, CFG, challenge["challenge_id"], signed, winner=winner,
                merchant_wallet=MERCHANT, idempotency_key="winner-order-123",
                terms_sha256=TERMS, now=closed,
            )

    def test_expired_winner_order_challenge_is_rejected(self):
        winner_key, winner_wallet = self.key()
        self.bid(winner_key, winner_wallet, "50")
        closed = CFG.ends_at + dt.timedelta(seconds=1)
        winner = winning_bid(self.db, CFG, PRODUCT.id, closed)
        challenge = create_winner_order_challenge(
            self.db, CFG, PRODUCT.id, MERCHANT, "winner-order-123", TERMS, closed,
        )
        signed = base64.b64encode(winner_key.sign(challenge["message"].encode())).decode()
        with self.assertRaisesRegex(PermissionError, "expired"):
            consume_winner_order_challenge(
                self.db, CFG, challenge["challenge_id"], signed, winner=winner,
                merchant_wallet=MERCHANT, idempotency_key="winner-order-123",
                terms_sha256=TERMS, now=closed + dt.timedelta(minutes=6),
            )

    def test_winner_can_recover_lost_order_claim_with_new_signature(self):
        now = dt.datetime.now(UTC).replace(microsecond=0)
        cfg = AuctionConfig("genesis-recovery", now - dt.timedelta(hours=1),
                            now + dt.timedelta(seconds=10), usdc_raw("50"), usdc_raw("5"))
        key, wallet = self.key()
        bid_challenge = create_bid_challenge(self.db, cfg, wallet, "50", TERMS, now)
        bid_signature = base64.b64encode(key.sign(bid_challenge["message"].encode())).decode()
        bid = submit_bid(self.db, cfg, bid_challenge["challenge_id"], bid_signature, now)
        closed = now + dt.timedelta(seconds=11)
        order = create_order(
            self.db, product=PRODUCT, merchant_wallet=MERCHANT,
            idempotency_key="winner-order-original", buyer_wallet=wallet,
            accepted_terms_sha256=TERMS, price_usdc="50", auction_bid_id=bid["bid_id"],
        )
        self.db.execute("UPDATE auction_bids SET status='selected' WHERE id=?", (bid["bid_id"],))
        winner, active = payable_winner(self.db, cfg, PRODUCT.id, closed)
        self.assertEqual(active["id"], order["id"])
        challenge = create_winner_order_challenge(
            self.db, cfg, PRODUCT.id, MERCHANT, "winner-order-recovery", TERMS, closed,
        )
        signed = base64.b64encode(key.sign(challenge["message"].encode())).decode()
        consume_winner_order_challenge(
            self.db, cfg, challenge["challenge_id"], signed, winner=winner,
            merchant_wallet=MERCHANT, idempotency_key="winner-order-recovery",
            terms_sha256=TERMS, now=closed,
        )
        restored = renew_pending_order_claim(
            self.db, order_id=active["id"], buyer_wallet=wallet,
            auction_bid_id=winner["id"], merchant_wallet=MERCHANT, product=PRODUCT,
        )
        self.assertEqual(restored["id"], order["id"])
        self.assertNotEqual(restored["claim_secret"], order["claim_secret"])
        with self.assertRaises(PermissionError):
            renew_pending_order_claim(
                self.db, order_id=active["id"], buyer_wallet=MERCHANT,
                auction_bid_id=winner["id"], merchant_wallet=MERCHANT,
                product=PRODUCT,
            )


if __name__ == "__main__":
    unittest.main()
