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
opening bid, minimum increment, start, and close are required deployment
settings; there is no fixed sale price. A winner has 24 hours to pay. If the
payment window expires, that bidder is marked as defaulted and the next highest
valid bidder may create an order. A bid is an offer, not proof of payment.

## Owner activation gates

The service refuses to start until all of the following are supplied:

- SALES_ENABLED=1
- SELLER_TERMS_ACCEPTED=1
- SALES_MERCHANT_WALLET: an owner-verified Solana wallet, never a mint address
- SALE_AUCTION_ID, SALE_AUCTION_STARTS_AT, SALE_AUCTION_ENDS_AT
- SALE_AUCTION_OPENING_BID_USDC and SALE_AUCTION_INCREMENT_USDC
- SELLER_LEGAL_NAME, SELLER_COUNTRY, SELLER_SUPPORT_EMAIL
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
Do not launch USDC checkout until the seller has confirmed the payment method
is permitted for this sale and location. The CBI has warned about digital
currencies and restricted licensed financial institutions from using cards and
e-wallets for crypto speculation/trading; this service does not make USDC an
authorized Iraqi payment instrument.

## Test

    PYTHONPATH=sale-service python -m unittest discover -s sale-service/tests -v

The tests use synthetic transaction objects and transfer no value.
