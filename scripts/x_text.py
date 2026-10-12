"""Dependency-free X text validation shared by queueing and publishing."""

import re
import unicodedata

URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
TRAILING = ".,!?;:)]}"


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
