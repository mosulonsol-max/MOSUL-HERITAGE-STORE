# Auction readiness — MOSUL-GENESIS-000001

The product is not auction-ready because a page says so. It is ready only when
the service returns `auction_ready: true` from `/readiness`.

## Required gates

1. The product remains a disclosed 1/1 timed ascending auction with no hidden
   reserve, a published opening bid and a published minimum increment.
2. The archival source has an official HTTPS catalogue record and a reviewed
   reuse status. The current record is Library of Congress item `2019706978`,
   from the Matson collection, whose catalogue uses the rights advisory “No
   known restrictions on publication.”
3. The public preview is visibly watermarked and pinned by SHA-256.
4. The Collector Master is private, at least 512×512, and pinned by SHA-256.
5. The exact private delivery ZIP exists on the service and matches the
   approved package SHA-256.
6. The seller-wallet signature verifies over the exact product and terms hash.
7. An auction ID and a valid opening/closing window are configured.

The automated preparation workflow uses a fixed product prompt and seed,
records the pinned model revision, signs the certificate with Ed25519, creates
a deterministic ZIP, and encrypts it with AES-256-GCM. The encryption key is
domain-separated from the configured signing seed with HKDF-SHA256. The
plaintext Collector Master and ZIP are erased with the ephemeral runner.

## Deliberate separation

Passing these gates permits bidding only. It does not silently enable payment.
The payment asset, settlement, production deployment and buyer delivery still
require their own final review. This separation prevents an artwork-generation
success from accidentally moving real funds.
