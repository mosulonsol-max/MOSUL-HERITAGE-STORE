import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from readiness import evaluate_readiness


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.product = self.root / "product.json"
        self.assets = self.root / "assets.json"
        self.package = self.root / "delivery.zip"
        self.package.write_bytes(b"private package")
        terms_hash = "a" * 64
        self.product.write_text(json.dumps({
            "id": "LOT-1", "edition": "1/1", "sale_type": "timed_ascending_auction",
            "reserve_policy": "no_hidden_reserve_opening_bid_is_minimum_sale_price",
            "auction_opening_bid_usdc": "100.00", "auction_increment_usdc": "10.00",
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
            "collector_master": {"sha256": "c" * 64, "width": 1024, "height": 1024,
                                 "publicly_accessible": False},
            "delivery_package": {"sha256": hashlib.sha256(b"private package").hexdigest()},
        }
        self.assets.write_text(json.dumps(self.valid_assets))

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


if __name__ == "__main__":
    unittest.main()
