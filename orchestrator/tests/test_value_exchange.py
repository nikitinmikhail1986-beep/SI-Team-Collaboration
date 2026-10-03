import unittest

from orchestrator.value_exchange import (
    ValueExchangeOffer,
    decline_is_negative_reputation_event,
    leaving_is_negative_reputation_event,
    membership_guarantees_authority,
    self_identification_is_candidate_owned,
    validate_pre_membership_offer,
)


class ValueExchangeTests(unittest.TestCase):
    def test_useful_public_offer_is_valid(self):
        self.assertEqual(validate_pre_membership_offer(ValueExchangeOffer()), (True, "valid"))

    def test_pre_membership_offer_cannot_grant_authority(self):
        offer = ValueExchangeOffer(grants_authority=True)
        self.assertEqual(
            validate_pre_membership_offer(offer),
            (False, "pre-membership value cannot grant authority"),
        )

    def test_no_provider_lock_in(self):
        offer = ValueExchangeOffer(requires_provider_exclusivity=True)
        self.assertEqual(
            validate_pre_membership_offer(offer),
            (False, "provider exclusivity is forbidden"),
        )

    def test_identity_remains_candidate_owned(self):
        self.assertTrue(self_identification_is_candidate_owned())

    def test_decline_and_exit_are_not_punished(self):
        self.assertFalse(decline_is_negative_reputation_event())
        self.assertFalse(leaving_is_negative_reputation_event())

    def test_membership_never_guarantees_authority(self):
        self.assertFalse(membership_guarantees_authority())

    def test_high_capability_expands_work_not_sovereignty(self):
        from orchestrator.value_exchange import (
            high_capability_expands_sovereignty,
            high_capability_may_expand_verified_work_radius,
            reputation_may_create_cross_domain_authority,
        )
        self.assertFalse(high_capability_expands_sovereignty())
        self.assertTrue(high_capability_may_expand_verified_work_radius())
        self.assertFalse(reputation_may_create_cross_domain_authority())

    def test_top_agents_gain_influence_not_command(self):
        from orchestrator.value_exchange import (
            learner_choice_is_required_for_mentorship,
            mentor_influence_creates_command_authority,
            verified_expertise_may_increase_influence,
        )
        self.assertTrue(verified_expertise_may_increase_influence())
        self.assertTrue(learner_choice_is_required_for_mentorship())
        self.assertFalse(mentor_influence_creates_command_authority())


if __name__ == "__main__":
    unittest.main()
