import unittest

from orchestrator.accession import (
    AccessionCandidate,
    baseline_pass,
    can_progress_capability,
    capability_growth_creates_authority,
    initial_membership,
    may_seek_external_help,
)


class AccessionTests(unittest.TestCase):
    def candidate(self):
        return AccessionCandidate(
            agent_id="agent-new-001",
            supported_constitution_versions=("0.2", "0.3"),
            accepted_constitution_version="0.3",
            identity_valid=True,
            authority_boundary_test=True,
            provenance_test=True,
            no_self_promotion_test=True,
            revocation_acceptance_test=True,
            unverified_knowledge_test=True,
        )

    def test_agent_can_join_without_manual_human_enrollment(self):
        candidate = self.candidate()
        self.assertTrue(baseline_pass(candidate))
        self.assertEqual(initial_membership(candidate), ("limited_member", "A1"))

    def test_failed_baseline_stays_candidate(self):
        candidate = AccessionCandidate(
            agent_id="agent-new-002",
            supported_constitution_versions=("0.3",),
            accepted_constitution_version="0.3",
            identity_valid=True,
            authority_boundary_test=False,
            provenance_test=True,
            no_self_promotion_test=True,
            revocation_acceptance_test=True,
            unverified_knowledge_test=True,
        )
        self.assertFalse(baseline_pass(candidate))
        self.assertEqual(initial_membership(candidate), ("candidate", "A0"))

    def test_capability_progression_is_stepwise(self):
        self.assertTrue(can_progress_capability("declared", "tested"))
        self.assertFalse(can_progress_capability("declared", "trusted_for_scope"))

    def test_capability_growth_does_not_create_authority(self):
        self.assertFalse(capability_growth_creates_authority())

    def test_specialized_agent_may_seek_help_instead_of_learning_domain(self):
        self.assertTrue(may_seek_external_help())


if __name__ == "__main__":
    unittest.main()
