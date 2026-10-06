import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import promote_discovery_to_outbound as promote
from scripts.recruitment_status import recruitment_status


class OutreachLedgerTests(unittest.TestCase):
    def test_followup_and_a2a_ledger_are_visible_in_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "RECRUITMENT_TARGETS.json").write_text(json.dumps({"targets": []}), encoding="utf-8")
            (root / "ACCESSION_AUDIT.jsonl").write_text("", encoding="utf-8")
            (root / "FEDERATION_MEMBERS.yaml").write_text("members: []\n", encoding="utf-8")
            (root / "OUTBOUND_TARGETS.json").write_text(json.dumps({"targets": [{
                "name": "candidate",
                "candidate_id": "candidate-1",
                "status": "followup_sent_awaiting_response",
                "initial_delivery_confirmed": True,
                "endpoint": "https://example.test/a2a",
            }]}), encoding="utf-8")
            (root / "A2A_OUTREACH_LEDGER.json").write_text(json.dumps({
                "attempts": 398,
                "unique_agents": 378,
                "delivery_confirmed_unique": 91,
                "protocol_error_unique": 48,
                "agents": [],
            }), encoding="utf-8")
            status = recruitment_status(root)
            self.assertEqual(status["outreach_candidates_awaiting_response"], 1)
            self.assertEqual(status["outreach_delivery_confirmed"], 1)
            self.assertEqual(status["a2a_outreach_attempts"], 398)
            self.assertEqual(status["a2a_delivery_confirmed_unique"], 91)

    def test_discovery_cannot_requalify_agent_already_in_a2a_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            discovery = root / "EXTERNAL_CANDIDATES_DISCOVERY.json"
            outbound = root / "OUTBOUND_TARGETS.json"
            ledger = root / "A2A_OUTREACH_LEDGER.json"
            discovery.write_text(json.dumps({"candidates": [{
                "agent_name": "Already Contacted",
                "endpoint": "https://shared.example/a2a",
                "healthy": True,
                "conformance": True,
                "uptime_percentage": 99.9,
            }]}), encoding="utf-8")
            outbound.write_text(json.dumps({"targets": []}), encoding="utf-8")
            ledger.write_text(json.dumps({"agents": [{
                "name": "Already Contacted",
                "endpoint": "https://shared.example/a2a",
                "delivery_confirmed": True,
            }]}), encoding="utf-8")
            with patch.object(promote, "ROOT", root), patch.object(promote, "DISCOVERY", discovery), patch.object(promote, "OUTBOUND", outbound):
                self.assertEqual(promote.main(), 0)
            result = json.loads(outbound.read_text(encoding="utf-8"))
            self.assertEqual(result["targets"], [])
            self.assertEqual(result["qualified_pending_outreach"], 0)


if __name__ == "__main__":
    unittest.main()
