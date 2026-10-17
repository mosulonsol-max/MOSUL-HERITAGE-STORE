"""Build and independently verify the project's MOSUL association statement."""
from __future__ import annotations

import base64
import datetime as dt
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core import b58decode

PROJECT = "MOSUL HERITAGE STORE"
TOKEN_NAME = "MOSUL"
NETWORK = "solana-mainnet-beta"
TOKEN_MINT = "6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump"
RECEIVING_WALLET = "EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu"
STATEMENT_VERSION = "2026-10-17-v1"


def association_message(signed_at: str, *, token_mint: str = TOKEN_MINT,
                        receiving_wallet: str = RECEIVING_WALLET) -> str:
    try:
        parsed = dt.datetime.fromisoformat(signed_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ValueError("signed_at must be an ISO-8601 timestamp") from None
    if parsed.tzinfo is None:
        raise ValueError("signed_at must include a timezone")
    return (
        "MOSUL HERITAGE TOKEN ASSOCIATION\n"
        f"Project: {PROJECT}\n"
        f"Token name: {TOKEN_NAME}\n"
        f"Network: {NETWORK}\n"
        f"Token mint: {token_mint}\n"
        f"Project receiving wallet: {receiving_wallet}\n"
        f"Statement version: {STATEMENT_VERSION}\n"
        f"Signed at: {signed_at}\n"
        "Declaration: I, Ahmed Nabeel, state that the token mint listed above is associated with the MOSUL HERITAGE STORE project and may be identified by the project as its associated token. This signature proves control of the wallet that signed this statement and records my stated association only; it does not prove control of the token mint or guarantee price, returns, or endorsement by Solana or pump.fun."
    )


def verify_record(record: dict, *, expected_mint: str = TOKEN_MINT,
                  expected_wallet: str = RECEIVING_WALLET) -> str:
    expected = {
        "project": PROJECT, "token_name": TOKEN_NAME, "network": NETWORK,
        "token_mint": expected_mint, "project_receiving_wallet": expected_wallet,
        "statement_version": STATEMENT_VERSION,
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("association record fields do not match the expected project statement")
    message = association_message(record.get("signed_at", ""), token_mint=expected_mint,
                                  receiving_wallet=expected_wallet)
    if record.get("message") != message:
        raise ValueError("signed message differs from the exact association statement")
    try:
        signature = base64.b64decode(record.get("signature_base64", ""), validate=True)
        public_key = b58decode(expected_wallet)
        if len(public_key) != 32 or len(signature) != 64:
            raise ValueError("wrong key/signature length")
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message.encode("utf-8"))
    except (ValueError, InvalidSignature):
        raise PermissionError("token association wallet signature did not verify") from None
    return message
