import base64
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from scripts.package_auction_product import MAGIC, build


class AuctionPackageTests(unittest.TestCase):
    def test_builds_signed_encrypted_package_without_publishing_master(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            master, preview = root / "master.png", root / "preview.png"
            Image.new("RGB", (512, 512), "navy").save(master)
            Image.new("RGB", (512, 512), "gold").save(preview)
            product = root / "product.json"
            product.write_text(json.dumps({
                "id": "LOT-1", "title": "Lot", "edition": "1/1",
                "terms_version": "v1", "terms_sha256": "a" * 64,
            }))
            assets = root / "assets.json"
            assets.write_text(json.dumps({
                "product_id": "LOT-1", "source_provenance": {
                    "page_url": "https://www.loc.gov/",
                    "resource_url": "https://tile.loc.gov/reference.jpg",
                },
                "delivery_package": {"contents": []},
            }))
            out = root / "out"
            result = build(
                master_path=master, preview_path=preview, product_path=product,
                assets_path=assets, output_dir=out,
                signing_key_b64=base64.b64encode(bytes(range(32))).decode(),
                preview_url="https://example.test/preview.png",
                generation={
                    "reference_url": "https://tile.loc.gov/reference.jpg",
                    "reference_sha256": "b" * 64,
                    "reference_mode": "image-to-image",
                },
            )
            encrypted = (out / "MOSUL-GENESIS-000001-package.zip.aes").read_bytes()
            self.assertTrue(encrypted.startswith(MAGIC))
            self.assertNotIn(master.read_bytes(), encrypted)
            manifest = json.loads((out / "MOSUL-GENESIS-000001.assets.json").read_text())
            self.assertEqual(result["package_sha256"], manifest["delivery_package"]["sha256"])
            self.assertFalse(manifest["collector_master"]["publicly_accessible"])

    def test_rejects_text_only_product_when_archival_resource_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            master, preview = root / "master.png", root / "preview.png"
            Image.new("RGB", (512, 512), "navy").save(master)
            Image.new("RGB", (512, 512), "gold").save(preview)
            product = root / "product.json"
            product.write_text(json.dumps({
                "id": "LOT-1", "title": "Lot", "edition": "1/1",
                "terms_version": "v1", "terms_sha256": "a" * 64,
            }))
            assets = root / "assets.json"
            assets.write_text(json.dumps({
                "product_id": "LOT-1", "source_provenance": {
                    "resource_url": "https://tile.loc.gov/reference.jpg",
                }, "delivery_package": {"contents": []},
            }))
            with self.assertRaisesRegex(ValueError, "image-to-image"):
                build(master_path=master, preview_path=preview,
                      product_path=product, assets_path=assets,
                      output_dir=root / "out",
                      signing_key_b64=base64.b64encode(bytes(range(32))).decode(),
                      preview_url="https://example.test/preview.png",
                      generation={})


if __name__ == "__main__":
    unittest.main()
