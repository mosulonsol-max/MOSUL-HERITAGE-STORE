# MOSUL AI engine

This is a local, open-source-compatible orchestration layer for MOSUL HERITAGE. Qwen runs through Ollama and may propose only actions listed in `config/ai-capabilities.json`. Deterministic Python policy checks authorize every action before a fixed adapter runs; the model never receives a shell, wallet key, GitHub token, or arbitrary network tool.

## Run locally

```bash
ollama pull qwen2.5:7b-instruct
AI_PLANNER_ENABLED=1 python ai-engine/run_agent.py --output-dir data
python -m unittest discover -s ai-engine/tests -v
```

With `AI_PLANNER_ENABLED=0` the engine uses the deterministic hourly preview action, so CI does not depend on a hosted language-model API. A remote Ollama endpoint must use HTTPS; localhost HTTP is accepted.

## Safety boundary

- Mainnet and real-value financial actions fail closed.
- Devnet financial tests require an explicit manual approval context.
- Unknown actions and missing adapters are denied and audited.
- Source claims are stored with retrieval time and SHA-256, but remain labeled as not independently verified.
- Social actions are queues only and require an approved channel.
- Checkout, auction settlement, NFT minting, and token transfers are not live.

The audit log is JSON Lines and must not contain credentials or personal buyer data.
