#!/usr/bin/env python3
"""Queue one verified, positive project achievement for X and Telegram."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from .x_text import weighted_length
except ImportError:  # Direct execution: python scripts/queue_daily_update.py
    from x_text import weighted_length

QUEUE_LIMIT = 400
SITE = "https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/"
NEGATIVE_OPERATION_TERMS = (
    "blocked", "cannot", "depleted", "disabled", "error", "failed",
    "failure", "issue", "missing", "problem", "unavailable",
)
ACHIEVEMENT_TERMS = ("automated", "completed", "includes", "now", "tested", "verified")

POSTS = {
    "morning": (
        "MOSUL HERITAGE now has a tested governance engine, deterministic policy gates, "
        "and signed provenance. Automated tests protect generation, publishing, and Devnet payment flows. "
        f"{SITE} #MOSUL #BuildInPublic"
    ),
    "afternoon": (
        "MOSUL HERITAGE now automates three daily project-update slots through protected GitHub pull requests. "
        "Every update remains traceable in the public development history. "
        f"{SITE} #MOSUL #OpenSource"
    ),
    "evening": (
        "MOSUL HERITAGE artwork previews now include a unique ID, SHA-256 digest, watermark, "
        "source notes, and optional Ed25519 signature for verifiable provenance. "
        f"{SITE} #MOSUL #Provenance"
    ),
}


def validate_achievement_update(text: str) -> None:
    """Reject operational problem reports and generic non-achievement updates."""
    lowered = text.casefold()
    if any(term in lowered for term in NEGATIVE_OPERATION_TERMS):
        raise ValueError("daily social posts must contain positive achievements only")
    if not any(term in lowered for term in ACHIEVEMENT_TERMS):
        raise ValueError("daily social post must state a concrete achievement")
    if weighted_length(text) > 280:
        raise ValueError("daily post exceeds X's 280 weighted-character limit")


def choose_slot(now: dt.datetime) -> str:
    hour = now.astimezone(ZoneInfo("Asia/Baghdad")).hour
    if hour < 12:
        return "morning"
    if hour < 18:
        return "afternoon"
    return "evening"


def queue_update(path: Path, slot: str, now: dt.datetime) -> bool:
    if slot not in POSTS:
        raise ValueError("slot must be morning, afternoon, or evening")
    local_date = now.astimezone(ZoneInfo("Asia/Baghdad")).date().isoformat()
    update_id = f"daily-{local_date}-{slot}"
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"updates": []}
    updates = payload.get("updates")
    if not isinstance(updates, list):
        raise ValueError("social queue must contain an updates list")
    if any(item.get("id") == update_id for item in updates if isinstance(item, dict)):
        return False
    text = POSTS[slot]
    validate_achievement_update(text)
    updates.append({"id": update_id, "status": "approved", "text": text})
    payload["updates"] = updates[-QUEUE_LIMIT:]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="social/updates.json")
    parser.add_argument("--slot", choices=sorted(POSTS))
    args = parser.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    slot = args.slot or choose_slot(now)
    changed = queue_update(Path(args.queue), slot, now)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"queued={'true' if changed else 'false'}\n")
    print(f"{'Queued' if changed else 'Already queued'} {slot} update.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
