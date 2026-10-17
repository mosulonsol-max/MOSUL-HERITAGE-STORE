# Devnet payment security review

Scope: the service is restricted in code to `https://api.devnet.solana.com`. It supports native-SOL Devnet transfers and verifies Token-2022 transfers only against an explicitly configured Devnet mint. It does not support Mainnet, the project's Mainnet MOSUL mint, custody of buyer funds, fiat conversion, or real-value settlement.

Controls implemented:

- Exact merchant, buyer (when supplied), amount, unique memo, intent time window, and finalized transaction checks. Native SOL requires the payer to be a transaction signer.
- For configured test tokens: exact Token-2022 `transferChecked`, configured mint, buyer token-account debit, merchant token-account credit, decimals, finalized mint account ownership/initialization, and intent memo are checked. Transfer-fee effects that change the exact credit are rejected.
- Unique idempotency keys, transaction signatures, memos, and sale records enforced by SQLite.
- Random refund capability stored only as a SHA-256 digest. A pending refund is excluded from benchmark output; the sale record is retained unless an exact refund is confirmed.
- Native-SOL refunds use a fixed `solana transfer --url devnet` argument list without a shell. A worker claims an intent before sending and marks it refunded only after a finalized exact amount, recipient, and refund memo check. An unverified send is held for manual reconciliation to avoid an automatic duplicate payment.
- The price feed contains only first-party, finalized, non-refunded records and exposes no buyer address.
- Secrets and keypair files are environment/deployment inputs and must never be committed.

Open production blockers:

- Independent review, reverse-proxy TLS, production authentication/rate limits, backups, monitoring, multi-process database strategy, delivery state machine, dispute handling, accounting, and final signed legal terms.
- A Devnet MOSUL-like mint, buyer/seller test token accounts, Token-2022 refund execution, and live transaction round-trip are still required before the MOSUL test flow can be described as end-to-end tested.
- The sale service remains a separate Mainnet-USDC prototype with payment disabled. The Devnet adapter is not wired into the auction checkout.
- NFT mint/transfer, buyer receipt, post-payment delivery retries, and end-to-end refund for the intended sale asset are still missing.
- Automatic SOL refunds require enough Devnet SOL and a dedicated low-privilege test keypair. Refund requests left `refund_processing` after an ambiguous RPC outcome require manual review before being retried.
- No on-chain cryptographic statement yet binds the project's MOSUL mint to the store. Seller terms approval binds seller/product/wallet/terms only.
