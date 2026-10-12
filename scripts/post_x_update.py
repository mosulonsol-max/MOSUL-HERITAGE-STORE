#!/usr/bin/env python3
"""Publish one new, approved MOSUL HERITAGE update to X."""

import json
import os
import re
import subprocess
import sys

import requests
from requests_oauthlib import OAuth1

try:
    from .x_text import weighted_length
except ImportError:  # Direct execution: python scripts/post_x_update.py
    from x_text import weighted_length

QUEUE = "social/updates.json"
POST_URL = "https://api.x.com/2/tweets"

def read_at(ref):
    if not ref or set(ref) == {"0"}:
        return {"updates": []}
    result = subprocess.run(["git", "show", f"{ref}:{QUEUE}"], capture_output=True, text=True)
    if result.returncode:
        return {"updates": []}
    return json.loads(result.stdout)

def main():
    before = read_at(os.environ.get("GITHUB_EVENT_BEFORE", ""))
    after = read_at(os.environ.get("GITHUB_EVENT_AFTER", ""))
    old_ids = {item.get("id") for item in before.get("updates", [])}
    added = [item for item in after.get("updates", []) if item.get("id") not in old_ids]
    approved = [item for item in added if item.get("status") == "approved"]
    if not approved:
        print("No newly approved update; nothing to publish.")
        return 0
    if len(approved) != 1:
        raise ValueError("Add exactly one approved update per commit.")
    update = approved[0]
    update_id, text = update.get("id"), update.get("text")
    if not isinstance(update_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", update_id):
        raise ValueError("Update id must be 1-80 letters, digits, dots, underscores, or hyphens.")
    if not isinstance(text, str) or not text.strip() or text != text.strip():
        raise ValueError("Approved update must have non-empty text without outer whitespace.")
    count = weighted_length(text)
    if count > 280:
        raise ValueError(f"Update is {count} weighted characters; maximum is 280.")
    names = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    credentials = {name: os.environ.get(name, "") for name in names}
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        raise RuntimeError("Add GitHub Actions secrets: " + ", ".join(missing))
    auth = OAuth1(credentials["X_API_KEY"], credentials["X_API_SECRET"],
                  credentials["X_ACCESS_TOKEN"], credentials["X_ACCESS_TOKEN_SECRET"])
    response = requests.post(POST_URL, json={"text": text}, auth=auth,
                             headers={"Content-Type": "application/json"}, timeout=30)
    if response.status_code != 201:
        raise RuntimeError(f"X API returned HTTP {response.status_code}: {response.text[:500]}")
    post_id = response.json().get("data", {}).get("id")
    if not post_id:
        raise RuntimeError("X accepted request but returned no post id; do not retry automatically.")
    print(f"Published update {update_id} to X (post id {post_id}; {count}/280 characters).")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"X publishing failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
