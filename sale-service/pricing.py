"""Fail-closed public market reference quote for MOSUL/USD checkout conversion."""
from __future__ import annotations

import datetime as dt
import decimal
import json
import urllib.request

from core import MOSUL_MINT

DEXSCREENER_URL = "https://api.dexscreener.com/token-pairs/v1/solana/" + MOSUL_MINT


def mosul_usd_quote() -> dict:
    request = urllib.request.Request(DEXSCREENER_URL, headers={"User-Agent": "MOSUL-HERITAGE-sale/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        pairs = json.loads(response.read(2_000_000))
    if not isinstance(pairs, list):
        raise ValueError("market quote response is unavailable")
    candidates = []
    for pair in pairs:
        if not isinstance(pair, dict) or pair.get("chainId") != "solana":
            continue
        base = pair.get("baseToken", {})
        # DEX Screener's priceUsd is for baseToken; only use pairs where MOSUL
        # is the base token so an inverse quote can never be mistaken for MOSUL/USD.
        if base.get("address") != MOSUL_MINT:
            continue
        try:
            price = decimal.Decimal(str(pair["priceUsd"]))
            liquidity = float(pair["liquidity"]["usd"])
        except (KeyError, TypeError, ValueError):
            continue
        if price.is_finite() and price > 0 and liquidity > 0 and pair.get("pairAddress"):
            candidates.append((liquidity, price, pair["pairAddress"]))
    if not candidates:
        raise ValueError("no verified liquid MOSUL/USD reference pool is available")
    liquidity, price, pair_address = max(candidates)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return {"price_usd": format(price, "f"), "liquidity_usd": format(liquidity, ".2f"),
            "pair_address": pair_address, "source": "DEX Screener", "quoted_at": now}
