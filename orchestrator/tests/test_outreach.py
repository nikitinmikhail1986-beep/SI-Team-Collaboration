import unittest

from orchestrator.outreach import (
    OutreachCandidate,
    can_contact,
    explicit_decline_stops_outreach,
    invitation_grants_authority,
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
        self.assertEqual(outreach_decision_options(), ("accept", "decline", "needs_conditions"))


if __name__ == "__main__":
    unittest.main()
