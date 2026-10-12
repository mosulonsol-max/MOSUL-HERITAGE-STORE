import json
import base64
import tempfile
import unittest
from pathlib import Path

from mosul_ai.capabilities import implemented_actions, load_registry
from mosul_ai.facts import append_fact, make_fact
from mosul_ai.orchestrator import Orchestrator
from mosul_ai.policy import authorize
from mosul_ai.provenance import sign_record, verify_record


class PolicyTests(unittest.TestCase):
    def test_preview_allowed(self): self.assertTrue(authorize("generate_preview").allowed)
    def test_unknown_denied(self): self.assertFalse(authorize("arbitrary_shell").allowed)
    def test_mainnet_denied(self): self.assertEqual(authorize("mint_nft", {"network": "mainnet", "manual_approval": True}).code, "DENY_MAINNET")
    def test_real_value_denied(self): self.assertEqual(authorize("transfer_token", {"network": "devnet", "manual_approval": True, "real_value": True}).code, "DENY_REAL_VALUE")
    def test_devnet_needs_approval(self): self.assertEqual(authorize("mint_nft", {"network": "devnet"}).code, "DENY_NO_APPROVAL")
    def test_devnet_approved(self): self.assertTrue(authorize("mint_nft", {"network": "devnet", "manual_approval": True}).allowed)
    def test_unapproved_channel_denied(self): self.assertFalse(authorize("queue_social_post", {"public_publish": True}).allowed)


class EvidenceTests(unittest.TestCase):
    def test_fact_hash(self):
        fact = make_fact("A claim", "https://example.org/source", "evidence", "2026-01-01T00:00:00Z")
        self.assertEqual(len(fact["source_sha256"]), 64)
    def test_http_fact_denied(self):
        with self.assertRaises(ValueError): make_fact("A", "http://example.org", "B")
    def test_append_fact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "facts.jsonl"
            append_fact(path, make_fact("A", "https://example.org", "B"))
            self.assertEqual(len(path.read_text().splitlines()), 1)


class RegistryTests(unittest.TestCase):
    def test_registry_and_orchestrator(self):
        with tempfile.TemporaryDirectory() as folder:
            registry = Path(folder) / "registry.json"
            audit = Path(folder) / "audit.jsonl"
            registry.write_text(json.dumps({"capabilities": [{"name": "generate_preview", "status": "implemented"}]}))
            loaded = load_registry(registry)
            self.assertEqual(implemented_actions(loaded), ["generate_preview"])
            called = []
            engine = Orchestrator(registry, audit)
            self.assertEqual(engine.run("preview", {"generate_preview": lambda _: called.append(True) or 0}), 0)
            self.assertEqual(called, [True])
            self.assertIn("ALLOW_REVERSIBLE", audit.read_text())
    def test_duplicate_registry_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "r.json"
            path.write_text(json.dumps({"capabilities": [{"name": "x", "status": "implemented"}, {"name": "x", "status": "partial"}]}))
            with self.assertRaises(ValueError): load_registry(path)


class ProvenanceTests(unittest.TestCase):
    def test_ed25519_round_trip_and_tamper(self):
        record = {"id": "MH-1", "sha256": "abc"}
        record["provenance_signature"] = sign_record(record, base64.b64encode(bytes(range(32))).decode())
        self.assertTrue(verify_record(record))
        record["sha256"] = "changed"
        self.assertFalse(verify_record(record))


if __name__ == "__main__":
    unittest.main()
