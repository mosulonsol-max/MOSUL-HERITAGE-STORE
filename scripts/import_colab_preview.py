#!/usr/bin/env python3
"""Safely import one Colab preview bundle into the persistent artwork data branch."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys, tempfile, zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-engine"))
from mosul_ai.provenance import sign_record

def safe_extract(bundle: Path, dest: Path) -> None:
    with zipfile.ZipFile(bundle) as zf:
        names = zf.namelist()
        if len(names) > 12:
            raise ValueError("Bundle has an unexpected number of files")
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or not name or "\\" in name:
                raise ValueError("Unsafe path in bundle")
            if name.endswith("/"):
                continue
            if not (name in {"catalog.json", "ai-audit.jsonl", "session-manifest.json"} or (len(p.parts) == 2 and p.parts[0] == "generated" and p.suffix.lower() == ".png")):
                raise ValueError("Unexpected file in bundle: " + name)
        zf.extractall(dest)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    bundle_arg = args.bundle
    if not re.fullmatch(r"sessions/[A-Za-z0-9._-]+\\.zip", bundle_arg):
        raise ValueError("Bundle must be a ZIP under sessions/ with a simple filename")
    data = Path(args.data_dir).resolve()
    bundle = (data / bundle_arg).resolve()
    if data not in bundle.parents or not bundle.is_file():
        raise ValueError("Session bundle does not exist in the artwork data checkout")
    with tempfile.TemporaryDirectory(prefix="mosul-colab-import-") as temp:
        tmp = Path(temp)
        safe_extract(bundle, tmp)
        catalog = json.loads((tmp / "catalog.json").read_text(encoding="utf-8"))
        manifest = json.loads((tmp / "session-manifest.json").read_text(encoding="utf-8"))
        items = catalog.get("items") if isinstance(catalog, dict) else None
        if not manifest.get("preview_only") or manifest.get("sale") != "disabled" or manifest.get("nft") != "not_minted":
            raise ValueError("Bundle is not explicitly marked preview-only")
        if not isinstance(items, list) or len(items) != 1:
            raise ValueError("Bundle must contain exactly one item")
        record = items[0]
        if record.get("status") != "PUBLIC PREVIEW — NOT FOR SALE" or record.get("mint_status") != "Not minted":
            raise ValueError("Item does not meet preview-only gates")
        rel = PurePosixPath(str(record.get("image", "")))
        if len(rel.parts) != 2 or rel.parts[0] != "generated" or rel.suffix.lower() != ".png":
            raise ValueError("Item image path is invalid")
        source_image = tmp.joinpath(*rel.parts)
        if not source_image.is_file() or source_image.stat().st_size > 20_000_000:
            raise ValueError("Image is missing or exceeds the 20 MB limit")
        image_hash = hashlib.sha256(source_image.read_bytes()).hexdigest()
        if image_hash != record.get("sha256") or image_hash != manifest.get("image_sha256"):
            raise ValueError("Image SHA-256 verification failed")
        if record.get("id") != manifest.get("item_id"):
            raise ValueError("Item identifier does not match manifest")
        try:
            from PIL import Image
            with Image.open(source_image) as image:
                image.verify()
            with Image.open(source_image) as image:
                if image.format != "PNG" or min(image.size) < 512 or max(image.size) > 8192:
                    raise ValueError("Image dimensions or format are not accepted")
        except ImportError as exc:
            raise RuntimeError("Pillow must be installed by the workflow") from exc
        signing_key = os.environ.get("ARTWORK_SIGNING_KEY_B64", "").strip()
        if signing_key:
            record["provenance_signature"] = sign_record(record, signing_key)
            record["watermark_status"] = "Signed public preview record; not a sale or legal authorship claim."
        else:
            record.pop("provenance_signature", None)
            record["provenance_signature_status"] = "not_configured"
            record["watermark_status"] = "Preview watermark present; signed provenance is not configured."
        generated = data / "generated"
        generated.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_image, generated / source_image.name)
        catalog_path = data / "catalog.json"
        try:
            existing = json.loads(catalog_path.read_text(encoding="utf-8"))
            old_items = existing.get("items", [])
            if not isinstance(old_items, list):
                old_items = []
        except (FileNotFoundError, json.JSONDecodeError):
            old_items = []
        old_items = [item for item in old_items if item.get("id") != record["id"]]
        catalog_path.write_text(json.dumps({"items": [record] + old_items[:119]}, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        audit_src = tmp / "ai-audit.jsonl"
        if audit_src.is_file():
            with (data / "ai-audit.jsonl").open("a", encoding="utf-8") as dst:
                dst.write(audit_src.read_text(encoding="utf-8"))
        bundle.unlink()
        print("Imported and verified preview " + record["id"] + "; sale and mint remain disabled.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Colab preview import stopped safely: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
