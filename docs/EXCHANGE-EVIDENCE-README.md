# Read-only exchange evidence collector

Run GitHub Actions → **MOSUL read-only exchange evidence** → **Run workflow**.

The job queries public Solana RPC, DexScreener and the expected GitHub Pages proof URL, producing a timestamped `exchange-evidence.json` as a workflow artifact. All network failures are recorded explicitly; missing metrics must never be filled in with guesses. A successful workflow means the script ran, **not** that all sources were verified.

It cannot determine legal/beneficial ownership or founder allocations from token accounts. The project owner must supply a Phantom **message** signature and attest to related wallets and treasury holdings. An independently validated signature is needed before changing the public project-to-mint verification status.

No wallets are connected, no secrets are used, and no transactions or exchange applications are submitted.
