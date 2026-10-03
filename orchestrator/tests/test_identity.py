import unittest

from orchestrator.identity import (
    AgentIdentity,
    continuity_requires_reverification,
    identity_grants_sovereignty,
    record_runtime,
    reputation_grants_authority,
    validate_identity,
)


class IdentityTests(unittest.TestCase):
    def test_identity_requires_agent_id(self):
        identity = AgentIdentity("", "Reviewer One", "reviewer_inspector")
        self.assertFalse(validate_identity(identity)[0])

    def test_identity_does_not_create_sovereignty(self):
        identity = AgentIdentity("agent-001", "Reviewer One", "reviewer_inspector")
        self.assertFalse(identity_grants_sovereignty(identity))

    def test_reputation_does_not_create_authority(self):
        identity = AgentIdentity("agent-001", "Reviewer One", "reviewer_inspector")
        identity.reputation_evidence.append({"capability": "review", "result": "verified"})
        self.assertFalse(reputation_grants_authority(identity))

    def test_runtime_history_preserves_identity(self):
        identity = AgentIdentity("agent-001", "Reviewer One", "reviewer_inspector")
        record_runtime(identity, provider="provider-a", model="model-1", session_or_run_id="run-1")
        record_runtime(identity, provider="provider-b", model="model-2", session_or_run_id="run-2")
        self.assertEqual(identity.agent_id, "agent-001")
        self.assertEqual(len(identity.runtime_history), 2)

    def test_model_change_requires_reverification(self):
        self.assertTrue(continuity_requires_reverification("model-1", "model-2"))
        self.assertFalse(continuity_requires_reverification("model-1", "model-1"))


if __name__ == "__main__":
    unittest.main()
