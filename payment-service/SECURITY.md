# Devnet payment security review

Scope: the service is restricted in code to `https://api.devnet.solana.com`. It accepts exact native-SOL devnet transfers only; it does not support mainnet, MOSUL token payments, custody, fiat conversion, or real-value settlement.

Controls implemented:

- Exact merchant, buyer (when supplied), lamport amount, unique memo, intent expiry, and finalized transaction checks.
- Unique idempotency keys, transaction signatures, memos, and sale records enforced by SQLite.
- Random refund capability stored only as a SHA-256 digest; completed-sale data is removed when a refund is requested.
- Refunds use a fixed `solana transfer --url devnet` argument list without a shell and are idempotent in the database.
- The price feed contains only first-party, finalized, non-refunded records and exposes no buyer address.
- Secrets and keypair files are environment/deployment inputs and must never be committed.

Open production blockers:

- Independent review, reverse-proxy TLS, authentication/rate limits, backups, monitoring, multi-process database strategy, delivery state machine, dispute handling, accounting, and legal terms.
- A Token-2022 devnet mint plus audited token-transfer and refund instructions are required before testing MOSUL-token payments.
- The current native-SOL Devnet adapter is a technical rehearsal, not a production payment system.
- Automatic refunds require enough Devnet SOL and a dedicated low-privilege test keypair.
