import base64
import sys
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sale-service"))
from core import b58encode
from token_association import association_message, verify_record


class TokenAssociationTests(unittest.TestCase):
    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        public = self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.wallet = b58encode(public)
        self.mint = b58encode(Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
        self.signed_at = "2026-10-17T12:00:00Z"
        self.message = association_message(self.signed_at, token_mint=self.mint,
                                           receiving_wallet=self.wallet)
        self.record = {
            "project": "MOSUL HERITAGE STORE", "token_name": "MOSUL",
            "network": "solana-mainnet-beta", "token_mint": self.mint,
            "project_receiving_wallet": self.wallet,
            "statement_version": "2026-10-17-v1", "signed_at": self.signed_at,
            "message": self.message,
            "signature_base64": base64.b64encode(self.private.sign(self.message.encode())).decode(),
        }

    def test_verifies_exact_signed_record(self):
        self.assertEqual(verify_record(self.record, expected_mint=self.mint,
                                       expected_wallet=self.wallet), self.message)

    def test_rejects_changed_mint_even_when_other_fields_are_present(self):
        changed = dict(self.record, token_mint="11111111111111111111111111111111")
        with self.assertRaises(ValueError):
            verify_record(changed, expected_mint=self.mint, expected_wallet=self.wallet)

    def test_rejects_signature_from_different_message(self):
        changed = dict(self.record, message=self.message + "\nChanged")
        with self.assertRaises(ValueError):
            verify_record(changed, expected_mint=self.mint, expected_wallet=self.wallet)


if __name__ == "__main__":
    unittest.main()
