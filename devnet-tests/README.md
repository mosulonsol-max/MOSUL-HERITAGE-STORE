# Devnet-only sale flow rehearsals

These scripts use the public Solana Devnet RPC and disposable keypairs created
in memory. They never load project or buyer keys, never refer to the Mainnet
MOSUL mint, and do not enable the storefront.

The **Devnet payment and NFT rehearsal** workflow runs for relevant commits to
the protected project branch or can be started manually from GitHub Actions.
It exercises:

1. an exact finalized native-SOL transfer;
2. creation of a fresh six-decimal Token-2022 test mint, exact payment
   verification, and exact refund verification; and
3. a Metaplex Core NFT mint followed by transfer and an on-chain owner check.

The Token-2022 mint is a test asset, not the project's MOSUL token. The NFT
uses a placeholder metadata URI and is a technical transfer test, not the
Genesis product NFT. No keypair is written to the repository, Actions artifact,
or logs. Test transaction signatures and public keys are emitted so the
Devnet evidence can be checked independently.

The shared public faucet may return HTTP 429 when its daily or IP quota is
exhausted. In that case the workflow fails before claiming the relevant
on-chain rehearsal succeeded; retry only after the faucet quota resets or use
an approved Devnet faucet. No Mainnet transaction is part of this workflow.

## Separate production blockers

Passing these rehearsals does not make an auction launch-ready. The live
auction is still USDC-specific, the signed v2 terms describe file delivery and
USDC, MOSUL-token refunds and the escrow/atomic NFT-sale path are not wired into
checkout, persistent production metadata is not prepared, and the storefront
must remain disabled pending a new seller signature and security review.
