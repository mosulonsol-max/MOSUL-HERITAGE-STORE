"""Evidence ledger helpers for source-backed heritage claims."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def make_fact(claim: str, source_url: str, source_text: str, retrieved_at: str | None = None) -> dict:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Fact sources must use an absolute HTTPS URL")
    if not claim.strip() or not source_text.strip():
        raise ValueError("Claim and source text are required")
    when = retrieved_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "claim": claim.strip(),
        "source_url": source_url,
        "retrieved_at": when,
        "source_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        "status": "source_recorded_not_independently_verified",
    }


def append_fact(path: str | Path, fact: dict) -> None:
    required = {"claim", "source_url", "retrieved_at", "source_sha256", "status"}
    if not required.issubset(fact):
        raise ValueError("Fact record is incomplete")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(fact, ensure_ascii=False, sort_keys=True) + "\n")
