#!/usr/bin/env python3
"""Independently verify a wallet-signed MOSUL association record."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sale-service"))
from token_association import verify_record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path, help="JSON record exported by token-association.html")
    args = parser.parse_args()
    try:
        record = json.loads(args.record.read_text(encoding="utf-8"))
        verify_record(record)
    except (OSError, json.JSONDecodeError, ValueError, PermissionError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VERIFIED: wallet signature authenticates the exact project/token association statement.")
    print("Scope: statement and signing-wallet control only; this does not prove mint authority or token economics.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
