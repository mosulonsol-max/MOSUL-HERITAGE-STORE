# MOSUL HERITAGE — release and listing readiness review

**Reviewed 18 October 2026 UTC.** This is an evidence and engineering status record. It does not state that the token is approved for listing, that the store accepts payments, or that an NFT exists. Financial and on-chain market data are dated snapshots, not guarantees.

## Evidence-backed functions

| Function | Observed result | Evidence and limit |
| --- | --- | --- |
| Token identity | Solana mainnet Token-2022 mint, one billion displayed supply, six decimals; null mint/freeze and metadata update authorities in 17–18 Oct RPC snapshot | [Token record](TOKEN-VERIFICATION.md) and [machine snapshot](https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/blob/exchange-evidence-data/exchange-evidence.json). Recheck finalized chain state. |
| Project declaration | Ed25519 signature verifies wallet `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu` over exact mint/network/project statement | [Proof JSON](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json). Does not prove legal identity or ownership of other wallets. |
| Public site | GitHub Pages home, checkout preview and wallet-proof pages returned HTTP 200 on 18 Oct | [Public preview](https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/). Reachability is not a live sale test. |
| Artwork previews | Hourly generation, validation, save and Pages deploy jobs succeeded on 18 Oct | [GitHub Actions run](https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/actions/runs/39128799047). These are watermarked previews, not commercial releases. |
| Sale software | Unit suites: 34 sale, 17 repository, 13 AI and 6 Devnet payment tests (70 total). Winner-order challenges require the caller's nominated wallet to match the winner before disclosing the signing message; orders require fresh wallet signatures and settlement requires the exact on-chain order memo and configured token program. MOSUL conversion and wrong-program rejection have synthetic coverage. | Tests use synthetic transactions and do not prove Mainnet settlement, private delivery or production security. The service remains parked. |

## Blocking gates

| Area | Current finding | Required evidence or action |
| --- | --- | --- |
| Distribution and market | RugCheck/GeckoTerminal reported one MOSUL/SOL pool in the 18 Oct 13:12 UTC snapshot. GeckoTerminal estimated $2,372.0872 total reserve and zero 24h volume; RugCheck reported 0.222291323 SOL quote reserve, about $23.06 at its snapshot quote. Top-account and pool-vault token figures disagree. Direct largest-account RPC was rate-limited. | Obtain reliable finalized RPC account data, reconcile vault and top-account balances, document beneficial-owner declarations, and simulate executable depth. Refresh every market metric before any application. [Detailed dated report](EXCHANGE-FORM-ANSWERS-2026-10-17.md#supplemental-live-market-and-holder-report--2026-10-18-1312-utc). |
| Tokenomics and team | Supply and authority status are documented. Original allocations, treasury, vesting, locks, legal identity and team roster are not independently evidenced. | Owner-provided verifiable allocation history and private applicant/team/KYC evidence. Do not fabricate three team members or infer founder allocations from current balances. |
| Auction lot | Offline `/readiness` evaluation: `auction_ready=false`; `delivery_package`, `seller_terms_signature`, `seller_disclosure`, `auction_window` blocked. Product, source and public preview metadata pass their gates. | Supply the exact private ZIP matching the manifest, signed seller terms, seller disclosures and future auction configuration; inspect deployed `/readiness` afterward. The passing master gate checks manifest metadata, not possession of a physical master. [Auction gates](AUCTION-READINESS.md). |
| Payment | The local candidate now uses MOSUL mint + Token-2022, converts the winning USD-referenced bid using a recorded DEX Screener quote, and checks the token program on finalized transaction balances. Synthetic tests pass; no mainnet end-to-end test or live service exists. Terms v3 are an unsigned draft, merchant wallet is blank, and `SALES_ENABLED=0`; storefront has no API URL. | Seller must review/sign v3 from a seller-controlled payment wallet; complete local compliance review; secure delivery package; deploy and test quote, payment, duplicate handling, refunds and delivery on a controlled environment; configure monitoring/backups/rate limits. Do not enable until every gate passes. |
| NFT and fulfillment | No verified MOSUL HERITAGE NFT mint/asset address; no sale delivery demonstrated. | Owner-approved asset standard, metadata, rights, buyer license and mint transaction; independent asset verification and end-to-end buyer delivery test before claims of NFT functionality. |
| X publication | Most recently inspected X workflow failed because configured X API account had no credits; job explicitly reported no post published. | Owner adds X API credits and reruns/observes successful publication if automatic X posting is required. [Failed run](https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/actions/runs/39087802082). |
| Exchange applications | No official acknowledgement/reference was retained for OKX or MEXC in this repository. Earlier OKX success-screen claim remains unresolved. | Reconcile official account/form record before another OKX submission; use [OKX](https://www.okx.com/token-listing-apply) and [MEXC](https://www.mexc.com/token-listing-apply) pages only. Preserve exact receipt, date and reference if issued. [Draft dossier](EXCHANGE-LISTING-DOSSIER-2026-10-17.md). |

The evidence collector now compares the indexed and finalized-RPC token-account addresses and exact raw balances. Missing, empty, malformed or conflicting lists keep completeness `partial`; a successful collection workflow does not itself imply complete listing evidence.

## Activation order

1. Resolve distribution, market and applicant evidence, and reconcile existing exchange application receipts.
2. Confirm legal seller, product rights, payment asset and signed terms. Complete the private product package and sale API deployment with `SALES_ENABLED=0`.
3. Implement and test the agreed Mainnet payment and delivery flow, including exact token mint/program, order idempotency, finality, refunds, backup and independent review. Test on a suitable network without misrepresenting a rehearsal as a live sale.
4. Activate only after the deployed readiness checks and owner-approved terms pass. Publish verified NFT transaction/address only if an NFT is actually minted.

No engineering test can create trading liquidity, prove third-party beneficial ownership, complete private KYC or grant exchange approval. Those claims require their own evidence and, where applicable, the owner's action.
