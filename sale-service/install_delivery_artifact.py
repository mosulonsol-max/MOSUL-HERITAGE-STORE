"""Fetch the encrypted delivery artifact onto Render's persistent disk.

This runs once after the first successful deploy. It never downloads or writes a
plaintext Collector Master or ZIP.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
ARTIFACT_URL = (
    "https://raw.githubusercontent.com/mosulonsol-max/"
    "MOSUL-HERITAGE-STORE/auction-data/auction-product/"
    "MOSUL-GENESIS-000001-package.zip.aes"
)
MAX_ARTIFACT_BYTES = 150_000_000


def install_artifact(*, url: str = ARTIFACT_URL,
                     destination: str | Path | None = None,
                     manifest_path: str | Path | None = None) -> Path:
    target = Path(destination or os.environ.get(
        "DELIVERY_ENCRYPTED_PACKAGE_PATH",
        "/app/data/private/MOSUL-GENESIS-000001-package.zip.aes"))
    manifest = Path(manifest_path or os.environ.get(
        "SALE_ASSET_MANIFEST",
        ROOT / "products" / "MOSUL-GENESIS-000001.assets.json"))
    assets = json.loads(manifest.read_text(encoding="utf-8"))
    expected = str(assets.get("delivery_package", {}).get(
        "encrypted_artifact_sha256", ""))
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("asset manifest has no valid encrypted artifact SHA-256")
    if not url.startswith("https://"):
        raise ValueError("encrypted artifact URL must use HTTPS")

    request = Request(url, headers={"User-Agent": "MOSUL-HERITAGE-delivery-bootstrap/1"})
    with urlopen(request, timeout=60) as response:
        payload = response.read(MAX_ARTIFACT_BYTES + 1)
    if not payload or len(payload) > MAX_ARTIFACT_BYTES:
        raise ValueError("downloaded encrypted artifact is empty or too large")
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise ValueError("downloaded encrypted artifact does not match the pinned manifest")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".delivery-", suffix=".tmp",
                dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return target


if __name__ == "__main__":
    path = install_artifact()
    print(f"verified encrypted delivery artifact installed: {path.name}")
