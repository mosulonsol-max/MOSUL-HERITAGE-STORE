# MOSUL HERITAGE sale readiness review

Review date: 2026-10-17

## Current operating state

- The public catalog is a preview catalog. Product generation can produce watermarked, provenance-recorded previews; this does not mean a product is saleable.
- The sale API has `SALES_ENABLED=0` in `render.yaml`. The current product and signed seller terms describe a USDC/Mainnet auction and a digital Collector Master download, not a MOSUL-token sale or NFT transfer.
- The mainnet payment route remains blocked by readiness gates. The payment prototype in `payment-service/` is pinned to Devnet and is not wired into the auction API.
- The Devnet Token-2022 and Metaplex Core live-rehearsal scripts and a manual GitHub Actions workflow are now prepared. The local run was attempted, but the shared Devnet faucet returned HTTP 429 before any transaction was sent; neither live test is complete.
- No mainnet transfer, refund, NFT mint, or buyer delivery was attempted during this review.

## Requested work, in order

| Work item | State | Remaining evidence/action |
| --- | --- | --- |
| 1. Auction denominated in MOSUL | **Not ready** | Auction challenge/ledger and signed terms remain USDC-specific. Exact Token-2022 payment verification is unit-tested and a Devnet live script now creates a disposable test mint, but it has not run on-chain. The production MOSUL mint is not a Devnet test mint. No reliable current MOSUL/USD price and market-depth quote was found to convert the researched $100 opening benchmark into MOSUL. |
| 2. NFT and delivery | **Not ready** | The product still fulfills a private download ZIP, not an NFT. A Metaplex Core Devnet mint/transfer/owner-check script is prepared; the faucet prevented an on-chain run. Production metadata needs durable storage, and paid auction fulfillment needs an escrow/atomic or otherwise independently audited transfer path. |
| 3. Refund path | **Devnet code implemented; live round-trip pending** | The worker now routes Token-2022 refunds through a separate `spl-token` transfer, verifies exact mint, decimals, amount, merchant debit, buyer credit and memo, and checks that the Devnet keypair matches the merchant. Ambiguous sends remain parked to prevent duplicate payouts. Unit tests pass; the live script now exercises a payment/refund round-trip, but the faucet blocked the attempt before any transaction. The signed v2 terms cover USDC/file delivery, not the requested MOSUL/NFT sale. |
| 4. Store setup | **Configured but parked** | Render Blueprint holds the app in `SALES_ENABLED=0`. Seller name, trade name, Iraq, support email and receiving wallet are configured. The disclosure now supports an online-only store description without inventing a street address. Deployment status, private delivery package, full terms and operational monitoring still need verification. Render Starter plus persistent disk is not a free deployment. |
| 5. Devnet run and security review | **Unit tests pass; live run blocked by faucet quota** | Payment tests cover exact SOL and mocked Token-2022 checks; auction tests cover signed bids and mock settlement. A manual workflow now runs live SOL, Token-2022 payment/refund and Core tests with ephemeral keys. The local RPC faucet returned 429; no on-chain payment, refund or NFT was recorded. A coherent MOSUL auction→payment→NFT→delivery→refund integration and independent review still remain. |
| 6. Cryptographic link between MOSUL and project | **Prepared; owner signature missing** | The signed seller-terms record binds seller, wallet, product and terms hash, not the token mint. A separate wallet-signing page and offline verifier now bind the project, Mainnet mint, receiving wallet and narrow scope of the claim. The owner still has to sign and preserve the exported record. |

## Security fixes in this review

1. Native-SOL payment verification requires a finalized transaction inside the intent time window and the payer as a transaction signer.
2. Refund requests no longer delete sale records immediately. The price-comparison feed excludes the sale while its intent is not paid.
3. Refund execution claims the request before sending. It verifies the finalized transaction's exact source, destination, amount and `REFUND:<intent>` memo before marking it refunded. Ambiguous outcomes are held in `refund_processing` to prevent an automatic duplicate transfer and require manual reconciliation.
4. Added fail-closed Token-2022 MOSUL-test-mint payment verification: each single `transferChecked` instruction must match the buyer debit and merchant credit in token balances, plus the exact mint, decimals and memo; the finalized mint account must be initialized and owned by the Token-2022 program. Refund verification applies the same same-instruction rule to the merchant debit and buyer credit.
5. The sale service can disclose an online-only seller location without a fabricated postal address. This is a display/readiness change, not a legal review of disclosure obligations.
6. Added an exact MOSUL association statement page and an offline Ed25519 verifier; no signature is fabricated or stored by the application.
7. Added a separate exact Token-2022 refund route; token base units are no longer treated as SOL lamports. Ambiguous CLI/RPC outcomes remain blocked from automatic retry.

## Release gate

Do not turn on public sales until one coherent Devnet flow is completed and independently reviewed: signed MOSUL bid → closed auction → exact MOSUL settlement → NFT received by the winning wallet → delivery record → a tested, policy-compliant refund/dispute route. Then issue a new buyer/seller terms version binding the asset mint, auction currency, delivery, refund conditions and online-only seller contact. The owner must sign that exact version. The mainnet MOSUL relation statement also needs the project wallet's signature. Production activation and any Mainnet transaction remain separate owner-controlled releases.
