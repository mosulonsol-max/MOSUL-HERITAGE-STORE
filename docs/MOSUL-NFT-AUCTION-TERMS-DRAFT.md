# MOSUL-GENESIS-000001 — MOSUL auction and NFT terms (DRAFT)

**Status: NON-OPERATIVE DRAFT. Do not publish as active terms, accept bids, charge a wallet, or mint for a buyer.**  
**Draft version:** 2026-10-17-v3-draft  
**Seller:** Ahmed Nabeel  
**Trade name:** MOSUL HERITAGE STORE  
**Store type:** online-only digital store; no physical retail shop  
**Support:** Mosulonsol@gmail.com  
**Receiving wallet:** `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu`  
**Proposed payment token (Mainnet only):** MOSUL Token-2022 mint `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump`  
**Product ID:** `MOSUL-GENESIS-000001`  
**Proposed NFT standard:** Metaplex Core on Solana

This is a working draft to prepare the next seller signature. It does not replace the signed 2026-10-13-v2 terms. Nothing in this draft activates a sale. The public catalog must remain preview-only and `SALES_ENABLED=0` until every item in the release gate at the end is satisfied. The seller's v2 wallet signature must never be treated as acceptance of this draft.

## 1. Lot and what transfers

The lot is one digitally generated Mosul heritage artwork, the verified Collector Master file, its provenance and verification records, and one Metaplex Core NFT representing the issued digital collectible. The public preview is not the Collector Master.

The catalogue must identify the historical source, reconstruction and AI-generation steps, model/version, edition number, final image and metadata hashes, and all known source/reuse restrictions. A “1/1” label identifies the issued collectible; it does not make the underlying archival photograph, public-domain source or historical subject exclusive.

No investment, expected profit, liquidity, token value, future resale market, or appreciation is promised. MOSUL is the payment asset only; paying in MOSUL does not give the buyer ownership in the MOSUL project or its treasury.

## 2. Timed ascending auction

- Every bid and the winning amount are denominated only in MOSUL, with six token decimals and the exact Mainnet mint shown above.
- Opening bid: **not set**. It may be published only after a fresh, documented MOSUL quote and executable liquidity/depth review support a defensible conversion of the researched USD 100 comparison benchmark.
- Minimum bid increment: **not set**. It must be displayed in MOSUL before opening and applied consistently by the auction service.
- Auction ID, start time, close time, extension rules, and any cancellation rule: **not set**. The live lot must display these values in UTC before the first bid.
- Highest eligible bid accepted by the service before the displayed close wins. The bid ledger must have a server timestamp, unique nonce, expiry, wallet and signed terms hash. Equal bids are ordered by the service's verified receipt time.
- Seller, receiving wallet, and anyone acting for the seller may not bid. The auction must disclose any cancellation, outage, or anti-manipulation rules before opening.

The lot cannot open while any required value above is blank or the auction service does not enforce the published rules.

## 3. Bidder eligibility and electronic acceptance

Before a bid is accepted, the bidder must be shown the full terms, product description, exact MOSUL mint, amount, auction ID, nonce and expiry. The bidder signs a human-readable message binding that exact bid and the SHA-256 of this exact terms version. The service stores the message, signature, UTC time and verification result.

A new version or any material terms change requires a new seller signature and fresh buyer acceptance. A wallet signature demonstrates control of that wallet and records acceptance of the displayed message; by itself it does not verify a civil identity or guarantee enforceability in every jurisdiction.

## 4. Payment, escrow and settlement

The winner must pay the exact winning MOSUL amount using the stated Solana Mainnet mint, decimals, network and unique order reference. A payment counts only after the program or verifier confirms the exact finalized token transfer, correct source and destination, exact amount and mint, order reference, and no replay or duplicate settlement.

