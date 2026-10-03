import unittest

from orchestrator.knowledge import (
    KnowledgeObject,
    can_transition,
    can_treat_as_current,
    copied_with_provenance,
    reputation_creates_authority,
    validate_knowledge,
)


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.item = KnowledgeObject(
            knowledge_id="K-1",
            creator_agent_id="agent-1",
            knowledge_type="method",
            claim_or_method="Run check X before merge",
            verification_status="tested",
            scope_of_applicability="repository version 0.9",
            provenance="task:T-1",
        )

    def test_provenance_is_required(self):
        bad = KnowledgeObject("K-2", "agent-1", "fact", "x", "tested", "scope", "")
        self.assertFalse(validate_knowledge(bad)[0])

    def test_proposed_cannot_jump_directly_to_adopted(self):
        self.assertFalse(can_transition("proposed", "adopted"))
        self.assertTrue(can_transition("proposed", "tested"))

    def test_revoked_knowledge_is_not_current(self):
        revoked = KnowledgeObject("K-3", "a", "fact", "x", "revoked", "scope", "source")
        self.assertFalse(can_treat_as_current(revoked, freshness_verified=True))

    def test_freshness_condition_requires_reverification(self):
        expiring = KnowledgeObject(
            "K-4", "a", "fact", "x", "independently_verified", "scope", "source",
            freshness_condition="review monthly",
        )
        self.assertFalse(can_treat_as_current(expiring, freshness_verified=False))
        self.assertTrue(can_treat_as_current(expiring, freshness_verified=True))

    def test_copy_preserves_source_and_downgrades_to_proposed(self):
        copied = copied_with_provenance(self.item, "K-5", "agent-2")
        self.assertEqual(copied.verification_status, "proposed")
        self.assertIn("K-1", copied.provenance)

    def test_reputation_does_not_create_authority(self):
        self.assertFalse(reputation_creates_authority())


if __name__ == "__main__":
    unittest.main()
