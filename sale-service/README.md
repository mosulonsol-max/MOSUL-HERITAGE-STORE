# Mainnet sale service

This directory contains a fail-closed checkout for the first one-of-one product,
MOSUL-GENESIS-000001. It creates an exact Solana Pay USDC request, verifies the
finalized Mainnet transaction independently, prevents reuse of a transaction or
resale of the one-of-one item, records a first-party completed sale, and releases
a private ZIP only through a short-lived, download-limited token.

It does not hold a wallet private key and never signs or sends a transaction.
The buyer signs in their own wallet. The seller receives USDC directly.

## Why USDC for the first sale

The listing price is USD 149 and the purpose is to fund operating costs. A fixed
USDC amount avoids an unaudited MOSUL/USD conversion and does not represent the
MOSUL token as stable or sufficiently liquid. MOSUL payment can be added only
after a separate finalized Mainnet payment and liquidity test.

## Owner activation gates

The service refuses to start until all of the following are supplied:

- SALES_ENABLED=1
- SELLER_TERMS_ACCEPTED=1
- SALES_MERCHANT_WALLET: an owner-verified Solana wallet, never a mint address
- DELIVERY_TOKEN_SECRET: at least 32 random characters
- DELIVERY_PACKAGE_PATH: private ZIP containing the Collector Master,
  certificate, verification records, and signed buyer license
- SALE_ALLOWED_ORIGIN: the exact HTTPS storefront origin
- SOLANA_MAINNET_RPC: optional private HTTPS RPC; defaults to the public RPC
- SALE_ADMIN_TOKEN: private token for the completed-sales feed

Before activation, replace the placeholder terms version and SHA-256 in
products/MOSUL-GENESIS-000001.json with the exact hash of the signed terms.
Deployment must provide HTTPS, durable database backups, log redaction,
monitoring, request throttling, and an independent security review.

## Test

    PYTHONPATH=sale-service python -m unittest discover -s sale-service/tests -v

The tests use synthetic transaction objects and transfer no value.
