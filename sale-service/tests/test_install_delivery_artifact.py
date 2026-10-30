import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from install_delivery_artifact import install_artifact


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, limit):
        return self.payload[:limit]


class InstallEncryptedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.payload = b"MOSUL-AESGCM-V1\x00ciphertext"
        self.manifest = self.root / "assets.json"
        self.manifest.write_text(json.dumps({
            "delivery_package": {
                "encrypted_artifact_sha256": hashlib.sha256(self.payload).hexdigest()
            }
        }))
        self.target = self.root / "private" / "package.zip.aes"

    def tearDown(self):
        self.temp.cleanup()

    def test_download_is_pinned_and_installed_atomically(self):
        with patch("install_delivery_artifact.urlopen",
                   return_value=FakeResponse(self.payload)):
            result = install_artifact(
                url="https://example.test/encrypted.aes",
                destination=self.target, manifest_path=self.manifest)
        self.assertEqual(self.target, result)
        self.assertEqual(self.payload, self.target.read_bytes())
        self.assertEqual([], list(self.target.parent.glob(".delivery-*.tmp")))

    def test_digest_mismatch_does_not_replace_existing_file(self):
        self.target.parent.mkdir()
        self.target.write_bytes(b"previous")
        with patch("install_delivery_artifact.urlopen",
                   return_value=FakeResponse(b"tampered")):
            with self.assertRaisesRegex(ValueError, "does not match"):
                install_artifact(
                    url="https://example.test/encrypted.aes",
                    destination=self.target, manifest_path=self.manifest)
        self.assertEqual(b"previous", self.target.read_bytes())

    def test_non_https_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            install_artifact(
                url="http://example.test/encrypted.aes",
                destination=self.target, manifest_path=self.manifest)


if __name__ == "__main__":
    unittest.main()
