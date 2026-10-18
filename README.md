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
- **Public website:** GitHub Pages deployment is confirmed; the live wallet-proof page returned HTTP 200 in the 18 October 2026 evidence run. The site is a project preview and documentation record only. It does not provide live checkout, bidding, token payment, NFT minting, or product delivery. The sale API remains parked with `SALES_ENABLED=0`.

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

## First-sale checkout candidate

The repository now contains a fail-closed timed ascending auction for the
one-of-one `MOSUL-GENESIS-000001`. The final price is the highest eligible
wallet-signed bid at the announced close; there is no fixed sale price. The
winner receives a 24-hour exact-amount USDC payment request. The service
verifies the finalized Mainnet transfer, rejects replay, prevents duplicate
sale, and protects private delivery. Bid messages do not escrow funds.

This is not yet an active offer. Activation requires the owner's signed seller
terms and their SHA-256, an owner-verified receiving wallet, auction dates and
bid settings, the private delivery ZIP, an HTTPS deployment, and review of the
payment method for the seller's location. See [the auction checkout](checkout.html),
[deployment notes](sale-service/README.md), and [security boundary](sale-service/SECURITY.md).
### Auction-product readiness

The first 1/1 product now has a machine-readable asset manifest and fail-closed
readiness evaluator. The public `/readiness` endpoint remains available while
sales are parked, but bidding cannot open until the source record, watermarked
preview, private Collector Master, exact delivery ZIP hash, seller signature,
and auction window all pass. Payment activation remains a separate review.

The `Prepare encrypted auction product` workflow creates the exact Genesis lot
on the free CPU generator, signs its certificate, packages the private master,
and persists only an AES-256-GCM encrypted package plus its public preview and
hashes. The cited archival record is the Library of Congress Matson catalogue
item `2019706978`; the artwork is labelled as an interpretive AI work, not as a
historical photograph.
