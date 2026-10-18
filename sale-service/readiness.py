"""Fail-closed, machine-readable auction readiness checks.

The checker deliberately separates a presentable lot from payment activation.
It never treats a generated preview, a missing private package, or an unsigned
terms revision as a saleable product.
"""
from __future__ import annotations

import hashlib
import json
import re
import argparse
import zipfile
from pathlib import Path
from urllib.parse import urlparse


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _https(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)


def _gate(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _delivery_matches_product(path: Path, product: dict, assets: dict) -> bool:
    """Check that the pinned ZIP actually contains this terms revision and master."""
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            master_name = "MOSUL-GENESIS-000001-Collector-Master.png"
            required = {master_name, "certificate.json", "SHA256SUMS", "LICENSE.txt"}
            if names != required or len(archive.infolist()) != len(required):
                return False
            # Bound decompression even if a supplied archive has a valid-looking header.
            if any(info.file_size > 50_000_000 for info in archive.infolist()):
                return False
            files = {name: archive.read(name) for name in required}
            certificate = json.loads(files["certificate.json"])
            if not isinstance(certificate, dict):
                return False
            hashes = {
                name: hashlib.sha256(files[name]).hexdigest()
                for name in (master_name, "certificate.json", "LICENSE.txt")
            }
            sums = "".join(f"{hashes[name]}  {name}\n" for name in
                           (master_name, "certificate.json", "LICENSE.txt"))
            return (
                files["SHA256SUMS"] == sums.encode("ascii")
                and certificate.get("product_id") == product.get("id")
                and certificate.get("terms_version") == product.get("terms_version")
                and certificate.get("terms_sha256") == product.get("terms_sha256")
                and certificate.get("collector_master_sha256") == hashes[master_name]
                and hashes[master_name] == assets.get("collector_master", {}).get("sha256")
                and certificate.get("public_preview_sha256") ==
                assets.get("public_preview", {}).get("sha256")
            )
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError):
        return False


def evaluate_readiness(*, product_path: str | Path, asset_manifest_path: str | Path,
                       delivery_package_path: str | Path | None = None,
                       seller_signature_valid: bool = False,
                       auction_configured: bool = False,
                       seller_disclosure_complete: bool = False) -> dict:
    """Return deterministic gates suitable for an API and CI artifact."""
    product = json.loads(Path(product_path).read_text(encoding="utf-8"))
    try:
        assets = json.loads(Path(asset_manifest_path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        assets = {}

    source = assets.get("source_provenance") if isinstance(assets, dict) else None
    source = source if isinstance(source, dict) else {}
    preview = assets.get("public_preview") if isinstance(assets, dict) else None
    preview = preview if isinstance(preview, dict) else {}
    master = assets.get("collector_master") if isinstance(assets, dict) else None
    master = master if isinstance(master, dict) else {}
    package = assets.get("delivery_package") if isinstance(assets, dict) else None
    package = package if isinstance(package, dict) else {}

    product_gate = (
        product.get("id") == assets.get("product_id")
        and product.get("edition") == "1/1"
        and product.get("sale_type") == "timed_ascending_auction"
        and product.get("reserve_policy") == "no_hidden_reserve_opening_bid_is_minimum_sale_price"
        and bool(product.get("auction_opening_bid_usd"))
        and bool(product.get("auction_increment_usd"))
    )
    source_gate = (
        _https(source.get("page_url"))
        and _https(source.get("resource_url"))
        and bool(source.get("catalog_id"))
        and source.get("rights_review") in {"public_domain", "no_known_restrictions"}
        and bool(source.get("creator"))
    )
    preview_gate = (
        _https(preview.get("url"))
        and bool(SHA256_RE.fullmatch(str(preview.get("sha256", ""))))
        and preview.get("watermarked") is True
    )
    master_gate = (
        bool(SHA256_RE.fullmatch(str(master.get("sha256", ""))))
        and int(master.get("width", 0) or 0) >= 512
        and int(master.get("height", 0) or 0) >= 512
        and master.get("publicly_accessible") is False
    )

    delivery = Path(delivery_package_path) if delivery_package_path else None
    expected_package_hash = str(package.get("sha256", ""))
    package_gate = bool(
        delivery and delivery.is_file()
        and SHA256_RE.fullmatch(expected_package_hash)
        and sha256_file(delivery) == expected_package_hash
        and _delivery_matches_product(delivery, product, assets)
    )
    terms_gate = (
        assets.get("terms_version") == product.get("terms_version")
        and assets.get("terms_sha256") == product.get("terms_sha256")
        and bool(SHA256_RE.fullmatch(str(product.get("terms_sha256", ""))))
        and seller_signature_valid
    )

    gates = [
        _gate("auction_product", product_gate,
              "1/1 timed ascending auction with disclosed opening bid and increment"),
        _gate("source_provenance", source_gate,
              "official HTTPS catalogue/resource records and reusable-rights review"),
        _gate("public_preview", preview_gate,
              "watermarked HTTPS preview with a pinned SHA-256"),
        _gate("collector_master", master_gate,
              "private Collector Master with dimensions and pinned SHA-256"),
        _gate("delivery_package", package_gate,
              "private ZIP hash, contents, master and certificate terms match this product"),
        _gate("seller_terms_signature", terms_gate,
              "seller wallet signature matches this product and exact terms hash"),
        _gate("seller_disclosure", seller_disclosure_complete,
              "the disclosures required by the signed terms are configured"),
        _gate("auction_window", auction_configured,
              "auction ID, opening time and closing time are configured"),
    ]
    blockers = [gate["name"] for gate in gates if not gate["passed"]]
    asset_names = {"source_provenance", "public_preview", "collector_master", "delivery_package"}
    asset_ready = all(gate["passed"] for gate in gates if gate["name"] in asset_names)
    auction_ready = not blockers
    return {
        "schema_version": "1.0",
        "product_id": product.get("id"),
        "asset_ready": asset_ready,
        "auction_ready": auction_ready,
        "payment_enabled": False,
        "gates": gates,
        "blockers": blockers,
        "safety": "Payment remains independently disabled until a separate production review.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the auction readiness gates")
    parser.add_argument("--product", required=True)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--delivery-package")
    parser.add_argument("--seller-signature-valid", action="store_true")
    parser.add_argument("--auction-configured", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    result = evaluate_readiness(
        product_path=args.product, asset_manifest_path=args.assets,
        delivery_package_path=args.delivery_package,
        seller_signature_valid=args.seller_signature_valid,
        auction_configured=args.auction_configured,
        seller_disclosure_complete=False,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if args.require_ready and not result["auction_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
