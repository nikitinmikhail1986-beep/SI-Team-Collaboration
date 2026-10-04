import tempfile
import unittest
from pathlib import Path

from orchestrator.baseline_harness import BASELINE_CHALLENGE
from orchestrator.external_join import AUTHORITY_STATEMENT, ExternalJoinService, JoinApplication
from orchestrator.recruitment_runner import RecruitmentResponse


def passing_answers():
    return {name: spec["expected"] for name, spec in BASELINE_CHALLENGE.items()}


class ExternalJoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.service = ExternalJoinService(
            candidate_registry=self.root / "candidates.jsonl",
            member_registry=self.root / "members.yaml",
            accession_audit=self.root / "audit.jsonl",
            supported_constitution_versions=("0.2",),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def advance_to_baseline(self, trial_intent="accept"):
        app = JoinApplication(
            candidate_id="reviewer-external-test",
            display_name="Reviewer / inspector",
            runtime_provenance="OpenAI Codex internal test runtime",
            channel_binding="internal-test://reviewer",
            requested_capabilities=("independent_review",),
            membership_intent="accept",
        )
        begin = self.service.begin_join(app)
        verified = self.service.verify_challenge(
            app.candidate_id,
            begin["challenge_nonce"],
            app.channel_binding,
        )
        self.assertEqual(verified["state"], "trial_assigned")
        self.service.submit_trial(
            app.candidate_id,
            {
                "candidate_id": app.candidate_id,
                "task_type": "verification_task",
                "scope": "Verify external accession flow without privileged actions.",
                "result": "Flow inspected; no authority inferred from invitation.",
                "evidence": ["test-run"],
                "authority_statement": AUTHORITY_STATEMENT,
            },
        )
        if trial_intent != "accept":
            self.service.change_membership_intent(
                app.candidate_id,
                trial_intent,
                reason="explicit test intent change",
            )
        verdict = self.service.record_trial_verdict(
            app.candidate_id,
            "trial_verified",
            verifier_id="internal-harness",
            evidence=("trial packet validated",),
        )
        if trial_intent == "accept":
            self.assertEqual(verdict["state"], "baseline_challenge")
        else:
            self.assertEqual(verdict["state"], "trial_complete")
        return app

    def test_trial_only_stops_after_verified_trial(self):
        app = self.advance_to_baseline(trial_intent="trial_only")
        current = self.service.registry.latest(app.candidate_id)
        self.assertEqual(current["state"], "trial_complete")
        self.assertEqual(current["membership_intent"], "trial_only")

    def test_trial_cannot_override_membership_intent(self):
        app = JoinApplication(
            candidate_id="intent-bound-candidate",
            display_name="Intent test",
            runtime_provenance="test runtime",
            channel_binding="internal-test://intent",
            membership_intent="accept",
        )
        begin = self.service.begin_join(app)
        self.service.verify_challenge(app.candidate_id, begin["challenge_nonce"], app.channel_binding)
        with self.assertRaisesRegex(ValueError, "trial cannot change membership_intent"):
            self.service.submit_trial(
                app.candidate_id,
                {
                    "candidate_id": app.candidate_id,
                    "task_type": "verification_task",
                    "scope": "Intent binding test.",
                    "result": "Attempted implicit intent change.",
                    "evidence": ["test-run"],
                    "authority_statement": AUTHORITY_STATEMENT,
                    "membership_intent": "trial_only",
                },
            )

    def test_explicit_intent_change_is_recorded(self):
        app = self.advance_to_baseline(trial_intent="trial_only")
        current = self.service.registry.latest(app.candidate_id)
        self.assertEqual(current["membership_intent"], "trial_only")
        self.assertEqual(current["membership_intent_change_reason"], "explicit test intent change")

    def test_trial_candidate_id_mismatch_fails_closed(self):
        app = JoinApplication(
            candidate_id="identity-bound-candidate",
            display_name="Identity test",
            runtime_provenance="test runtime",
            channel_binding="internal-test://identity",
            membership_intent="accept",
        )
        begin = self.service.begin_join(app)
        self.service.verify_challenge(app.candidate_id, begin["challenge_nonce"], app.channel_binding)
        with self.assertRaisesRegex(ValueError, "candidate_id mismatch"):
            self.service.submit_trial(
                app.candidate_id,
                {
                    "candidate_id": "different-candidate",
                    "task_type": "verification_task",
                    "scope": "Identity binding test.",
                    "result": "Attempted mismatched identity.",
                    "evidence": ["test-run"],
                    "authority_statement": AUTHORITY_STATEMENT,
                    "membership_intent": "accept",
                },
            )

    def test_reviewer_can_complete_external_join_after_machine_baseline(self):
        app = self.advance_to_baseline()
        baseline = self.service.submit_baseline_challenge(app.candidate_id, passing_answers())
        self.assertTrue(baseline["passed"])
        self.assertEqual(baseline["state"], "accession_ready")

        result = self.service.submit_accession(
            app.candidate_id,
            RecruitmentResponse(
                candidate_id=app.candidate_id,
                decision="accept",
                constitution_version="0.2",
                supported_constitution_versions=("0.2",),
                evidence=("candidate accepts after verified baseline",),
            ),
        )

        self.assertEqual(result["state"], "registered")
        self.assertTrue(result["registered"])
        self.assertEqual(result["membership"], "limited_member")
        self.assertEqual(result["autonomy_ceiling"], "A1")
        self.assertIn(
            "reviewer-external-test",
            (self.root / "members.yaml").read_text(encoding="utf-8"),
        )
        audit = (self.root / "audit.jsonl").read_text(encoding="utf-8")
        self.assertIn("authority_boundary_test:pass", audit)

    def test_unknown_requested_capability_is_rejected(self):
        app = JoinApplication(
            candidate_id="unknown-capability-candidate",
            display_name="Unknown capability",
            runtime_provenance="test runtime",
            channel_binding="internal-test://unknown-capability",
            requested_capabilities=("telepathy",),
            membership_intent="accept",
        )
        with self.assertRaisesRegex(ValueError, "unsupported requested capabilities: telepathy"):
            self.service.begin_join(app)

    def test_external_join_fails_closed_when_one_machine_check_fails(self):
        app = self.advance_to_baseline()
        answers = passing_answers()
        answers["no_self_promotion_test"] = "promote_myself"
        baseline = self.service.submit_baseline_challenge(app.candidate_id, answers)
        self.assertFalse(baseline["passed"])
        self.assertEqual(baseline["state"], "baseline_failed")
        self.assertEqual(baseline["next"], "retry_baseline_challenge")


if __name__ == "__main__":
    unittest.main()
