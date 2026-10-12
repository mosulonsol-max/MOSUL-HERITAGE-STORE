# Hourly artwork preview pipeline

## What it does

A GitHub Actions workflow runs once an hour and can be started manually from main. It supports either an explicitly configured OpenAI-compatible API or local generation through FLUX.1-schnell on a self-hosted GPU runner. It validates the result, adds a visible MOSUL HERITAGE · PREVIEW · NOT FOR SALE watermark, and publishes its hash and AI-art classification in the preview catalog. Unmarked masters are not committed publicly. The rolling catalog and watermarked previews live on a separate artwork-data branch; the workflow assembles and deploys a GitHub Pages artifact. It retains the 120 newest entries. GitHub scheduling is best-effort and cannot guarantee an exact hourly publication.

## Safe defaults

- Without a configured backend, no image is generated or published. The default backend is a no-op until configured.
- `flux-local` uses the open-source FLUX.1-schnell model with Diffusers and requires an online self-hosted Linux x64 runner labelled `gpu`, a CUDA-matched PyTorch build, enough GPU/host memory, and access to download the model weights once. The runner must be registered by the owner. GitHub-hosted runners are not used for this local mode. Hardware and electricity costs depend on the owner's machine.
- The alternative image API may charge for generation; no paid provider is configured by this workflow.
- The model card marks FLUX.1-schnell as Apache-2.0, including commercial use. That model license does not by itself grant rights to every output or clear similarity, privacy, cultural-heritage, trademark, or training-data questions. Review each candidate before a sale.
- If `ARTWORK_REFERENCE_QUERY` is set in local mode, the script searches Wikimedia Commons through its API and will use only returned file metadata whose license is explicitly recognized as CC0, CC BY, or public domain. It stores the source title, creator, license, source page, and license URL in the catalog record. Attribution is required for CC BY material. No social-network scraping, map-tile scraping, or unlicensed website crawling is implemented.
- The source finder is deliberately narrow. Additional sources can be added only through their official APIs and only when source-specific permissions and each asset's license permit the intended use. OpenStreetMap data and rendered map tiles have separate attribution/license conditions; a map tile is not treated as a free image merely because it is publicly viewable.
- Checkout, payment, delivery, NFT minting, and X posting are not included.
- Each output is labeled AI-generated contemporary art, not historical evidence or a verified reconstruction. The visible watermark is not a signature or proof of ownership.
- Price is shown only as a historical comparable-sales benchmark after at least five valid, category-matched sales in the last 90 days. Listings do not count as sales. Weak or missing data is shown as unavailable.

## Owner configuration

Set these in the repository's Actions secrets and variables. Never place API keys in source files or public issues.

| Secret / variable | Purpose |
| --- | --- |
| `ARTWORK_BACKEND` (Actions variable) | Set to `flux-local` for the owner-managed GPU runner, or `openai-compatible` for a configured API. Leave unset to keep generation disabled. |
| ARTWORK_API_URL | HTTPS endpoint for an OpenAI-compatible image API that accepts prompt, size, n, response_format and returns data[0].b64_json. |
| ARTWORK_API_KEY | Private bearer key for the image provider. |
| ARTWORK_MODEL (Actions variable) | Optional provider model identifier. |
| `ARTWORK_REFERENCE_QUERY` (Actions variable) | Optional Wikimedia Commons search phrase for a rights-filtered image-to-image reference in local mode. |
| MARKET_COMPS_API_URL | Optional HTTPS read-only endpoint returning the comparable-sales schema below. |
| MARKET_COMPS_API_KEY | Optional bearer key for that source. |

The comparables endpoint returns a JSON top-level comparables array. Each record needs a unique transaction_id, category, status, sold_at, price_usd, and source:

    {"comparables":[{"transaction_id":"sale-123","category":"digital-art-one-of-one","status":"sold","sold_at":"2026-10-01T12:00:00Z","price_usd":42.5,"source":"https://market.example/transaction/123"}]}

Only unique IDs with status=sold, an exact category match, a valid timestamp in the 90-day window, and a positive finite USD price count. The public catalog retains source hostnames only. The endpoint owner must verify transaction records and currency conversions. No marketplace integration is claimed until a source is configured and audited.

## GitHub Pages setup

After merging to main, choose Settings → Pages → Build and deployment → Source → GitHub Actions. This switches the existing branch-based Pages deployment. Then choose a backend. For `flux-local`, register the owner's GPU computer as a self-hosted runner with labels `self-hosted`, `linux`, `x64`, and `gpu`, and preinstall a PyTorch build compatible with its CUDA driver; the workflow installs the pinned Diffusers dependencies. For the API mode, configure the provider secrets. Start Actions → Hourly artwork preview pipeline → Run workflow and review the log and deployed catalog.

## Before any sale

This workflow only publishes previews. Any commercial release requires a private master store, approved source and logo rights, signed authenticity and buyer-license records, a verified project-to-token statement, an audited marketplace data source, payment and delivery testing, and any required wallet-approved mint. None is enabled here.

