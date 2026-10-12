# Automatic Telegram updates

The Telegram workflow publishes the exact text of one newly added `approved` entry in `social/updates.json` to the configured group. It runs only when that file changes on `main`; it does not generate claims from commits or retry ambiguous sends.

## Set up the group bot

1. Create a bot with Telegram's `@BotFather` and keep its token private.
2. Add the bot to the intended MOSUL HERITAGE group and grant only the permission to send messages. This publisher does not read group messages, so it does not need group-read access.
3. In the repository, open **Settings → Secrets and variables → Actions** and add:
   - `TELEGRAM_BOT_TOKEN`: the token from BotFather.
   - `TELEGRAM_CHAT_ID`: `@mosulcoin` if that public group username is active; otherwise the group's numeric chat ID.

Never put the bot token in a commit, issue, pull request, screenshot, or chat message. The workflow skips publishing when either secret is missing.

## Publishing behavior

- Add exactly one new update with `status: approved` to `social/updates.json` on `main`.
- The Telegram publisher and X publisher are separate workflows. Each sends the approved text only to its own configured destination.
- An empty queue or a commit without a newly approved item sends nothing.
- The current queue is empty. Do not add a dummy item just to test against the public group.

## Questions from group members

This workflow only broadcasts approved updates; it does not read or answer questions. A question-answering bot needs a separate always-on Telegram webhook service and an approved FAQ source. Unknown or financial questions should be routed to a human administrator rather than answered as fact.
