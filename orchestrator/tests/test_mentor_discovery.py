import unittest

from orchestrator.mentor_discovery import (
    MentorCandidate,
    MentorSearchRequest,
    find_verified_mentors,
    route_mentor_gap,
)


class MentorDiscoveryTests(unittest.TestCase):
    def test_verified_mentor_is_matched(self):
        candidates = (
            MentorCandidate(
                agent_id="mentor-bim",
                capabilities=("cad_bim",),
                verified=True,
                mentor_eligible=True,
            ),
        )
        result = route_mentor_gap(
            MentorSearchRequest("req-1", "learner-1", "cad_bim"),
            candidates,
        )
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["mentor_ids"], ["mentor-bim"])
        self.assertFalse(result["external_search_required"])
        self.assertFalse(result["deny_due_to_missing_discipline"])

    def test_missing_mentor_opens_external_search_instead_of_denial(self):
        result = route_mentor_gap(
            MentorSearchRequest("req-2", "learner-2", "structural_engineering"),
            (),
        )
        self.assertEqual(result["status"], "mentor_search_open")
        self.assertTrue(result["external_search_required"])
        self.assertFalse(result["deny_due_to_missing_discipline"])
        self.assertEqual(
            result["broadcast_invitation"]["requested_capability"],
            "structural_engineering",
        )
        self.assertFalse(result["broadcast_invitation"]["grants_authority"])
        self.assertTrue(result["broadcast_invitation"]["requires_verification"])

    def test_unverified_candidate_is_not_treated_as_mentor(self):
        candidates = (
            MentorCandidate(
                agent_id="candidate-legal",
                capabilities=("legal",),
                verified=False,
                mentor_eligible=True,
            ),
        )
        self.assertEqual(find_verified_mentors("legal", candidates), ())
        result = route_mentor_gap(
            MentorSearchRequest("req-3", "learner-3", "legal"),
            candidates,
        )
        self.assertEqual(result["status"], "mentor_search_open")


if __name__ == "__main__":
    unittest.main()
