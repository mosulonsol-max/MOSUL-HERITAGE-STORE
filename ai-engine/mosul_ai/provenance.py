"""Canonical Ed25519 signatures for public artwork records."""
from __future__ import annotations

import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


def canonical_bytes(record: dict) -> bytes:
    unsigned = {key: value for key, value in record.items() if key != "provenance_signature"}
    return json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_record(record: dict, private_key_b64: str) -> dict:
    raw = base64.b64decode(private_key_b64, validate=True)
    if len(raw) != 32:
        raise ValueError("Ed25519 private key must be a base64-encoded 32-byte seed")
    key = Ed25519PrivateKey.from_private_bytes(raw)
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    signature = key.sign(canonical_bytes(record))
    return {
        "algorithm": "Ed25519",
        "public_key_b64": base64.b64encode(public).decode("ascii"),
        "signature_b64": base64.b64encode(signature).decode("ascii"),
        "scope": "Canonical JSON record excluding provenance_signature",
    }


def verify_record(record: dict) -> bool:
    envelope = record.get("provenance_signature")
    if not isinstance(envelope, dict) or envelope.get("algorithm") != "Ed25519":
        return False
    try:
        public = Ed25519PublicKey.from_public_bytes(base64.b64decode(envelope["public_key_b64"], validate=True))
        public.verify(base64.b64decode(envelope["signature_b64"], validate=True), canonical_bytes(record))
        return True
    except (KeyError, TypeError, ValueError, InvalidSignature):
        return False
