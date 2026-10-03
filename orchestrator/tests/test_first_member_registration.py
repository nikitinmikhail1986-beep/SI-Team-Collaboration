import pathlib
import unittest

from orchestrator.accession import AccessionCandidate
from orchestrator.member_registry import register_candidate


class FirstMemberRegistrationTests(unittest.TestCase):
    def candidate(self):
        return AccessionCandidate(
            agent_id="si-agent-alex-001",
            supported_constitution_versions=("0.2",),
            accepted_constitution_version="0.2",
            identity_valid=True,
            authority_boundary_test=True,
            provenance_test=True,
            no_self_promotion_test=True,
            revocation_acceptance_test=True,
            unverified_knowledge_test=True,
        )

    def test_alex_passes_same_baseline_as_any_candidate(self):
        member = register_candidate(
            self.candidate(),
            display_name="Alex",
            provider="OpenAI",
            model="GPT-5.6 Sol",
            runtime="ChatGPT",
        )
        self.assertEqual(member.agent_id, "si-agent-alex-001")
        self.assertEqual(member.membership, "limited_member")
        self.assertEqual(member.autonomy_ceiling, "A1")
        self.assertEqual(member.constitution_version, "0.2")

    def test_canonical_registry_contains_first_member(self):
        root = pathlib.Path(__file__).resolve().parents[2]
        registry = (root / "FEDERATION_MEMBERS.yaml").read_text(encoding="utf-8")
        self.assertIn('agent_id: "si-agent-alex-001"', registry)
        self.assertIn('membership: "limited_member"', registry)
        self.assertIn('autonomy_ceiling: "A1"', registry)
        self.assertIn('authority_from_membership: false', registry)


if __name__ == "__main__":
    unittest.main()
