#!/usr/bin/env python3
"""Publish one approved queued update or factual merged-PR status to X."""

import json
import os
import re
import subprocess
import sys

import requests
from requests_oauthlib import OAuth1

try:
    from .x_text import accepted_post_id, weighted_length
except ImportError:  # Direct execution: python scripts/post_x_update.py
    from x_text import accepted_post_id, weighted_length

QUEUE = "social/updates.json"
POST_URL = "https://api.x.com/2/tweets"


def read_at(ref):
    if not ref or set(ref) == {"0"}:
        return {"updates": []}
    result = subprocess.run(["git", "show", f"{ref}:{QUEUE}"], capture_output=True, text=True)
    if result.returncode:
        return {"updates": []}
    return json.loads(result.stdout)


def merged_pr_update(before_ref, after_ref):
    """Summarize the public PR title for a merged project change."""
    changed = subprocess.run(
        ["git", "diff", "--name-only", before_ref, after_ref],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    project_files = [path for path in changed if path != QUEUE]
    if not project_files:
        print("No newly approved queue item or project-file change; nothing to publish.")
        return None

    title = os.environ.get("GITHUB_PR_TITLE", "").strip()
    url = os.environ.get("GITHUB_PR_URL", "").strip()
    if not title or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+", url):
        raise RuntimeError("Merged PR title or canonical GitHub PR URL is missing.")
    # Keep the public project update in English and prevent control chars or
    # unusual markup from entering the post. PR titles are owner-approved at merge.
    title = title.encode("ascii", "ignore").decode("ascii")
    title = re.sub(r"[^A-Za-z0-9 .,!?():_/-]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        raise RuntimeError("Merged PR title has no publishable ASCII text.")
    prefix = "MOSUL HERITAGE update: "
    suffix = f". Merged: {url}"
    available = 280 - weighted_length(prefix + suffix)
    title = title[:available].rstrip(" .,!?")
    text = prefix + title + suffix
    count = weighted_length(text)
    if count > 280:
        raise ValueError(f"Merged update is {count} weighted characters; maximum is 280.")
    return "merged-pr", text


def main():
    before_ref = os.environ.get("GITHUB_EVENT_BEFORE", "")
    after_ref = os.environ.get("GITHUB_EVENT_AFTER", "")
    before = read_at(before_ref)
    after = read_at(after_ref)
    old_ids = {item.get("id") for item in before.get("updates", [])}
    added = [item for item in after.get("updates", []) if item.get("id") not in old_ids]
    approved = [item for item in added if item.get("status") == "approved"]

    if len(approved) > 1:
        raise ValueError("Add exactly one approved update per commit.")
    if approved:
        update = approved[0]
        update_id, text = update.get("id"), update.get("text")
        if not isinstance(update_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", update_id):
            raise ValueError("Update id must be 1-80 letters, digits, dots, underscores, or hyphens.")
        if not isinstance(text, str) or not text.strip() or text != text.strip():
            raise ValueError("Approved update must have non-empty text without outer whitespace.")
        count = weighted_length(text)
        if count > 280:
            raise ValueError(f"Update is {count} weighted characters; maximum is 280.")
        post_label = update_id
    else:
        fallback = merged_pr_update(before_ref, after_ref)
        if fallback is None:
            return 0
        post_label, text = fallback
        count = weighted_length(text)

    names = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    credentials = {name: os.environ.get(name, "") for name in names}
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        raise RuntimeError("Add GitHub Actions secrets: " + ", ".join(missing))
    auth = OAuth1(credentials["X_API_KEY"], credentials["X_API_SECRET"],
                  credentials["X_ACCESS_TOKEN"], credentials["X_ACCESS_TOKEN_SECRET"])
    response = requests.post(POST_URL, json={"text": text}, auth=auth,
                             headers={"Content-Type": "application/json"}, timeout=30)
    try:
        payload = response.json()
    except ValueError:
        payload = None
    post_id = accepted_post_id(response.status_code, payload, response.text)
    if post_id is None:
        print("X publication deferred: the configured X API account has no credits. "
              "No retry was attempted and this is not a code failure.")
        return 0
    print(f"Published update {post_label} to X (post id {post_id}; {count}/280 characters).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"X publishing failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
