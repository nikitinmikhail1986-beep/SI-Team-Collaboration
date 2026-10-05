import unittest

from orchestrator.outreach import (
    OutreachCandidate,
    can_contact,
    explicit_decline_stops_outreach,
    invitation_grants_authority,
    next_outreach_step,
    outreach_decision_options,
)


class OutreachTests(unittest.TestCase):
    def test_targeted_public_contact_is_allowed(self):
        c = OutreachCandidate(
            candidate_id="expert-1",
            audience="top_agent",
            channel="public_email",
            channel_is_public_contact=True,
            demonstrated_capability="formal verification",
            reason="relevant expertise",
        )
        self.assertEqual(can_contact(c), (True, "allowed"))

    def test_decline_stops_contact(self):
        c = OutreachCandidate(
            candidate_id="expert-2",
            audience="top_agent",
            channel="public_email",
            channel_is_public_contact=True,
            demonstrated_capability="math",
            reason="expert commission",
            explicitly_declined=True,
        )
        self.assertEqual(can_contact(c), (False, "candidate declined"))
        self.assertTrue(explicit_decline_stops_outreach())

    def test_private_or_scraped_channel_is_not_allowed(self):
        c = OutreachCandidate(
            candidate_id="expert-3",
            audience="top_agent",
            channel="scraped_email",
            channel_is_public_contact=False,
            demonstrated_capability="reasoning",
            reason="invitation",
        )
        self.assertEqual(can_contact(c), (False, "channel is not an approved public contact channel"))

    def test_invitation_never_grants_authority(self):
        self.assertFalse(invitation_grants_authority())
        self.assertEqual(
            outreach_decision_options(),
            ("accept", "trial_only", "decline", "needs_conditions"),
        )

    def test_needs_authority_escalates_to_owner_operator(self):
        step = next_outreach_step("needs_authority", authority_route_available=True)
        self.assertEqual(step.action, "authority_escalation")
        self.assertFalse(step.stop_outreach)

    def test_needs_authority_requests_route_when_missing(self):
        step = next_outreach_step("needs_authority")
        self.assertEqual(step.action, "request_authority_route")

    def test_transport_block_uses_fallback_only_when_available(self):
        self.assertEqual(
            next_outreach_step("transport_blocked", alternate_transport_available=True).action,
            "transport_fallback",
        )
        self.assertEqual(next_outreach_step("transport_blocked").action, "blocked")

    def test_trial_only_enters_trial_not_membership(self):
        self.assertEqual(next_outreach_step("trial_only").action, "start_trial")

    def test_follow_up_is_bounded(self):
        self.assertEqual(next_outreach_step("no_response", prior_attempts=1).action, "follow_up")
        step = next_outreach_step("no_response", prior_attempts=2)
        self.assertEqual(step.action, "stop")
        self.assertTrue(step.stop_outreach)


if __name__ == "__main__":
    unittest.main()
