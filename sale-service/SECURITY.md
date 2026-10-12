# Production security boundary

- Checkout is disabled unless the owner explicitly enables it and accepts the
  final seller terms.
- The merchant wallet is a public receiving address supplied at deployment.
  No seed phrase or signing key is used by this service.
- A payment settles only when a finalized Solana Mainnet transaction contains
  the unique order reference and increases merchant-owned USDC balances by the
  exact raw amount within the order validity window.
- Order IDs, references, payment signatures, and product inventory are unique.
  The one-of-one product cannot be reserved twice or sold twice.
- Delivery requires a paid order and an HMAC-authenticated token that expires
  after 15 minutes and allows no more than three downloads.
- The Collector Master and delivery ZIP remain outside the public repository.
- Browser requests are restricted to the exact HTTPS storefront origin.
- Production still requires an HTTPS reverse proxy, rate limiting, durable
  backups, monitoring, secret rotation, and independent review.

The service does not automate refunds. A real refund requires the seller to
review the request and approve a wallet transaction under the published terms.
This avoids placing a spending key on the web server.
