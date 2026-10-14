# Mainnet sale service

This directory contains a fail-closed timed ascending auction and checkout for
the one-of-one product MOSUL-GENESIS-000001. Bidders sign offers with their own
Solana wallets; a bid does not transfer or escrow funds. After auction close,
the highest valid bidder receives a 24-hour request for the winning bid amount
in USDC. The service verifies the finalized Mainnet transfer, prevents replay
and duplicate sale, records the completed price, and releases a private ZIP
through a short-lived, download-limited token.

It does not hold a wallet private key and never signs or sends a transaction.
The buyer signs in their own wallet. The seller receives USDC directly.

## Auction price

The final price is the highest eligible signed bid at the announced close. The
evidence-backed opening bid is 100 USDC and the minimum increment is 10 USDC.
Start and close are required deployment settings; there is no fixed sale
price. A winner has 24 hours to pay. If the
payment window expires, that bidder is marked as defaulted and the next highest
valid bidder may create an order. A bid is an offer, not proof of payment.

## Deployment and owner activation gates

`render.yaml` provisions the Docker service in Frankfurt with a one-GB
persistent disk and `/health` check. It starts with `SALES_ENABLED=0`: the
service can be deployed and health-checked, but `/auction`, bids, orders and
downloads return HTTP 503, and health output does not disclose seller details.
This parked deployment does not accept bids or payments.

Before enabling sales, upload the private delivery ZIP to the configured disk
path, store the signed-terms values and any remaining settings in Render's
environment-secret panel, choose a future auction window, and update the
storefront's API URL. Keep `SALES_ENABLED=0` throughout setup. Activation is
made only by a reviewed change to `render.yaml` setting it to `1`, followed by
a Blueprint sync; a dashboard-only override may be overwritten by a later
sync. Never put the ZIP, signature value, or generated secrets in GitHub.

When `SALES_ENABLED=1`, the service refuses to start until all of the following
are supplied:

- SALES_ENABLED=1
- SALES_MERCHANT_WALLET: an owner-verified Solana wallet, never a mint address
- SALE_AUCTION_ID, SALE_AUCTION_STARTS_AT, SALE_AUCTION_ENDS_AT
- optional SALE_AUCTION_OPENING_BID_USDC and SALE_AUCTION_INCREMENT_USDC may
  repeat, but may not override, the signed product settings (100/10 USDC)
- SELLER_LEGAL_NAME, SELLER_TRADE_NAME, SELLER_COUNTRY, SELLER_ADDRESS,
  SELLER_SUPPORT_EMAIL
- SELLER_TERMS_SIGNED_AT and SELLER_TERMS_SIGNATURE_B64, produced by
  `seller-sign-terms.html` using the receiving wallet
- DELIVERY_TOKEN_SECRET: at least 32 random characters
- DELIVERY_PACKAGE_PATH: private ZIP containing the Collector Master,
  certificate, verification records, and signed buyer license
- SALE_ALLOWED_ORIGIN: the exact HTTPS storefront origin
- SOLANA_MAINNET_RPC: optional private HTTPS RPC; defaults to the public RPC
- SALE_ADMIN_TOKEN: private token for the completed-sales feed

The service verifies the detached seller wallet signature against the exact
terms version and SHA-256 in products/MOSUL-GENESIS-000001.json. A changed file,
identity, wallet, version or timestamp invalidates the signature.
Deployment must provide HTTPS, durable database backups, log redaction,
monitoring, request throttling, and an independent security review.
Do not launch USDC checkout until the seller has confirmed the payment method
is permitted for this sale and location. The CBI has warned about digital
currencies and restricted licensed financial institutions from using cards and
e-wallets for crypto speculation/trading; this service does not make USDC an
authorized Iraqi payment instrument.

## Test

    PYTHONPATH=sale-service python -m unittest discover -s sale-service/tests -v

The tests use synthetic transaction objects and transfer no value.
