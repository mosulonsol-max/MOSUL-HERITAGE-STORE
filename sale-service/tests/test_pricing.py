import json
import unittest
from unittest.mock import patch

from core import MOSUL_MINT
from pricing import mosul_usd_quote


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.payload


class PricingTests(unittest.TestCase):
    def test_uses_mosul_base_pair_with_highest_reported_liquidity(self):
        pairs = [
            {"chainId": "solana", "pairAddress": "low", "baseToken": {"address": MOSUL_MINT},
             "quoteToken": {"address": "So11111111111111111111111111111111111111112"},
             "priceUsd": "0.000002", "liquidity": {"usd": 100}},
            {"chainId": "solana", "pairAddress": "high", "baseToken": {"address": MOSUL_MINT},
             "quoteToken": {"address": "So11111111111111111111111111111111111111112"},
             "priceUsd": "0.000003", "liquidity": {"usd": 900}},
            {"chainId": "solana", "pairAddress": "inverse", "baseToken": {"address": "So11111111111111111111111111111111111111112"},
             "quoteToken": {"address": MOSUL_MINT}, "priceUsd": "100000", "liquidity": {"usd": 5000}},
        ]
        with patch("pricing.urllib.request.urlopen", return_value=Response(pairs)):
            quote = mosul_usd_quote()
        self.assertEqual(quote["price_usd"], "0.000003")
        self.assertEqual(quote["pair_address"], "high")
        self.assertEqual(quote["liquidity_usd"], "900.00")
        self.assertEqual(quote["source"], "DEX Screener")
        self.assertTrue(quote["quoted_at"].endswith("+00:00"))

    def test_missing_liquid_market_fails_closed(self):
        with patch("pricing.urllib.request.urlopen", return_value=Response([])):
            with self.assertRaisesRegex(ValueError, "no verified liquid"):
                mosul_usd_quote()


if __name__ == "__main__":
    unittest.main()
