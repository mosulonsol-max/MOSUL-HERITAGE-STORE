# MOSUL HERITAGE sale readiness review

Review date: 2026-10-17

## Current operating state

- The public catalog is a preview catalog. Product generation can produce watermarked, provenance-recorded previews; this does not mean a product is saleable.
- The sale API has `SALES_ENABLED=0` in `render.yaml`. The current product and signed seller terms describe a USDC/Mainnet auction and a digital Collector Master download, not a MOSUL-token sale or NFT transfer.
- The mainnet payment route remains blocked by readiness gates. The payment prototype in `payment-service/` is pinned to Devnet and is not wired into the auction API.
- The current Devnet live rehearsal tests native SOL only. Token-2022 MOSUL-test-mint transaction verification has unit coverage, but has not been exercised against live Devnet.
- No mainnet transfer, refund, NFT mint, or buyer delivery was attempted during this review.

## Requested work, in order

| Work item | State | Remaining evidence/action |
| --- | --- | --- |
| 1. Auction denominated in MOSUL | **Not ready** | Auction challenge/ledger and product terms are currently USDC. Implement asset-aware bid UI and payment/settlement as a separate Devnet configuration; do not change the already signed v2 USDC terms. The production MOSUL mint is not a Devnet test mint. |
| 2. NFT and delivery | **Not ready** | Existing fulfillment is a gated download ZIP for a Collector Master, not an NFT. Select an NFT standard; implement mint/transfer and retry-safe fulfillment; test buyer receipt on Devnet. Metadata must point to a durable, rights-cleared asset. |
| 3. Refund path | **Partially hardened, wrong asset** | The Devnet SOL prototype now excludes refund-requested sales from the benchmark and marks a refund complete only after a finalized exact refund is verified. MOSUL-token refund execution, a timed refund/dispute policy, and integration with the auction fulfillment state machine remain missing. The published seller terms v2 already disclaim a discretionary refund after conforming delivery/payment, subject to mandatory remedies; a new MOSUL/NFT terms version must be signed before launch. |
| 4. Store setup | **Configured but parked** | Render Blueprint holds the app in `SALES_ENABLED=0`. Seller name, trade name, Iraq, support email and receiving wallet are configured. The disclosure now supports an online-only store description without inventing a street address. Deployment status, private delivery package, full terms and operational monitoring still need verification. Render Starter plus persistent disk is not a free deployment. |
| 5. Devnet run and security review | **Unit-level progress; live MOSUL E2E remains** | Payment tests cover exact SOL and mocked Token-2022 checks; auction tests cover signed bids and mock settlement. Execute a live Devnet Token-2022 lifecycle with ephemeral keys/test mint, then test auction close, payment, NFT receipt, delivery, failed/replayed transfers and refund. Keep Mainnet disabled. |
| 6. Cryptographic link between MOSUL and project | **Prepared; owner signature missing** | The signed seller-terms record binds seller, wallet, product and terms hash, not the token mint. A separate wallet-signing page and offline verifier now bind the project, Mainnet mint, receiving wallet and narrow scope of the claim. The owner still has to sign and preserve the exported record. |

## Security fixes in this review

1. Native-SOL payment verification now requires a finalized transaction inside the intent time window and the payer as a transaction signer.
2. Refund requests no longer delete sale records immediately. The price-comparison feed excludes the sale while its intent is not paid.
3. Refund execution claims the request before sending. It verifies the finalized transaction's exact source, destination, amount and `REFUND:<intent>` memo before marking it refunded. Ambiguous outcomes are held in `refund_processing` to prevent an automatic duplicate transfer and require manual reconciliation.
4. Added fail-closed Token-2022 MOSUL-test-mint payment verification: exact `transferChecked`, exact token balance decrease/increase, buyer, merchant, mint, decimals and memo; the finalized mint account must be initialized and owned by the Token-2022 program.
5. The sale service can disclose an online-only seller location without a fabricated postal address. This is a display/readiness change, not a legal review of disclosure obligations.
6. Added an exact MOSUL association statement page and an offline Ed25519 verifier; no signature is fabricated or stored by the application.

## Release gate

Do not turn on public sales until one coherent Devnet flow is completed and independently reviewed: signed MOSUL bid → closed auction → exact MOSUL settlement → NFT received by the winning wallet → delivery record → a tested, policy-compliant refund/dispute route. Then issue a new buyer/seller terms version binding the asset mint, auction currency, delivery, refund conditions and online-only seller contact. The owner must sign that exact version. The mainnet MOSUL relation statement also needs the project wallet's signature. Production activation and any Mainnet transaction remain separate owner-controlled releases.
