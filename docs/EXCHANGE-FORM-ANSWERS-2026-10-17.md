# MOSUL — Exchange application field answers
Prepared 17 October 2026; reviewed 18 October. **Draft answers; official submission status is not conclusively reconciled. Do not resubmit to OKX until its prior reported success screen is checked against the official account or acknowledgement.** Public project facts only. Applicant identity and KYC belong in private exchange forms.

## MEXC: Project Information (official form)

| Field | Proposed answer | Verification status |
| --- | --- | --- |
| Project Name | MOSUL HERITAGE | Owner-provided |
| Token/Crypto Symbol | MOSUL | Explorer snapshot |
| Project Description | MOSUL HERITAGE is an early-stage Solana digital collectibles project inspired by Mosul's architecture and cultural history. It is developing original AI-assisted artworks, provenance records, digital auctions, NFTs and a planned token-based checkout. The repository provides a public development record. Production sales, MOSUL payments, and NFT delivery are not yet independently verified as live. | Reflects repository status |
| Project Official Website Link | https://mosulonsol-max.github.io/MOSUL-HERITAGE-STORE/ (GitHub Pages live, HTTP 200 verified 2026-10-17; production sales still unverified). | Blocking |
| Official X Account | https://x.com/MosulOnSol | Owner-provided |
| Smart Contract/Block Explorer Link | https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump | Explorer snapshot 12 Oct; refresh |
| Listed Exchange Platforms | **Unverified**; list only confirmed CEX listings, or N/A if none. Do not count DEX aggregators as CEX spot listings. | Blocking |
| CoinMarketCap or CoinGecko Link | **Unverified**; N/A only after checking both services. | Pending |

Official form: https://www.mexc.com/token-listing-apply

## MEXC: Personal Information / Team Information
- Applicant type: Individual / natural person, resident in Iraq (owner-confirmed; exchange eligibility unverified).
- Legal name, contact email, proof of identity, nationality and residence: **provide privately through the official exchange portal only**. Never store KYC in GitHub.
- Team members, roles, founder experience and legal status: owner must verify. Do not invent staff or a registered company.
- Token creator wallet supplied by owner: `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu`; wallet signature independently verified 2026-10-17; see docs/MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json.
- The project-to-mint association is documented by the independently verified wallet-signed statement at docs/MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json; legal identity is a separate matter.
- **Owner disclosure, 2026-10-17:** The owner states there are no other wallets under their or the project's control holding MOSUL beyond the verified signing wallet. This is a declaration, not an on-chain proof of beneficial ownership. Do not describe other token holders as independent until verified.

## OKX: Core project answers
- Project: MOSUL HERITAGE; token MOSUL; Solana Token-2022.
- Candidate mint: `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump`.
- Project stage: early development; production marketplace and token checkout unverified/inactive.
- Public GitHub: https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE
- Whitepaper: https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/blob/main/docs/WHITEPAPER.md
- Official X: https://x.com/MosulOnSol
- Tokenomics: 1,000,000,000 supply and 6 decimals verified by Solana RPC at 2026-10-17T19:37:08Z; mint and freeze authorities null. The signer wallet has 7,892,140.40988 MOSUL (0.789214%). **Owner declaration:** no other owner- or project-controlled MOSUL wallets. This is not independently verifiable from a wallet signature; beneficial ownership of third-party accounts, top holders, allocation history, treasury obligations, vesting and executable liquidity remain unverified. DexScreener returned zero pools in this snapshot, which does not establish absence of all markets.
- No guaranteed appreciation, listing, revenue or fundraising claim.
- Legal identity/KYC, team disclosure, token ownership and current market metrics must be supplied and verified before final submission.

Official form: https://www.okx.com/token-listing-apply

