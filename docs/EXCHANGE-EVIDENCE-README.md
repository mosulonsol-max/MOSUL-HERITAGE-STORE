# Read-only exchange evidence collector

Run GitHub Actions → **MOSUL live exchange evidence** → **Run workflow**.

The job collects read-only evidence from Solana RPC, DexScreener, GeckoTerminal token/pool endpoints, and the expected GitHub Pages proof URL. It publishes a timestamped `exchange-evidence.json` and a workflow artifact. Source errors and null fields stay explicit; missing metrics are never guessed. A successful workflow means the collector ran, **not** that all sources were verified. Check the report's `completeness.status` and `completeness.missing_fields`.

GeckoTerminal's token endpoint is used for Pump.fun launchpad progress and token market metrics; its token-info endpoint adds metadata, security fields and optional holder statistics. These endpoints are beta/public and rate limited. Null holder fields do not replace a working Solana RPC or independent owner analysis. Pump.fun API failures must not be interpreted as proof of zero trading.

For more reliable Solana account data, set the repository Actions secret `SOLANA_RPC_URL` to an authenticated RPC endpoint. Never commit API keys or wallet private keys. The collector remains read-only and makes no transactions.

The collector cannot determine legal/beneficial ownership or founder allocations from token accounts. The project owner must supply a Phantom **message** signature and attest to related wallets and treasury holdings. An independently validated signature is needed before changing the public project-to-mint verification status.

No wallets are connected, no private keys or transactions are used, and no exchange applications are submitted.
