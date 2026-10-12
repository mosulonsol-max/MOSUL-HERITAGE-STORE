# Hourly artwork preview pipeline

## What it does

The GitHub Actions workflow is scheduled once per hour and can also be started manually. When configured, it requests one new square concept image from an owner-selected HTTPS image API, validates the PNG, adds a visible MOSUL HERITAGE · PREVIEW · NOT FOR SALE watermark, records the output hash and classification, and adds the result to the public preview catalog. The original unmarked image is not committed to this public repository.

The workflow stores the rolling catalog and preview files on a separate artwork-data branch, assembles them with the project source, and deploys a GitHub Pages artifact. It keeps the 120 newest entries. The schedule is best-effort; GitHub may delay scheduled runs, so it cannot guarantee a new image at the exact start of every hour.

## Safe defaults

- With no image API configuration, the run exits without generating or publishing anything.
- Checkout, payment, delivery, NFT minting, and X posting are not part of this workflow.
- Every output is marked AI-generated contemporary art, not a historical photograph or verified reconstruction.
- Every image is a public preview only. The watermark is a visible label, not a cryptographic signature or proof of ownership.
- The system does not invent a price. It reports a comparable-sales benchmark only when it receives at least five category-matched completed sales from the last 90 days. Listings are not treated as sales. If data is missing or weak, the catalog says the price is unavailable.
- A historical benchmark is not an appraisal, asking price, investment claim, or permission to sell.

## Owner configuration

Add these as GitHub repository Actions secrets. Never put API keys in the repository or in a public issue.

| Secret / variable | Purpose |
| --- | --- |
| ARTWORK_API_URL | Full HTTPS endpoint for an OpenAI-compatible image generation API that accepts prompt, size, n, and response_format and returns data[0].b64_json. |
| ARTWORK_API_KEY | Private bearer key for that image provider. The provider may charge for image generation; the workflow is inert until the owner configures it. |
| ARTWORK_MODEL (Actions variable) | Optional model identifier accepted by the selected provider. |
| MARKET_COMPS_API_URL | Optional owner-selected HTTPS read-only endpoint returning the normalized comparable-sales schema below. |
| MARKET_COMPS_API_KEY | Optional bearer key for the selected comparable-sales source. |

The comparable-sales endpoint must return JSON with a top-level comparables array. Each item must provide category, status, sold_at, price_usd, and source. For example:

    {"comparables":[{"category":"digital-art-one-of-one","status":"sold","sold_at":"2026-10-01T12:00:00Z","price_usd":42.5,"source":"https://market.example/transaction/123"}]}

Only status=sold, an exact category match, a valid timestamp in the 90-day window, and a positive USD amount count. The endpoint owner is responsible for using a source whose completed-sale records and USD conversions can be independently checked. No marketplace integration is claimed until one is configured and its feed is audited.

## GitHub Pages setup

After this workflow is merged to main, choose Settings → Pages → Build and deployment → Source → GitHub Actions. The existing branch-based Pages setup must be switched once so the workflow can deploy its assembled preview. Then configure the provider secrets and run Actions → Hourly artwork preview pipeline → Run workflow. Review the run log and the deployed catalog.html preview before relying on it.

## Before any sale

This pipeline only produces watermarked previews. Commercial release still needs a separately secured private master store, project-approved source and logo rights, signed authenticity and buyer-license records, a verified project-to-token statement, an audited marketplace data source, a real payment and delivery test, and any required wallet-approved mint. None is activated by this workflow.
