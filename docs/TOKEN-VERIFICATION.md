# MOSUL Token — On-Chain Verification Record

**Checked:** 12 October 2026 (UTC+3)  
**Network:** Solana mainnet  
**Status (updated 18 October 2026):** Mint configuration observed on-chain; the public project-to-mint wallet statement was independently verified on 17 October. Legal identity and third-party beneficial ownership remain outside this proof.

## Verified account

- **Mint:** `6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump`
- **Token name / symbol shown by Solscan:** Mosul / MOSUL
- **Owner program:** Token-2022 (program ID `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`)
- **Current supply shown:** 1,000,000,000 MOSUL
- **Decimals shown:** 6
- **Mint authority:** N/A on the explorer
- **Freeze authority:** N/A on the explorer
- **Update authority:** N/A on the explorer
- **Token Extensions:** Solscan showed TRUE; the later RPC snapshot enumerated `metadataPointer` and `tokenMetadata`.
- **Creator shown by Solscan:** `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu`

These are explorer observations for this mint at the check date. The mint address identifies the token account; it is not a wallet or a payment destination. Do not send funds to it.

## Primary explorer record

[Open the MOSUL mint on Solscan](https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump)

The page identifies the mint, reports its supply and decimals, lists Token-2022 as the owner program, and displays N/A for mint, freeze, and update authorities. Explorer labels and indexed data are useful references; users can independently inspect the account and its transactions on Solana.

## What this proves—and what it does not

This record documents the on-chain identity and configuration visible for the mint above. It supports the statements that the token is represented by a Token-2022 mint, has six decimals and a displayed supply of one billion, and that the explorer reports no mint, freeze, or update authority.

The original explorer snapshot alone does **not** prove that the mint is issued or controlled by MOSUL HERITAGE, or that the project has a treasury, allocation, lock, burn, or vesting arrangement. The separate signed statement below establishes wallet control and the project's declaration identifying this mint; it does not verify legal identity or ownership of other wallets. MOSUL payments, an NFT, and product sales are not active. No custom MOSUL smart-contract program or source code is identified here. Token-2022 is the shared Solana token program, not a project-specific contract.

## Project-binding gate

On 17 October 2026, wallet `EpFkymuvH8XGq1CWfRtGE1XJUFAjAwUZy5oby5v8Qhxu` signed a statement naming the exact mint, network, signer and MOSUL HERITAGE project. The [public proof JSON](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json) was independently checked using Ed25519 and verified again on 18 October 2026. The signature establishes that the holder of the wallet's private key signed that project declaration. It does not verify the signer's civil identity, other token holders, team members, or the legal authority to bind another person.

The Solana RPC snapshot of 17–18 October enumerates `metadataPointer` and `tokenMetadata` extensions with null metadata update authority, plus null mint and freeze authorities. See the [timestamped machine evidence](https://github.com/mosulonsol-max/MOSUL-HERITAGE-STORE/blob/exchange-evidence-data/exchange-evidence.json) for source data and errors; the holder-distribution RPC query remains rate-limited.

## References

- [Solscan: MOSUL mint](https://solscan.io/token/6Asbjq8icEZi4XdKKsoT7vA23NaLECyGfWQYuF57pump)
- [Solana token documentation](https://solana.com/docs/tokens)
- [Solana Token-2022 documentation](https://solana.com/docs/tokens/extensions)
- [Signed project-to-mint statement](MOSUL-WALLET-PROOF-VERIFIED-2026-10-17.json)
