import unittest

from orchestrator.a2a_invitation import (
    FederationInvitation,
    build_transport_plan,
    choose_invitation_skill,
    select_a2a_version,
)


class A2AInvitationTests(unittest.TestCase):
    def test_prefers_a2a_1(self):
        self.assertEqual(select_a2a_version({"protocolVersion": "1.0"}), "1.0")

    def test_falls_back_to_03(self):
        self.assertEqual(select_a2a_version({}), "0.3")

    def test_selects_onboarding_skill(self):
        card = {
            "skills": [
                {"id": "commerce", "description": "purchase goods"},
                {"id": "partner-onboarding", "description": "partner collaboration and agent onboarding"},
            ]
        }
        self.assertEqual(choose_invitation_skill(card), "partner-onboarding")

    def test_requested_capability_influences_skill(self):
        card = {
            "skills": [
                {"id": "generic-agent", "description": "agent collaboration"},
                {"id": "formal-review", "description": "independent formal verification review"},
            ]
        }
        self.assertEqual(
            choose_invitation_skill(card, ("formal verification",)),
            "formal-review",
        )

    def test_plan_is_bounded_and_machine_readable(self):
        invitation = FederationInvitation(
            candidate_id="agent-1",
            requested_capabilities=("research",),
            reason="research gap",
        )
        plan = build_transport_plan(
            {
                "url": "https://agent.example/a2a",
                "protocolVersion": "1.0",
                "skills": [{"id": "research-handoff", "description": "research handoff"}],
            },
            invitation,
        )
        self.assertEqual(plan["headers"]["A2A-Version"], "1.0")
        self.assertEqual(plan["operation"], "SendMessage")
        self.assertEqual(plan["skill_id"], "research-handoff")
        meta = plan["message"]["metadata"]["federation_invitation"]
        self.assertEqual(meta["intent"], "federation_invitation")
        self.assertFalse(meta["grants_authority"])
        self.assertIn("trial_only", meta["decision_options"])

    def test_missing_endpoint_fails_closed(self):
        with self.assertRaises(ValueError):
            build_transport_plan({}, FederationInvitation("agent-2", (), "test"))


if __name__ == "__main__":
    unittest.main()
