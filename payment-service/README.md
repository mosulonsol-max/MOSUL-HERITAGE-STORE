# Solana Devnet payment rehearsal

This service is a Devnet prototype. It can create native-SOL intents and can verify exact Token-2022 MOSUL test-mint transfers when `DEVNET_MOSUL_MINT` is configured. The verifier checks the finalized transaction, intent memo/window, transfer instruction, buyer debit, merchant credit, mint program owner, initialization state, and decimals. It cannot select Mainnet: the RPC URL is fixed in code.

Run tests:

```bash
PYTHONPATH=payment-service python -m unittest discover -s payment-service/tests -v
```

Run the optional live rehearsal:

```bash
python -m pip install -r payment-service/requirements-devnet-test.txt
PYTHONPATH=payment-service python payment-service/live_devnet_test.py
```

The existing live rehearsal creates ephemeral wallets, requests Devnet SOL, sends an exact transfer with a unique memo, verifies it through a separate RPC read, and destroys the local database. It does not yet create a Token-2022 test mint or run a MOSUL payment/refund round trip. Public faucets may rate-limit shared IP addresses; faucet refusal is not a payment-code success.

Deployment requires `PAYMENT_SERVICE_TOKEN`, `DEVNET_MERCHANT_PUBKEY`, `PAYMENT_DB`, and a reverse proxy providing HTTPS and rate limits. `DEVNET_MOSUL_MINT` must point to a separately created Devnet-only test mint; it must never be set to the Mainnet mint. Automated refunds currently support only the native-SOL Devnet path and require `DEVNET_REFUND_KEYPAIR`, pointing to an owner-managed Devnet-only keypair outside the repository. MOSUL-token refunds are not implemented, and the sale service does not use this prototype yet. Set the artwork pipeline's `MARKET_COMPS_API_URL` to the HTTPS `/comparables` endpoint and `MARKET_COMPS_API_KEY` to the service token. Until five non-refunded completed sales exist, the artwork pipeline displays no benchmark.

This is not production checkout and cannot transfer the Mainnet MOSUL token. It must not be exposed as a public checkout or used for real funds.
