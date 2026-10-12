# Self-hosted auction bid ledger

Single-host Python and SQLite prototype for a persistent signed-bid log. The included example lot is disabled. This service does not charge, escrow, settle, refund, or deliver products.

Install with `python -m pip install -r requirements.txt`; copy `auction.example.json` to ignored `auction.json`, configure an owner-approved lot, then run `AUCTION_CONFIG=auction.json AUCTION_DB=data/auction.sqlite3 python server.py`. It binds to localhost by default.

Wallets sign the short-lived UTF-8 challenge; the API verifies the Ed25519 signature, minimum increment, challenge replay, and auction clock. Late bids in the final two minutes extend the close by two minutes.

Host on one owner-managed machine with a persistent disk behind HTTPS. The GitHub Pages site is not connected yet. Set `AUCTION_PAUSED=1` and restart to pause bids. Public launch still needs reverse-proxy abuse controls, recovery/backup procedures, buyer terms, UI integration, and independent security review. Settlement and delivery stay disabled.