## Submission blockers and controls
1. GitHub Pages HTTPS wallet-proof page returned HTTP 200 on 2026-10-17. Confirm any claimed production sales and wallet checkout independently.
2. Completed: owner signed the exact association statement using Phantom; Ed25519 signature independently verified and published in docs/MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json.
3. Completed as of 2026-10-17T19:37:08Z: Token-2022 metadataPointer and tokenMetadata extensions; mint, freeze and metadata update authorities null; supply 1B. Refresh before application.
4. Owner declares one MOSUL-holding wallet only. Verify top holders, historical token distribution, any custody arrangements, allocation/treasury obligations and vesting independently. Do not equate current wallet balance with original founder allocation.
5. Obtain timestamped real trading pairs, exchange listings, liquidity and 24h volume.
6. Owner completes private KYC and accepts official exchange terms.
7. Reconcile any prior submission on each official portal and preserve acknowledgement IDs, URLs and timestamps. **No official acknowledgement is retained here; absence of one does not prove non-submission. Avoid duplicate OKX submission.**

**Do not make public claims of listing, approval, secured financing, or exchange partnership.**

## Evidence snapshot

Live machine-collected JSON: https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/blob/exchange-evidence-data/exchange-evidence.json . Snapshot 2026-10-17T19:37:08Z. The top-token-accounts query returned HTTP 429; no concentration conclusion can be drawn. DexScreener returned no pools. Do not present unverified liquidity or market metrics to exchanges.

## Additional verified market evidence — 2026-10-17T19:42:05Z

Source: GitHub Actions run https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/actions/runs/39063579479/artifacts/12112297878 (raw API snapshot). GeckoTerminal Solana token-pools endpoint returned one MOSUL/SOL pool, address `FZQEzikp7rkjaggBkeM4uW8RPT2seRBWKWboQLGW1VZq`, created `2026-10-10T21:32:52Z`, reported pool reserve **$2,372.0872**, reference token price **$0.00000312730565**, and reported 24h pool volume **$0.0**. This is a low-liquidity snapshot, not guaranteed executable depth or complete all-venue volume. DexScreener returned zero pools for this mint in the same snapshot. Largest-token-accounts RPC still failed (429/403/400); top holder concentration **unknown, not 0%**. Pump.fun frontend API returned 404/403, so bonding curve status remains unverified. Never represent the missing results as zero holdings or zero launchpad activity.

## Supplemental live market and holder report — 2026-10-18 13:12 UTC

Sources queried directly at 13:12:07 UTC: [RugCheck token report API](https://api.rugcheck.xyz/v1/tokens/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump/report) and [GeckoTerminal token-pools API](https://api.geckoterminal.com/api/v2/networks/solana/tokens/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump/pools). Both returned one MOSUL/SOL market, `FZQEzikp7rkjaggBkeM4uW8RPT2seRBWKWboQLGW1VZq`. GeckoTerminal reported a $2,372.0872 pool reserve and $0.00 24h volume, with no swaps reported in its 24h transaction counters. RugCheck reported 2 holders/accounts: a pool-associated account at 99.2108% and the creator wallet at 0.7892%. These are provider-reported account figures, not verified beneficial-owner distribution; the RPC largest-account call remains rate-limited.

The two sources disagree on price/valuation. RugCheck's market record lists `0.222291323 SOL` on the quote side (about **$23.06** at its quote price) and `785,207,859.59012 MOSUL` in the associated token vault, while GeckoTerminal's reserve estimate marks the pool at **$2,372.09**. Do not describe the marked token-side reserve or total pool reserve as executable sell depth. The pool's quote reserve is small, no 24h trades were reported, and exact executable exit depth has not been independently simulated. The RugCheck top-account result (992,107,859.59012 MOSUL) also does not match its market vault token amount (785,207,859.59012); this discrepancy must be reconciled against finalized Solana RPC before presenting a definitive concentration or liquidity claim to an exchange.

**Updated status:** holder information is now available as a third-party indexed snapshot, but holder concentration and executable liquidity remain **partially unverified** pending finalized RPC corroboration and a trade-depth check. No holder or liquidity figure should be represented as independently chain-verified from this snapshot alone.
