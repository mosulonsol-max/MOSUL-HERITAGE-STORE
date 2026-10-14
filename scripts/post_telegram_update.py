#!/usr/bin/env python3
"""Publish an approved queue item or factual merged-PR status to Telegram."""
import json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request

QUEUE = "social/updates.json"
UPDATE_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,80}")
PR_URL_RE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+")


def read_at(ref):
    if not ref or set(ref) == {"0"}:
        return {"updates": []}
    result = subprocess.run(["git", "show", f"{ref}:{QUEUE}"], capture_output=True, text=True, check=False)
    if result.returncode:
        return {"updates": []}
    return json.loads(result.stdout)


def merged_pr_update(before_ref, after_ref):
    # Push events handle the queue; this fallback is only for merged PR events.
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return None
    changed = subprocess.run(
        ["git", "diff", "--name-only", before_ref, after_ref],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    project_files = [path for path in changed if path != QUEUE]
    if not project_files:
        print("Queue-only change has no approved update; nothing to publish.")
        return None
    title = os.environ.get("GITHUB_PR_TITLE", "").strip()
    url = os.environ.get("GITHUB_PR_URL", "").strip()
    if not title or not PR_URL_RE.fullmatch(url):
        raise RuntimeError("Merged PR title or canonical GitHub PR URL is missing.")
    title = title.encode("ascii", "ignore").decode("ascii")
    title = re.sub(r"[^A-Za-z0-9 .,!?():_/-]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        raise RuntimeError("Merged PR title has no publishable ASCII text.")
    text = f"MOSUL HERITAGE update: {title}. Merged: {url}"
    if len(text) > 4096:
        suffix = f". Merged: {url}"
        title = title[:4096 - len("MOSUL HERITAGE update: ") - len(suffix)].rstrip(" .,!?")
        text = f"MOSUL HERITAGE update: {title}{suffix}"
    return "merged-pr", text


def main():
    before_ref = os.environ.get("GITHUB_EVENT_BEFORE", "")
    after_ref = os.environ.get("GITHUB_EVENT_AFTER", "")
    before = read_at(before_ref)
    after = read_at(after_ref)
    old_ids = {item.get("id") for item in before.get("updates", [])}
    added = [item for item in after.get("updates", []) if item.get("id") not in old_ids]
    approved = [item for item in added if item.get("status") == "approved"]

    # A merge with an approved queue entry is sent by the push-triggered workflow.
    # Skip here to avoid sending it twice.
    if os.environ.get("GITHUB_EVENT_NAME") == "pull_request" and approved:
        print("Approved queue item will be sent by the push workflow; skipping duplicate.")
        return 0
    if len(approved) > 1:
        raise ValueError("Add exactly one approved update per commit.")
    if approved:
        item = approved[0]
        update_id, text = item.get("id"), item.get("text")
        if not isinstance(update_id, str) or not UPDATE_ID_RE.fullmatch(update_id):
            raise ValueError("Invalid update id.")
        if not isinstance(text, str) or not text.strip() or text != text.strip():
            raise ValueError("Approved update must have non-empty text without outer whitespace.")
        if len(text) > 4096:
            raise ValueError("Telegram message exceeds the 4096-character limit.")
        label = update_id
    else:
        fallback = merged_pr_update(before_ref, after_ref)
        if fallback is None:
            print("No eligible project update; nothing to publish.")
            return 0
        label, text = fallback

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise RuntimeError("Configure Telegram Actions secrets.")
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    request = urllib.request.Request(endpoint, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Telegram API returned HTTP {exc.code}; message was not retried.") from None
    except urllib.error.URLError:
        raise RuntimeError("Could not reach Telegram API; message was not retried.") from None
    if payload.get("ok") is not True:
        raise RuntimeError("Telegram API rejected the message; it was not retried.")
    message_id = payload.get("result", {}).get("message_id")
    if not isinstance(message_id, int):
        raise RuntimeError("Telegram returned no message id; do not retry automatically.")
    print(f"Published update {label} to Telegram (message id {message_id}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Telegram publishing failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
