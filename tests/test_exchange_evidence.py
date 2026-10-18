import copy
import unittest

from scripts.verify_exchange_evidence import completeness_status


class ExchangeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = {"sources": {
            "rugcheck_report": {"reported_total_holders": 2, "top_token_accounts": [
                {"address": "account-one", "amount": 9007199254740993},
                {"address": "account-two", "amount": 50},
            ]},
            "largest_token_accounts": [
                {"address": "account-two", "amount": "50"},
                {"address": "account-one", "amount": "9007199254740993"},
            ],
            "pumpfun_coin": {"fields": {"launchpad_details": {"completed": False},
                                         "price_usd": "0.00001", "volume_usd": {"h24": "0.0"}}},
            "gecko_pools": [{"address": "pool-one"}],
        }}

    def test_exact_accounts_and_raw_balances_agree_regardless_of_rank(self):
        result = completeness_status(self.report)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["holder_distribution_reconciliation"]["status"], "matched")
        self.assertEqual(result["observed_volume_24h_usd"], "0.0")

    def test_changed_balance_or_account_keeps_evidence_partial(self):
        for field, value in (("amount", "9007199254740992"), ("address", "replacement")):
            report = copy.deepcopy(self.report)
            report["sources"]["largest_token_accounts"][1][field] = value
            result = completeness_status(report)
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["holder_distribution_reconciliation"]["status"], "conflict")

    def test_missing_empty_duplicate_and_inexact_accounts_are_not_complete(self):
        for accounts in (None, [], [{"address": "a", "amount": 1.5}],
                         [{"address": "a", "amount": "1"}, {"address": "a", "amount": "1"}]):
            with self.subTest(accounts=accounts):
                report = copy.deepcopy(self.report)
                report["sources"]["largest_token_accounts"] = accounts
                result = completeness_status(report)
                self.assertEqual(result["status"], "partial")
                self.assertNotEqual(result["holder_distribution_reconciliation"]["status"], "matched")


if __name__ == "__main__":
    unittest.main()
