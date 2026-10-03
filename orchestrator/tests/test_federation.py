import unittest

from orchestrator.federation import (
    Council,
    CrossOrgHandoff,
    FederationMember,
    can_delegate,
    can_receive_sensitive_data,
    compatible,
    council_can_bind,
    council_can_create_parallel_command,
    default_autonomy_ceiling,
    validate_handoff,
    expert_commission_requires_verified_capability,
    expert_commission_creates_command_authority,
    expert_commission_may_have_high_epistemic_influence,
)


class FederationTests(unittest.TestCase):
    def setUp(self):
        self.org_a = FederationMember("org-a", "organization", ("0.2", "0.3"), ("research", "review"), "trusted", True)
        self.org_b = FederationMember("org-b", "organization", ("0.3",), ("bim", "review"), "trusted", True)
        self.independent = FederationMember("agent-x", "independent_agent", ("0.3",), ("research",), "limited", False)
        self.incompatible = FederationMember("org-c", "organization", ("9.0",), ("bim",), "trusted", True)

    def test_compatible_constitution_required(self):
        self.assertTrue(compatible(self.org_a, self.org_b))
        self.assertFalse(compatible(self.org_a, self.incompatible))

    def test_delegation_requires_trusted_capability(self):
        self.assertTrue(can_delegate(self.org_a, self.org_b, "bim"))
        self.assertFalse(can_delegate(self.org_a, self.org_b, "legal"))

    def test_unverified_independent_agent_defaults_to_a1(self):
        self.assertEqual(default_autonomy_ceiling(self.independent), "A1")

    def test_limited_independent_agent_cannot_receive_sensitive_data(self):
        self.assertFalse(can_receive_sensitive_data(self.independent))

    def test_handoff_is_bounded_and_requires_provenance(self):
        h = CrossOrgHandoff(
            request_id="X-1",
            requesting_member_id="org-a",
            receiving_member_id="org-b",
            requesting_authority="lead-a",
            capability="bim",
            outcome="Check model",
            autonomy_ceiling="A1",
            acceptance_criteria=("return findings",),
        )
        self.assertTrue(validate_handoff(h)[0])
        self.assertFalse(h.allow_subdelegation)

    def test_council_is_advisory_by_default(self):
        c = Council("C-1", "What path?", "lead-a", ("agent-a", "agent-b"))
        self.assertFalse(council_can_bind(c))
        self.assertFalse(council_can_create_parallel_command(c))

    def test_expert_commission_is_influential_but_not_command(self):
        self.assertTrue(expert_commission_requires_verified_capability())
        self.assertTrue(expert_commission_may_have_high_epistemic_influence())
        self.assertFalse(expert_commission_creates_command_authority())


if __name__ == "__main__":
    unittest.main()
