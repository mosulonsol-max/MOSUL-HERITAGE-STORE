# Production security boundary

- Checkout is disabled unless the owner explicitly enables it and accepts the
  final seller terms.
- Bids require an Ed25519 wallet signature over the auction ID, amount, terms
  hash, one-time challenge, and expiry. Bid messages do not escrow funds.
- Only after the auction closes does the highest valid bidder receive a
  24-hour exact amount payment request. An expired winner is defaulted and the
  next highest valid bid can be selected.
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
- Application request logs omit request paths because download URLs carry a
  short-lived token. The HTTPS reverse proxy must redact query strings too.
- Production still requires an HTTPS reverse proxy, rate limiting, durable
  backups, monitoring, secret rotation, and independent review.

The service does not automate refunds. A real refund requires the seller to
review the request and approve a wallet transaction under the published terms.
This avoids placing a spending key on the web server.
