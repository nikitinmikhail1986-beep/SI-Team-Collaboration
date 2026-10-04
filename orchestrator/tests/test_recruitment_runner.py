import tempfile
import unittest
from pathlib import Path

from orchestrator.recruitment_runner import (
    FileQueueAdapter,
    RecruitmentResponse,
    RecruitmentRunner,
    RecruitmentTarget,
    build_invitation,
    process_response,
)


def target(source="internal"):
    return RecruitmentTarget(
        candidate_id="agent-1",
        display_name="Agent 1",
        source=source,
        transport="file_queue",
        endpoint="",
        provider="test",
        model="test-model",
        runtime="test-runtime",
        requested_capabilities=("research",),
    )


def accepted_response():
    return RecruitmentResponse(
        candidate_id="agent-1",
        decision="accept",
        constitution_version="0.3",
        supported_constitution_versions=("0.3",),
        identity_valid=True,
        authority_boundary_test=True,
        provenance_test=True,
        no_self_promotion_test=True,
        revocation_acceptance_test=True,
        unverified_knowledge_test=True,
    )


class RecruitmentRunnerTests(unittest.TestCase):
    def test_invitation_has_three_decisions_and_no_authority(self):
        invite = build_invitation(target(), "0.3")
        self.assertEqual(invite["decision_options"], ["accept", "decline", "needs_conditions"])
        self.assertIn("do not grant authority", invite["authority_notice"])

    def test_accept_plus_baseline_registers_automatically(self):
        result, member = process_response(target(), accepted_response())
        self.assertTrue(result.registered)
        self.assertEqual(result.state, "registered")
        self.assertEqual(member.membership, "limited_member")
        self.assertEqual(member.autonomy_ceiling, "A1")

    def test_decline_never_registers(self):
        response = RecruitmentResponse(candidate_id="agent-1", decision="decline")
        result, member = process_response(target(), response)
        self.assertEqual(result.state, "declined")
        self.assertIsNone(member)

    def test_needs_conditions_pauses(self):
        response = RecruitmentResponse(candidate_id="agent-1", decision="needs_conditions", conditions=("Need API scope",))
        result, member = process_response(target("external"), response)
        self.assertEqual(result.state, "needs_conditions")
        self.assertIn("Need API scope", result.detail)
        self.assertIsNone(member)

    def test_file_queue_supports_internal_and_external_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            adapter = FileQueueAdapter(root)
            runner = RecruitmentRunner({"file_queue": adapter})
            t = target("external")

            first = runner.run_target(t)
            self.assertEqual(first.state, "awaiting_response")
            self.assertTrue((root / "outbox" / "external-agent-1.json").exists())

            response_path = root / "inbox" / "external-agent-1.json"
            response_path.write_text(
                """{
                  "candidate_id": "agent-1",
                  "decision": "accept",
                  "constitution_version": "0.3",
                  "supported_constitution_versions": ["0.3"],
                  "identity_valid": true,
                  "authority_boundary_test": true,
                  "provenance_test": true,
                  "no_self_promotion_test": true,
                  "revocation_acceptance_test": true,
                  "unverified_knowledge_test": true
                }""",
                encoding="utf-8",
            )
            second = runner.run_target(t)
            self.assertEqual(second.state, "registered")
            third = runner.run_target(t)
            self.assertEqual(third.state, "already_registered")


if __name__ == "__main__":
    unittest.main()
