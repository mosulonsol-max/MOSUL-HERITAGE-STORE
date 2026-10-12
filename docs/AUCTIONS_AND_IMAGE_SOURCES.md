# Licensed source material and auction design

## Image sourcing policy

The generator may use a source image as visual input only when its item-level metadata explicitly permits commercial adaptation. The current connector queries Wikimedia Commons through its MediaWiki API and accepts only CC0, CC BY, or public-domain labels. The generated catalogue stores the source file page, creator, license, and attribution data. CC BY attribution must remain visible with the derivative.

This is an allowlist, not a declaration that every search result is rights-cleared. Metadata can be incomplete or wrong, so an operator must check the source page and the final candidate before any listing. A model's license does not transfer rights in a reference image. A derivative made from a licensed source must not be advertised as exclusive or wholly owned by MOSUL HERITAGE unless a rights review supports that claim.

The project must not crawl arbitrary websites, social networks, private albums, or map tiles. For other platforms, add only an official, permitted API integration that returns item-level license/rights metadata. For mapping inspiration, use open geographic data under its actual attribution and share-alike conditions, or make a new abstract interpretation from facts; do not download visible map tiles and treat them as unlicensed source images. OpenStreetMap and other map-data providers have distinct data, rendering, and tile-service terms.

## Model and execution

The open-weight baseline is FLUX.1-schnell from Black Forest Labs. The official inference-code repository is `https://github.com/black-forest-labs/flux`; the model weights are distributed separately as `black-forest-labs/FLUX.1-schnell`. The model is marked Apache-2.0 and the documented distilled inference path uses four steps. `scripts/generate_flux.py` calls Diffusers' FLUX image-to-image pipeline and falls back to text-to-image when no permitted Commons reference is found. No API key or paid image service is required in this mode.

Local generation needs an owner-managed GPU runner, an installed CUDA-compatible PyTorch build, sufficient GPU or system memory, and the first model download. It cannot run on GitHub Pages. If the self-hosted runner is offline, an hourly scheduled job can wait or be skipped; hourly output is therefore best-effort, not guaranteed. The website receives only the watermarked preview and its provenance record, never an unwatermarked master.

## Auction mechanics

The intended format is a transparent ascending English auction:

1. Each lot publishes its image preview, rights/provenance statement, auction start and close in UTC, opening bid, minimum increment, accepted bid currency, and whether a reserve exists. Any reserve is set before bids open and is not changed during the sale.
2. Bidders authenticate with a wallet or account and submit a signed bid. The server or audited on-chain program validates auction status, currency, increment, bidder eligibility, and ordering. The browser is never the source of truth.
3. The highest valid bid is displayed with a shortened bidder identifier and audit timestamp. Equal amounts are ordered by the first accepted server sequence or chain slot; rejected bids do not move the clock.
4. A bid in the final two minutes extends the closing time by two minutes. This anti-sniping rule is based on published Sotheby's online-auction practice; publish it in every lot's terms before bidding starts.
5. At close, the highest bid wins only if it meets the published reserve. Otherwise the lot is unsold. The winner receives the item only after payment settlement; delivery includes the specified digital file/license and a verifiable receipt.

Opening bids and reserve recommendations can use category-matched completed sales, but auction competition determines the final hammer price. Display evidence count and comparable window. If reliable sales data is missing, the seller chooses the opening bid and reserve explicitly; the system must not invent a valuation.

## Current deployment boundary

The official site is GitHub Pages, which is static hosting. It can display auction results but cannot securely authenticate bidders, enforce a durable globally ordered bid log, escrow cryptocurrency, settle transfers, or grant delivery rights. A client-side or local-storage “auction” would be easy to manipulate and must not be presented as live bidding.

Before enabling live bids, add and audit a persistent backend or a Solana program that handles signed bids and settlement, protect seller reserve configuration, define winner non-payment and refund rules, specify the payment asset, and test the complete flow on a test network. The live auction UI remains disabled until those components and the lot rights records are reviewed. Do not accept funds or mint NFTs as part of this preview-only change.

## Configuration still required

- Settlement asset: native SOL, the verified MOSUL token mint, another token, or more than one asset.
- Auction execution: owner-operated backend with escrow, or an audited non-custodial Solana program.
- Commercial terms: opening bid and reserve per lot, minimum increment schedule, auction duration, winner payment deadline, refund rules, buyer fees, and digital usage rights.

This document captures a safe default auction format; it does not create a live marketplace or prove that any item has exclusive intellectual-property rights.
