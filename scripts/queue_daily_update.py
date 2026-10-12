#!/usr/bin/env python3
"""Queue one factual, non-promotional project update for X and Telegram."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

QUEUE_LIMIT = 400
SITE = "https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/"

POSTS = {
    "morning": (
        "MOSUL HERITAGE build log: the public repository records code, verification notes, "
        "and release gates. The project remains preview-only while payment and minting stay disabled. "
        f"{SITE} #MOSUL #BuildInPublic"
    ),
    "afternoon": (
        "Inside MOSUL HERITAGE: the governed AI pipeline can plan and generate heritage-inspired "
        "art previews, while deterministic policy checks block unknown, mainnet, and real-value actions. "
        f"{SITE} #MOSUL #DigitalArt"
    ),
    "evening": (
        "Every MOSUL HERITAGE preview is designed for traceability: unique ID, SHA-256, visible watermark, "
        "source notes, and optional Ed25519 provenance. A signature supports verification; it is not proof of a sale. "
        f"{SITE} #MOSUL #Provenance"
    ),
}


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
    if not text.isascii() or len(text) > 280:
        raise ValueError("daily post must be ASCII and at most 280 characters")
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
