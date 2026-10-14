# Automatic Telegram updates

The Telegram workflow sends an exact, newly approved item from `social/updates.json` to the configured group. For other project changes, it sends a concise status based on the merged pull request title and links to that pull request.

## Set up the group bot

1. Create a bot with Telegram's `@BotFather` and keep its token private.
2. Add the bot to the intended MOSUL HERITAGE group and grant only the permission to send messages. This publisher does not read group messages, so it does not need group-read access.
3. In the repository, open **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`: the token from BotFather.
   - `TELEGRAM_CHAT_ID`: `@mosulcoin` if that public group username is active; otherwise the group's numeric chat ID.

Never put the bot token in a commit, issue, pull request, screenshot, or chat message. The workflow skips publishing when either secret is missing.

## Publishing behavior

- Queue updates publish on `main` only when one newly added item is marked `approved`.
- A merged project PR without a new approved queue item publishes its factual PR title and a direct link.
- Unmerged PRs and queue-only edits without an approved item do not publish.
- Telegram queue posts are sent once by the push workflow; merged-PR handling skips the same approved item to prevent duplicates.
- The Telegram publisher and X publisher are separate workflows. Each sends only to its configured destination.
- A failed or ambiguous request is not retried automatically.

## Questions from group members

This workflow only broadcasts approved updates; it does not read or answer questions. A question-answering bot needs a separate always-on Telegram webhook service and an approved FAQ source. Unknown or financial questions should be routed to a human administrator rather than answered as fact.
