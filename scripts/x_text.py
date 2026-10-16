"""Dependency-free X text validation shared by queueing and publishing."""

import re
import unicodedata

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
TRAILING = ".,!?;:)]}"


def accepted_post_id(status_code: int, payload: object, response_text: str = ""):
    """Return a post id, or None only for X's explicit credits-depleted response."""
    if status_code == 201:
        post_id = payload.get("data", {}).get("id") if isinstance(payload, dict) else None
        if not post_id:
            raise RuntimeError("X accepted request but returned no post id; do not retry automatically.")
        return post_id
    if status_code == 402 and isinstance(payload, dict) and payload.get("detail") == "credits depleted":
        return None
    raise RuntimeError(f"X API returned HTTP {status_code}: {response_text[:500]}")


def weighted_length(text: str) -> int:
    """Return X's relevant weighted length for ASCII text (URLs count as 23)."""
    text = unicodedata.normalize("NFC", text)
    if any(ord(char) > 127 for char in text):
        raise ValueError("X update must use ASCII English text only.")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
        raise ValueError("Unsupported control character in update.")
    total = 0
    cursor = 0
    for match in URL_RE.finditer(text):
        trimmed = match.group(0).rstrip(TRAILING)
        if not trimmed:
            continue
        end = match.start() + len(trimmed)
        total += match.start() - cursor + 23
        cursor = end
    return total + len(text) - cursor
