# MOSUL-GENESIS-000001 — auction and buyer terms

**STATUS: DRAFT — AUCTION AND CHECKOUT MUST REMAIN DISABLED UNTIL SIGNED AND REVIEWED**

The final signed terms must identify the legal seller, country/jurisdiction,
support contact, exact product, opening bid, minimum increment, start/end time,
payment window, delivery window, refund policy, governing law, dispute contact,
and permitted use. The exact SHA-256 of the signed version must replace the
placeholder in product configuration and storefront metadata. The displayed
highest bid is not a fixed price; the final price is the highest eligible bid
accepted at auction close.

## Auction and payment

- The bidder signs a message from their own wallet. A signed bid records an
offer and does not transfer or escrow funds.
- The auction accepts ascending bids at or above the opening bid and at least
the configured increment above the current highest bid.
- The highest eligible bid at the announced close is selected. The winner has
24 hours to pay the exact winning amount in USDC. If that payment window expires,
the winning bid is defaulted and the next highest eligible bidder may be invited.
- A sale is complete only after the seller's receiving wallet receives the exact
finalized payment and the digital package is delivered.

## Product disclosure

- One digital Collector Master, certificate, and verification records.
- Edition 1/1 applies to this issued product identity; it does not make the
underlying 1932 public-domain source exclusive.
- Personal display and archival use only unless the signed version explicitly
grants broader commercial rights.
- No copyright, trademark, token, investment, resale-value, or NFT promise.
- NFT is not included unless a successful mint and asset address are shown
before bidding.

## Refund wording for legal review

The seller does not offer discretionary refunds after a completed payment and
delivery. This does not remove remedies that applicable law may require,
including remedies for duplicate payment, failed delivery, fraud, or material
misdescription. Applicable mandatory buyer rights remain in force. This text is
a draft and must be checked by Iraqi counsel before sale.

Do not set `SELLER_TERMS_ACCEPTED=1` while this draft marker remains. Do not
publish seller personal/contact details from this template; provide them to the
production service through its private environment configuration, where the
buyer-facing checkout discloses them before bidding.
