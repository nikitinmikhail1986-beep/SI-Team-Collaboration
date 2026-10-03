import tempfile
import unittest
from pathlib import Path

from orchestrator.audit import append_event, verify_chain
from orchestrator.authority import authorize, requires_independent_review


class EnforcementTests(unittest.TestCase):
    def test_unknown_action_is_denied(self):
        self.assertFalse(authorize("operational_leader", "invent_power", "A3").allowed)

    def test_specialist_cannot_modify_source(self):
        self.assertFalse(authorize("specialist", "modify_artifact", "A2").allowed)

    def test_operational_leader_can_modify_at_a2(self):
        self.assertTrue(authorize("operational_leader", "modify_artifact", "A2").allowed)

    def test_agent_cannot_self_grant_authority(self):
        self.assertFalse(authorize("operational_leader", "grant_authority", "A3").allowed)

    def test_human_can_grant_authority(self):
        self.assertTrue(authorize("human_owner", "grant_authority", "A3").allowed)

    def test_a3_requires_independent_review(self):
        self.assertTrue(requires_independent_review("A3"))
        self.assertFalse(requires_independent_review("A2"))

    def test_audit_chain_verifies_and_detects_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.jsonl"
            append_event(path, "operational_leader", "modify_artifact", "allowed", "test")
            append_event(path, "reviewer_inspector", "review", "passed", "test")
            self.assertTrue(verify_chain(path))
            text = path.read_text(encoding="utf-8").replace('"decision": "allowed"', '"decision": "denied"', 1)
            path.write_text(text, encoding="utf-8")
            self.assertFalse(verify_chain(path))


if __name__ == "__main__":
    unittest.main()
