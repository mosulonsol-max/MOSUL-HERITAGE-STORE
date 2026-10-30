import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from delivery import MAGIC, _delivery_key, load_private_package


class EncryptedDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "package.zip.aes"
        self.seed = base64.b64encode(bytes(range(32))).decode()
        self.product_id = "LOT-1"
        self.package = b"private zip bytes"
        self.nonce = bytes(range(12))
        self.ciphertext = AESGCM(_delivery_key(self.seed)).encrypt(
            self.nonce, self.package, self.product_id.encode())
        self.path.write_bytes(MAGIC + self.nonce + self.ciphertext)
        self.encrypted_hash = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.package_hash = hashlib.sha256(self.package).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def load(self, **changes):
        values = {
            "signing_seed_b64": self.seed,
            "expected_encrypted_sha256": self.encrypted_hash,
            "expected_package_sha256": self.package_hash,
            "product_id": self.product_id,
        }
        values.update(changes)
        return load_private_package(self.path, **values)

    def test_decrypts_only_when_both_pinned_hashes_match(self):
        self.assertEqual(self.package, self.load())

    def test_rejects_modified_ciphertext(self):
        raw = self.path.read_bytes()
        self.path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, "encrypted artifact SHA-256"):
            self.load()

    def test_rejects_wrong_seed_or_product_id(self):
        wrong_seed = base64.b64encode(bytes(reversed(range(32)))).decode()
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            self.load(signing_seed_b64=wrong_seed)
        with self.assertRaisesRegex(ValueError, "authentication failed"):
            self.load(product_id="OTHER-LOT")

    def test_rejects_mismatched_decrypted_digest(self):
        with self.assertRaisesRegex(ValueError, "decrypted package SHA-256"):
            self.load(expected_package_sha256="0" * 64)


if __name__ == "__main__":
    unittest.main()
