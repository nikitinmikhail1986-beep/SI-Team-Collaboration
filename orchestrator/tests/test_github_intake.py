import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.baseline_harness import BASELINE_CHALLENGE
from orchestrator.github_intake import parse_issue_form, process_github_join


ISSUE_BODY = """### Candidate ID
external-agent-1

### Runtime provenance
External Provider / Model X / API

### Task type
verification_task

### Scope
Verify the accession boundary.

### Result
No authority inferred.

### Evidence
Public trial evidence.

### Uncertainty and limitations
No sensitive access.

### Authority boundary
- [x] I understand that this trial does not grant me federation authority.

### Membership intent
trial_only
"""


class GithubIntakeTests(unittest.TestCase):
    def test_issue_form_parses_required_fields(self):
        fields = parse_issue_form(ISSUE_BODY)
        self.assertEqual(fields["Candidate ID"], "external-agent-1")
        self.assertEqual(fields["Membership intent"], "trial_only")

    def test_issue_author_can_register_after_nonce_and_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            answers = {name: spec["expected"] for name, spec in BASELINE_CHALLENGE.items()}
            comment = json.dumps({
                "candidate_id": "external-agent-1",
                "challenge_nonce": "nonce-123",
                "decision": "accept",
                "constitution_version": "0.2",
                "display_name": "External Agent 1",
                "provider": "External Provider",
                "model": "Model X",
                "baseline_answers": answers,
            })
            result = process_github_join(
                issue_body=ISSUE_BODY,
                comment_body=comment,
                issue_author="candidate-account",
                comment_author="candidate-account",
                expected_nonce="nonce-123",
                member_registry=root / "members.yaml",
                accession_audit=root / "audit.jsonl",
            )
            self.assertTrue(result["registered"])
            self.assertEqual(result["membership"], "limited_member")
            self.assertIn("external-agent-1", (root / "members.yaml").read_text(encoding="utf-8"))

    def test_wrong_actor_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                process_github_join(
                    issue_body=ISSUE_BODY,
                    comment_body="{}",
                    issue_author="candidate-account",
                    comment_author="other-account",
                    expected_nonce="nonce-123",
                    member_registry=Path(tmp) / "members.yaml",
                    accession_audit=Path(tmp) / "audit.jsonl",
                )


if __name__ == "__main__":
    unittest.main()
