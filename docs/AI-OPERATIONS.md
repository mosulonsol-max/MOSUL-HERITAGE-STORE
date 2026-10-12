# AI operations and readiness

Last reviewed: 12 October 2026.

## Readiness matrix

| Component | State | What exists | What is still required |
| --- | --- | --- | --- |
| GitHub control | Ready | ChatGPT Codex Connector installed for all repositories with repository read/write access | Keep account MFA enabled and review the installation periodically |
| Governed AI engine | Ready in code | Ollama/Qwen client, capability registry, deterministic policy, fixed adapters, JSONL audit | A runner with Ollama if model planning is enabled |
| Hourly generation | Ready in code | GitHub schedule, guarded orchestration, catalog persistence, Pages artifact | Select and configure an image backend; GitHub schedules run at best-effort times |
| Local open-source image model | Ready in code | FLUX runner and dependency profile | Owner-managed Linux x64 GPU runner labeled `self-hosted`, `linux`, `x64`, `gpu` |
| Heritage references | Partial | Narrow Wikimedia Commons reference lookup and provenance fields | Human source review, a curated source allow-list, and expanded institutional sources |
| Integrity and provenance | Configured | UUID, SHA-256, visible watermark, canonical Ed25519 signing and verification; `ARTWORK_SIGNING_KEY_B64` is stored as an Actions secret | Verify the first generated signed preview on the GPU runner |
| Comparable-sales benchmark | Ready in code | First-party finalized, non-refunded sales ledger; rejects stale/insufficient evidence | Deploy the Devnet payment service behind HTTPS; no benchmark appears before five completed sales |
| X publishing | Existing queue workflow | OAuth-based publisher and reviewable queue | Valid X secrets and a non-empty approved queue |
| Telegram publishing | Existing workflow | Bot publishing path | `TELEGRAM_BOT_TOKEN`, destination chat ID, and an end-to-end test |
| Auction bids | Prototype only | Signed-bid ledger design and pause controls | Persistent service, HTTPS, abuse limits, backup/recovery, buyer terms, UI, and security review |
| Checkout and settlement | Devnet rehearsal only | Exact finalized native-SOL Devnet payments, idempotent settlement, refund capability, automated refund processor | Deployment host, live faucet-funded rehearsal, independent audit, delivery, accounting, and legal review |
| NFT minting | Disabled | Policy gate and provenance inputs | Devnet adapter and tests first; owner approval is required for each financial test |

## Configuration

Repository variables:

- `AI_PLANNER_ENABLED`: `1` only on a runner that can reach Ollama; otherwise `0`.
- `OLLAMA_BASE_URL`: normally `http://127.0.0.1:11434` on a self-hosted runner. Remote endpoints must use HTTPS.
- `OLLAMA_MODEL`: defaults to `qwen2.5:7b-instruct`.
- `ARTWORK_BACKEND`: `flux-local` or `openai-compatible`.
- `ARTWORK_MODEL` and `ARTWORK_REFERENCE_QUERY`: optional model and curated search settings.

Actions secrets:

- `ARTWORK_SIGNING_KEY_B64`: base64 encoding of one raw 32-byte Ed25519 private seed.
- `ARTWORK_API_URL` and `ARTWORK_API_KEY`: only for an owner-approved image API.
- `MARKET_COMPS_API_URL` and `MARKET_COMPS_API_KEY`: only for a lawful completed-sales source.
- Social publisher credentials documented by their existing workflows.

Never commit these secrets, a wallet seed phrase, buyer data, or unwatermarked private masters. GitHub repository write access does not grant the AI permission to spend funds. Mainnet and real-value operations remain blocked.

## Activation order

1. Merge the reviewed pull request after the governance check is green.
2. Configure a self-hosted GPU runner and Ollama/Qwen if local planning and FLUX are required.
3. Add the Ed25519 secret through GitHub Actions secrets and verify one signed preview.
4. Configure a lawful comparable-sales feed and confirm the benchmark stays unavailable when evidence is insufficient.
5. Run X and Telegram end-to-end tests with reviewable queues.
6. Build and independently review Devnet-only checkout, settlement, refunds, and delivery before considering any production financial action.
