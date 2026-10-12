"""Capability registry validation and status reporting."""
from __future__ import annotations

import json
from pathlib import Path

VALID_STATUS = {"implemented", "partial", "blocked", "disabled"}


def load_registry(path: str | Path) -> dict:
    registry = json.loads(Path(path).read_text(encoding="utf-8"))
    items = registry.get("capabilities")
    if not isinstance(items, list) or not items:
        raise ValueError("Capability registry must contain a non-empty capabilities list")
    names = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("Each capability needs a name")
        if item.get("status") not in VALID_STATUS:
            raise ValueError("Invalid capability status")
        if item["name"] in names:
            raise ValueError("Duplicate capability name")
        names.add(item["name"])
    return registry


def implemented_actions(registry: dict) -> list[str]:
    return sorted(item["name"] for item in registry["capabilities"] if item["status"] == "implemented")
