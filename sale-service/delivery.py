"""Authenticated decryption for the private auction delivery artifact.

The repository stores only AES-GCM ciphertext. The verified ZIP stays in process
memory and is served only after the payment and one-time download checks pass.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

MAGIC = b"MOSUL-AESGCM-V1\0"
MAX_ENCRYPTED_BYTES = 150_000_000
MAX_PACKAGE_BYTES = 140_000_000


def _delivery_key(signing_seed_b64: str) -> bytes:
    try:
        seed = base64.b64decode(signing_seed_b64, validate=True)
    except (ValueError, TypeError):
        raise ValueError("ARTWORK_SIGNING_KEY_B64 is not valid base64") from None
    if len(seed) != 32:
        raise ValueError("ARTWORK_SIGNING_KEY_B64 must contain a 32-byte seed")
    return HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=b"MOSUL HERITAGE private delivery package encryption v1",
    ).derive(seed)


def load_private_package(path: str | Path, *, signing_seed_b64: str,
                         expected_encrypted_sha256: str,
                         expected_package_sha256: str, product_id: str) -> bytes:
    """Verify both pinned digests and authenticate/decrypt the AES-GCM artifact."""
    artifact_path = Path(path)
    if artifact_path.stat().st_size > MAX_ENCRYPTED_BYTES:
        raise ValueError("encrypted delivery artifact exceeds the allowed size")
    encrypted = artifact_path.read_bytes()
    actual_encrypted = hashlib.sha256(encrypted).hexdigest()
    if not expected_encrypted_sha256 or not hmac.compare_digest(
            actual_encrypted, expected_encrypted_sha256):
        raise ValueError("encrypted artifact SHA-256 does not match the asset manifest")
    if not encrypted.startswith(MAGIC) or len(encrypted) < len(MAGIC) + 12 + 16:
        raise ValueError("encrypted artifact has an unsupported format")
    nonce_start = len(MAGIC)
    nonce = encrypted[nonce_start:nonce_start + 12]
    ciphertext = encrypted[nonce_start + 12:]
    try:
        package = AESGCM(_delivery_key(signing_seed_b64)).decrypt(
            nonce, ciphertext, product_id.encode("utf-8"))
    except (InvalidTag, ValueError):
        # Do not expose details from an authentication failure.
        raise ValueError("encrypted delivery artifact authentication failed") from None
    if len(package) > MAX_PACKAGE_BYTES:
        raise ValueError("decrypted delivery package exceeds the allowed size")
    actual_package = hashlib.sha256(package).hexdigest()
    if not expected_package_sha256 or not hmac.compare_digest(
            actual_package, expected_package_sha256):
        raise ValueError("decrypted package SHA-256 does not match the asset manifest")
    return package
