# Virtual auction rehearsal — 2026-10-17

## Scope

This is a synthetic, local rehearsal of the current signed-terms implementation
(`2026-10-13-v2`). It uses generated bidder keys and a mocked finalized USDC
transaction. It does not contact Solana, transfer funds, mint an NFT, or publish
the auction. The deployed sale service is still parked with `SALES_ENABLED=0`.

## Scenario and outcome

Three synthetic bidders submitted wallet-signed offers of 100, 110, and 120
USDC. After the simulated close, the highest bidder received an order for the
exact 120 USDC. The simulated transaction credited that amount to the seller
and debited it from the same winning wallet. The service marked the bid and
order paid, wrote exactly one completed-sale record, issued a short-lived
download token, allowed the configured three downloads, and rejected the
fourth. Repeating confirmation for the same transaction did not add another
sale. All 25 service tests passed, including the separate unpaid-winner/default
and next-bidder scenario.

## Problems and launch blockers found

1. **The signed terms do not match the previously requested product/payment.**
   The active v2 hash signed by the seller describes USDC and a digital file
   sale with no NFT. The user's earlier requested configuration was MOSUL
   payments and an NFT per product. That requires new terms, product settings,
   buyer acceptance and a new seller wallet signature; the existing signature
   cannot authorize those changes.
2. **No refund operation exists.** The terms distinguish a change-of-mind
   refund from remedies for non-delivery or material mismatch, but the service
   has no refund endpoint, workflow, audit record, or automated transfer. A
   required refund would currently need an independently executed and recorded
   seller transaction.
3. **No NFT mint/transfer is implemented.** The simulated delivery is a private
   ZIP link only; “edition 1/1” does not mint or transfer a token.
4. **Production delivery is unverified.** The test exercises download
   authorization, not a real uploaded private package, its integrity at the
   host, backup/restore, or actual browser download.
5. **The auction is not live.** `SALES_ENABLED=0`; there is no public bidding or
   payment endpoint until production configuration and readiness gates pass.
6. **No actual payment or chain-finality test was performed.** RPC behavior is
   represented by a synthetic transaction, so network outages, token-account
   edge cases, delayed confirmation, and real wallet UX remain untested.
7. **Seller disclosure still blocks activation.** Readiness requires
   `SELLER_ADDRESS`; the current record does not provide an agreed online-only
   service/contact address for that field.

## Existing safeguards exercised

- Signed bids bind bidder wallet, amount, auction, terms hash, expiry, and a
  single-use challenge.
- Bids below the opening amount or minimum increment, invalid signatures,
  replayed challenges, wrong payer, wrong payment amount, missing reference,
  and duplicate sales are rejected by the suite.
- Payment is requested only after close. The seller holds no app-side wallet
  private key; the buyer sends the payment from their wallet.
- The no-bid/underpayment/default path can expire an unpaid winner and offer a
  payment window to the next eligible bid.

## Short X update (Arabic)

تقدّم MOSUL HERITAGE: حسّنا التحقق من دفعة المزاد وربطناها بمحفظة الفائز، واجتزنا محاكاة محلية للمزايدة والتسوية والتسليم. البيع ما زال مغلقًا حتى استكمال الشروط والتجهيزات النهائية.

This post is 182 Unicode code points (under X's 280-character limit). It reports
verified local work and does not claim the auction is live.

## What must happen before real launch

Keep sales parked. Decide whether to retain signed v2 (USDC, file only) or issue
a new terms version for MOSUL and/or NFT delivery. Then implement the chosen
payment and asset flows, add an auditable refund/remedy process, resolve the
online seller disclosure field, provide and verify the production package,
test against Solana Devnet with disposable wallets, and only then repeat the
security review and launch gates.
