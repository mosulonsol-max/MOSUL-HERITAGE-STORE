# MOSUL HERITAGE

**Project record and development repository**  
**Current stage: documentation and preview. No product is for sale; token payment and NFT minting are inactive.**

MOSUL HERITAGE is developing digital collectibles inspired by Mosul’s architecture, places, and cultural history. This repository records project documentation and evidence. Statements are limited to what can be independently checked and dated.

## MOSUL token — verified facts

As checked on Solscan on 12 October 2026, the candidate mint page displays:

| Field | Explorer record |
| --- | --- |
| Mint | `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump` |
| Network / owner program | Solana mainnet / Token-2022 |
| Current supply | 1,000,000,000 MOSUL |
| Decimals | 6 |
| Mint, freeze, update authorities | N/A for each |
| Token Extensions | TRUE; exact extensions not enumerated here |

[Inspect the mint on Solscan](https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump) · [Read the verification record](docs/TOKEN-VERIFICATION.md) · [Read the whitepaper](docs/WHITEPAPER.md)

**Project association is not yet cryptographically proved.** The on-chain record does not by itself prove that MOSUL HERITAGE issued or controls this token or the displayed creator wallet. A signed statement from a project-controlled wallet is still required. The mint address is not a wallet or payment destination; do not send funds to it.

## Smart-contract status

The token is represented by a mint governed by Solana’s shared Token-2022 program. This is not a custom MOSUL smart-contract program. This repository does not currently publish a separate project-specific program address or source code. The project will not claim custom contract functionality without verifiable program evidence.

## Project status

- **Token payment:** inactive; no end-to-end payment test completed.
- **Product sales:** blocked; no item is currently for sale.
- **NFT issuance:** not completed; no MOSUL HERITAGE NFT asset address is claimed.
- **Tokenomics beyond the verified mint snapshot:** allocation, treasury, vesting, lock, and burn information is not independently verified here.
- **Storefront automation:** not represented as live in this repository.
- **Public website:** GitHub Pages is not yet confirmed as deployed. The repository is the intended canonical project record once its public release and hosting are configured.

## Release gates

1. Publish and independently verify the signed project-to-mint statement.
2. Document relevant Token-2022 extensions and any owner-approved token allocation or treasury facts.
3. Complete product source, rights, logo, authenticity, and buyer-license review.
4. Test secure checkout, transaction finality, duplicate-payment rejection, refunds, and delivery before enabling sales.
5. If an NFT is issued, publish its verified mint transaction and asset address only after successful minting.
6. Enable the public repository and GitHub Pages only after the project’s public-release settings are reviewed.

These are gates, not launch dates. No price, investment return, listing, sales, or launch date is promised.

## Transparency and security

The repository is intended to hold public documentation, evidence, and source code approved for release. Never commit seed phrases, private keys, signing keys, payment-provider secrets, unredacted buyer information, or private collector masters. Public transparency does not require exposing credentials or customer data.

A hash, certificate, signature, or watermark can support verification of a specific record or file; none alone prevents copying or proves a sale, copyright ownership, or NFT ownership. Product records must state what has and has not been verified.

## Files

- [Token verification](docs/TOKEN-VERIFICATION.md): dated Solscan observations and binding limitations.
- [Whitepaper v0.2](docs/WHITEPAPER.md): bilingual project, token, utility, status, and risk disclosures.

Last reviewed: **12 October 2026**.


## Governed AI engine

The `ai-engine/` directory contains an Ollama/Qwen planning layer, deterministic capability allow-list, source-evidence ledger, Ed25519 provenance helpers, audit log, and policy tests. The hourly preview workflow runs the policy suite before generation. Mainnet, checkout, settlement, minting, and real-value transfers remain disabled; approved devnet tests are the only permitted financial path.
