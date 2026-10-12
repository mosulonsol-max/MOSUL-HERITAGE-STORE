# Solana Devnet payment rehearsal

This service creates idempotent native-SOL Devnet payment intents, verifies exact finalized transfers, settles a first-party completed-sales record, accepts a one-time refund capability, and processes refunds automatically with a dedicated Devnet keypair. It cannot select Mainnet: the RPC URL is fixed in code.

Run tests:

```bash
PYTHONPATH=payment-service python -m unittest discover -s payment-service/tests -v
```

Run the optional live rehearsal:

```bash
python -m pip install -r payment-service/requirements-devnet-test.txt
PYTHONPATH=payment-service python payment-service/live_devnet_test.py
```

The live rehearsal creates ephemeral wallets, requests Devnet SOL, sends an exact transfer with a unique memo, verifies it through a separate RPC read, and destroys the local database. Public faucets may rate-limit shared IP addresses; faucet refusal is not a payment-code success.

Deployment requires `PAYMENT_SERVICE_TOKEN`, `DEVNET_MERCHANT_PUBKEY`, `PAYMENT_DB`, and a reverse proxy providing HTTPS and rate limits. Automated refunds additionally require `DEVNET_REFUND_KEYPAIR`, pointing to an owner-managed Devnet-only keypair outside the repository. Set the artwork pipeline's `MARKET_COMPS_API_URL` to the HTTPS `/comparables` endpoint and `MARKET_COMPS_API_KEY` to the service token. Until five non-refunded completed sales exist, the artwork pipeline displays no benchmark.

This is not production checkout and cannot transfer the Mainnet MOSUL token.
