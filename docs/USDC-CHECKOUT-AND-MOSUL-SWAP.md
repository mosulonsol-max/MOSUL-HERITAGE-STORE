# USDC auction checkout and optional MOSUL swap

## Chosen payment flow

- Auction bids and the winning settlement remain denominated in USDC.
- The checkout may offer an optional Jupiter swap interface, defaulting to MOSUL input and USDC output. USDC is the fixed output token.
- A buyer reviews the swap quote and transaction in their own wallet and signs it there. The swap is separate from bidding and auction payment. It does not submit a bid or pay the seller.
- The swap output goes to the buyer's wallet. The buyer must separately make the auction payment in USDC through the configured payment flow.
- MOSUL HERITAGE does not custody swap funds and does not exchange MOSUL for USDC on the buyer's behalf.

## Safety and readiness constraints

- The converter is hidden unless the auction readiness endpoint passes and the auction is open or closed.
- The Jupiter interface is loaded only after the user clicks its button. If it fails to load, no swap has been requested.
- The mint addresses configured in the interface are MOSUL Token-2022 `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump` and Solana mainnet USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`.
- The interface defaults to MOSUL input and fixes USDC output. Buyers must confirm the displayed mints, quote, minimum output, price impact, slippage, and network fees in Jupiter and their wallet before signing.
- If Jupiter has no executable route, the buyer must not increase slippage to force one. Live route availability and liquidity have not been verified as part of this change.
- A successful swap is not proof of auction payment. Payment verification and delivery remain separate and must pass the configured service checks.
- The checkout's current production API URL is not configured, and `SALES_ENABLED` remains `0`. These changes do not activate sales or enable mainnet payment.

## Signed terms

The existing seller terms signature covers the exact published v2 terms and wallet. This change does not modify those terms. Any future change to the seller's obligations, fees, refund rules, or payment recipient requires publishing and signing a new exact terms version. The optional third-party swap is a buyer-controlled wallet action and is not represented as a service performed by the seller.
