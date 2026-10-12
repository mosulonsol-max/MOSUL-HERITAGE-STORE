# Hourly artwork preview pipeline

## What it does

A GitHub Actions workflow runs once an hour and can be started manually from main. When an owner configures an HTTPS image API, it requests one square concept image, validates it, adds a visible MOSUL HERITAGE · PREVIEW · NOT FOR SALE watermark, and publishes its hash and AI-art classification in the preview catalog. Unmarked masters are not committed publicly. The rolling catalog and watermarked previews live on a separate artwork-data branch; the workflow assembles and deploys a GitHub Pages artifact. It retains the 120 newest entries. GitHub scheduling is best-effort and cannot guarantee an exact hourly publication.

## Safe defaults

- Without image API configuration, no image is generated or published.
- The provider may charge for image generation. No service is configured by this workflow.
- Checkout, payment, delivery, NFT minting, and X posting are not included.
- Each output is labeled AI-generated contemporary art, not historical evidence or a verified reconstruction. The visible watermark is not a signature or proof of ownership.
- Price is shown only as a historical comparable-sales benchmark after at least five valid, category-matched sales in the last 90 days. Listings do not count as sales. Weak or missing data is shown as unavailable.

## Owner configuration

Set these in the repository's Actions secrets and variables. Never place API keys in source files or public issues.

| Secret / variable | Purpose |
| --- | --- |
| ARTWORK_API_URL | HTTPS endpoint for an OpenAI-compatible image API that accepts prompt, size, n, response_format and returns data[0].b64_json. |
| ARTWORK_API_KEY | Private bearer key for the image provider. |
| ARTWORK_MODEL (Actions variable) | Optional provider model identifier. |
| MARKET_COMPS_API_URL | Optional HTTPS read-only endpoint returning the comparable-sales schema below. |
| MARKET_COMPS_API_KEY | Optional bearer key for that source. |

The comparables endpoint returns a JSON top-level comparables array. Each record needs a unique transaction_id, category, status, sold_at, price_usd, and source:

    {"comparables":[{"transaction_id":"sale-123","category":"digital-art-one-of-one","status":"sold","sold_at":"2026-10-01T12:00:00Z","price_usd":42.5,"source":"https://market.example/transaction/123"}]}

Only unique IDs with status=sold, an exact category match, a valid timestamp in the 90-day window, and a positive finite USD price count. The public catalog retains source hostnames only. The endpoint owner must verify transaction records and currency conversions. No marketplace integration is claimed until a source is configured and audited.

## GitHub Pages setup

After merging to main, choose Settings → Pages → Build and deployment → Source → GitHub Actions. This switches the existing branch-based Pages deployment. Then configure the provider secrets and start Actions → Hourly artwork preview pipeline → Run workflow. Review the workflow log and deployed catalog before relying on it.

## Before any sale

This workflow only publishes previews. Any commercial release requires a private master store, approved source and logo rights, signed authenticity and buyer-license records, a verified project-to-token statement, an audited marketplace data source, payment and delivery testing, and any required wallet-approved mint. None is enabled here.
