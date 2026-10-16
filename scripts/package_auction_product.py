#!/usr/bin/env python3
"""Create and encrypt a private 1/1 delivery package from an approved master."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-engine"))
from mosul_ai.provenance import sign_record

MAGIC = b"MOSUL-AESGCM-V1\0"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def derived_delivery_key(signing_seed_b64: str) -> bytes:
    seed = base64.b64decode(signing_seed_b64, validate=True)
    if len(seed) != 32:
        raise ValueError("ARTWORK_SIGNING_KEY_B64 must contain a 32-byte Ed25519 seed")
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=b"MOSUL HERITAGE private delivery package encryption v1",
    ).derive(seed)


def deterministic_zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, files[name])
    return output.getvalue()


def build(*, master_path: Path, preview_path: Path, product_path: Path,
          assets_path: Path, output_dir: Path, signing_key_b64: str,
          preview_url: str, generation: dict | None = None) -> dict:
    product = json.loads(product_path.read_text(encoding="utf-8"))
    assets = json.loads(assets_path.read_text(encoding="utf-8"))
    if product["id"] != assets["product_id"]:
        raise ValueError("product and asset manifest IDs differ")
    master = master_path.read_bytes()
    preview = preview_path.read_bytes()
    with Image.open(io.BytesIO(master)) as image:
        width, height = image.size
        if image.format != "PNG" or width < 512 or height < 512:
            raise ValueError("Collector Master must be a PNG at least 512x512")
    with Image.open(io.BytesIO(preview)) as image:
        if image.format != "PNG":
            raise ValueError("public preview must be a PNG")

    certificate = {
        "schema_version": "1.0", "product_id": product["id"],
        "title": product["title"], "edition": product["edition"],
        "classification": "AI-generated interpretive artwork informed by the cited archival record; not a historical photograph.",
        "collector_master_sha256": digest(master),
        "public_preview_sha256": digest(preview),
        "source_provenance": assets["source_provenance"],
        "generation": generation or {},
        "terms_version": product["terms_version"],
        "terms_sha256": product["terms_sha256"],
    }
    certificate["provenance_signature"] = sign_record(certificate, signing_key_b64)
    certificate_bytes = (json.dumps(certificate, ensure_ascii=False, indent=2) + "\n").encode()
    license_text = (
        "MOSUL HERITAGE STORE — Collector package\n\n"
        "Rights are governed by the exact auction and buyer terms identified in certificate.json.\n"
        "The archival source remains subject to its cited Library of Congress rights record.\n"
    ).encode()
    sums = (
        f"{digest(master)}  MOSUL-GENESIS-000001-Collector-Master.png\n"
        f"{digest(certificate_bytes)}  certificate.json\n"
        f"{digest(license_text)}  LICENSE.txt\n"
    ).encode()
    package = deterministic_zip({
        "MOSUL-GENESIS-000001-Collector-Master.png": master,
        "certificate.json": certificate_bytes,
        "LICENSE.txt": license_text,
        "SHA256SUMS": sums,
    })
    nonce = os.urandom(12)
    encrypted = MAGIC + nonce + AESGCM(derived_delivery_key(signing_key_b64)).encrypt(
        nonce, package, product["id"].encode())

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "MOSUL-GENESIS-000001-preview.png").write_bytes(preview)
    (output_dir / "MOSUL-GENESIS-000001-certificate.json").write_bytes(certificate_bytes)
    (output_dir / "MOSUL-GENESIS-000001-package.zip.aes").write_bytes(encrypted)
    assets["public_preview"] = {
        "url": preview_url, "sha256": digest(preview), "watermarked": True,
    }
    assets["collector_master"] = {
        "sha256": digest(master), "width": width, "height": height,
        "publicly_accessible": False,
    }
    assets["delivery_package"].update({
        "sha256": digest(package),
        "encrypted_artifact_sha256": digest(encrypted),
        "encryption": "AES-256-GCM; key derived with HKDF-SHA256 from the artwork signing seed",
    })
    manifest_path = output_dir / "MOSUL-GENESIS-000001.assets.json"
    manifest_path.write_text(json.dumps(assets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"manifest": str(manifest_path), "package_sha256": digest(package),
            "encrypted_artifact_sha256": digest(encrypted)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--product", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--preview-url", required=True)
    parser.add_argument("--generation-metadata", type=Path)
    args = parser.parse_args()
    key = os.environ.get("ARTWORK_SIGNING_KEY_B64", "")
    if not key:
        raise SystemExit("ARTWORK_SIGNING_KEY_B64 is required")
    print(json.dumps(build(
        master_path=args.master, preview_path=args.preview,
        product_path=args.product, assets_path=args.assets,
        output_dir=args.output_dir, signing_key_b64=key,
        preview_url=args.preview_url,
        generation=(json.loads(args.generation_metadata.read_text(encoding="utf-8"))
                    if args.generation_metadata else None),
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
