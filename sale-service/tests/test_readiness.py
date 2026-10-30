import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from readiness import evaluate_readiness


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.product = self.root / "product.json"
        self.assets = self.root / "assets.json"
        self.package = self.root / "delivery.zip"
        terms_hash = "a" * 64
        self.product.write_text(json.dumps({
            "id": "LOT-1", "edition": "1/1", "sale_type": "timed_ascending_auction",
            "reserve_policy": "no_hidden_reserve_opening_bid_is_minimum_sale_price",
            "auction_opening_bid_usd": "100.00", "auction_increment_usd": "10.00",
            "terms_version": "v1", "terms_sha256": terms_hash,
        }))
        self.valid_assets = {
            "product_id": "LOT-1", "terms_version": "v1", "terms_sha256": terms_hash,
            "source_provenance": {
                "page_url": "https://www.loc.gov/item/1/",
                "resource_url": "https://tile.loc.gov/reference.jpg", "catalog_id": "1",
                "rights_review": "no_known_restrictions", "creator": "Archive",
            },
            "public_preview": {"url": "https://example.test/preview.png", "sha256": "b" * 64,
                               "watermarked": True},
            "collector_master": {"sha256": hashlib.sha256(b"private master").hexdigest(),
                                 "width": 1024, "height": 1024,
                                 "publicly_accessible": False},
            "delivery_package": {},
        }
        self.write_package("v1", terms_hash)
        self.assets.write_text(json.dumps(self.valid_assets))

    def write_package(self, version, terms_hash):
        master_name = "MOSUL-GENESIS-000001-Collector-Master.png"
        files = {
            master_name: b"private master",
            "LICENSE.txt": b"buyer license",
            "certificate.json": json.dumps({
                "product_id": "LOT-1", "terms_version": version,
                "terms_sha256": terms_hash,
                "collector_master_sha256": hashlib.sha256(b"private master").hexdigest(),
                "public_preview_sha256": "b" * 64,
            }).encode(),
        }
        files["SHA256SUMS"] = "".join(
            f"{hashlib.sha256(files[name]).hexdigest()}  {name}\n"
            for name in (master_name, "certificate.json", "LICENSE.txt")
        ).encode()
        with zipfile.ZipFile(self.package, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        self.valid_assets["delivery_package"]["sha256"] = hashlib.sha256(
            self.package.read_bytes()).hexdigest()

    def tearDown(self):
        self.temp.cleanup()

    def test_all_gates_can_pass_without_enabling_payment(self):
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_path=self.package, seller_signature_valid=True,
            auction_configured=True, seller_disclosure_complete=True,
        )
        self.assertTrue(result["asset_ready"])
        self.assertTrue(result["auction_ready"])
        self.assertFalse(result["payment_enabled"])
        self.assertEqual([], result["blockers"])

    def test_missing_master_and_package_fail_closed(self):
        broken = dict(self.valid_assets)
        broken["collector_master"] = {}
        broken["delivery_package"] = {"sha256": "0" * 64}
        self.assets.write_text(json.dumps(broken))
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_path=self.package, seller_signature_valid=True,
            auction_configured=True, seller_disclosure_complete=True,
        )
        self.assertFalse(result["auction_ready"])
        self.assertIn("collector_master", result["blockers"])
        self.assertIn("delivery_package", result["blockers"])

    def test_verified_package_can_be_checked_from_memory(self):
        self.assets.write_text(json.dumps(self.valid_assets))
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_bytes=self.package.read_bytes(),
            seller_signature_valid=True, auction_configured=True,
            seller_disclosure_complete=True,
        )
        self.assertTrue(result["asset_ready"])
        self.assertTrue(result["auction_ready"])

    def test_in_memory_package_digest_mismatch_fails_closed(self):
        self.assets.write_text(json.dumps(self.valid_assets))
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_bytes=b"tampered",
            seller_signature_valid=True, auction_configured=True,
            seller_disclosure_complete=True,
        )
        self.assertIn("delivery_package", result["blockers"])

    def test_terms_mismatch_fails_closed(self):
        broken = dict(self.valid_assets)
        broken["terms_sha256"] = "d" * 64
        self.assets.write_text(json.dumps(broken))
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_path=self.package, seller_signature_valid=True,
            auction_configured=True, seller_disclosure_complete=True,
        )
        self.assertIn("seller_terms_signature", result["blockers"])

    def test_old_certificate_fails_even_when_zip_hash_matches_manifest(self):
        self.write_package("v0", "d" * 64)
        self.assets.write_text(json.dumps(self.valid_assets))
        result = evaluate_readiness(
            product_path=self.product, asset_manifest_path=self.assets,
            delivery_package_path=self.package, seller_signature_valid=True,
            auction_configured=True, seller_disclosure_complete=True,
        )
        self.assertIn("delivery_package", result["blockers"])


if __name__ == "__main__":
    unittest.main()