**Release blocker:** the current payment prototype is Devnet-only and is not integrated with this auction. Do not ask a buyer to send funds directly to the receiving wallet before NFT delivery. Production must use an independently reviewed, replay-resistant escrow/atomic settlement path that releases payment to the seller only when the NFT transfer to the winning buyer is confirmed, and returns payment when the sale cannot complete. If this atomic path is unavailable, the auction must not accept bids or payment.

## 5. NFT and file delivery

On a successful atomic settlement, the winner receives the specified Metaplex Core asset in the buyer wallet and an authenticated, time-limited link to the Collector Master bundle and certificate. The NFT mint/address, owner after transfer, metadata URI, image hash and transaction signature must be verified and provided to the buyer.

Metadata must be durable and independently retrievable. The buyer should download the private bundle promptly and verify its included hashes. The seller must provide support for a failed or corrupt delivery. If the seller cannot deliver the described NFT or file, the sale is incomplete and escrow returns the payment under the settlement rules.

## 6. License and provenance

After completed payment, NFT transfer and delivery, the current NFT holder receives a worldwide, perpetual, royalty-free, non-commercial license to display and archive the delivered artwork and package. This limited license follows the NFT to a verified new holder; a previous holder's public display license ends after transfer, though the former holder may retain one private archival copy for records.

No commercial reproduction, sublicensing, removal of authenticity marks, false authorship claims, or separate minting is granted without written permission. The license does not transfer rights in archival source material or third-party marks. AI-generated elements may not qualify for copyright protection in some jurisdictions; no exclusive copyright in such elements is promised. The seller warrants only that they have authority to grant the rights stated here and must document the source and commercial-use basis before listing.

## 7. Refunds, failed settlement and final sale

The seller's policy is **no discretionary refund after a completed sale**, meaning the exact payment has finalized, the matching NFT has transferred to the buyer, and the conforming digital bundle has been delivered.

Before that point, duplicate or incorrect payments, failed/cancelled settlement, non-delivery, a material mismatch with the catalogue, or another mandatory remedy must be handled through the escrow/refund path. Nothing here waives rights that applicable law does not permit the parties to waive. Refunds go to the verified paying wallet except where applicable law requires another method. Network fees and market-value changes are not refundable except where mandatory law requires otherwise.

## 8. Privacy, security and records

Public auction records should show only the information needed to verify the auction, bids and settlement. Signed messages, wallet addresses, transaction IDs, order references and delivery logs are retained for security, fulfilment, accounting and disputes. Public blockchain data cannot be removed by the seller. No support process will request a seed phrase or private key.

## 9. Seller, support and disputes

Seller contact is the email above. The store is online-only and has no in-person shop. Before a real sale, the seller disclosure and complaint route must be checked for the countries where the offer is made. This draft makes no claim that omitting a street address satisfies every disclosure rule.

The parties should first try to resolve a written support complaint in good faith. Any governing-law, forum and consumer-rights clauses require review for the seller's actual jurisdiction and buyer locations before the terms become active. No clause removes a mandatory consumer protection.

## 10. Record and release gate

The operative record, if later approved and signed, must bind the exact file hash, seller, trade name, receiving wallet, Mainnet token mint, product and auction rules. The detached seller signature must be independently verified before deployment. The v2 signature does not satisfy this requirement.

Before enabling any MOSUL auction, all of the following must be complete:

1. Set and publish a MOSUL opening amount and increment from fresh, documented price and executable liquidity evidence.
2. Publish the auction ID and UTC opening/closing schedule.
3. Confirm the exact product, commercial-use basis, private delivery bundle, SHA-256 hashes and durable metadata URI.
4. Implement the audited escrow/atomic MOSUL-payment plus NFT-delivery path, including failure refunds and replay protection.
5. Run and pass the full payment/refund/NFT/delivery rehearsal on Devnet.
6. Complete an independent security review and document findings.
7. Have the seller sign the final hash of these terms and separately sign a narrow MOSUL-to-project association statement.
8. Verify deployment configuration, monitoring and buyer support while keeping Mainnet funds out of tests.

Until then, this is only a draft and the store must remain parked.
