#!/usr/bin/env python3
"""Publish one newly added, approved MOSUL HERITAGE update to a Telegram group."""
import json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request
QUEUE = "social/updates.json"
UPDATE_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,80}")
def read_at(ref):
    if not ref or set(ref) == {"0"}: return {"updates": []}
    result = subprocess.run(["git", "show", f"{ref}:{QUEUE}"], capture_output=True, text=True, check=False)
    if result.returncode: return {"updates": []}
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
    if len(approved) != 1: raise ValueError("Add exactly one approved update per commit.")
    update = approved[0]
    update_id, text = update.get("id"), update.get("text")
    if not isinstance(update_id, str) or not UPDATE_ID_RE.fullmatch(update_id):
        raise ValueError("Update id must be 1-80 letters, digits, dots, underscores, or hyphens.")
    if not isinstance(text, str) or not text.strip() or text != text.strip():
        raise ValueError("Approved update must have non-empty text without outer whitespace.")
    if len(text) > 4096: raise ValueError("Telegram message exceeds the 4096-character limit.")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id: raise RuntimeError("Configure Telegram Actions secrets.")
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
    if payload.get("ok") is not True: raise RuntimeError("Telegram API rejected the message; it was not retried.")
    message_id = payload.get("result", {}).get("message_id")
    if not isinstance(message_id, int): raise RuntimeError("Telegram returned no message id; do not retry automatically.")
    print(f"Published update {update_id} to Telegram (message id {message_id}).")
    return 0
if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"Telegram publishing failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

