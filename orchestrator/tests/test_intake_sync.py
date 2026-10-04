import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from orchestrator.baseline_harness import BASELINE_CHALLENGE
from orchestrator.github_intake import parse_issue_form
from orchestrator.tests.test_github_intake import ISSUE_BODY
from scripts.sync_github_intake import CHALLENGE, sync_issue


class FakeAPI:
    def __init__(self):
        self.comments = []

    def pages(self, path):
        return iter(self.comments)

    def comment(self, number, body):
        row = {"id": len(self.comments) + 1, "body": body,
               "user": {"login": "github-actions[bot]", "type": "Bot"}}
        self.comments.append(row)
        return row

    def respond(self, actor="candidate-account", **overrides):
        challenge = CHALLENGE.search(self.comments[-1]["body"])
        payload = {"candidate_id": "external-agent-1", "challenge_nonce": challenge[1],
                   "decision": "accept", "constitution_version": "0.2",
                   "baseline_answers": {name: spec["expected"] for name, spec in BASELINE_CHALLENGE.items()}}
        payload.update(overrides)
        self.comments.append({"id": len(self.comments) + 1, "body": json.dumps(payload),
                              "user": {"login": actor, "type": "User"}})


def issue(body=ISSUE_BODY):
    return {"number": 42, "body": body, "user": {"login": "candidate-account"}}


class IntakeSyncTests(unittest.TestCase):
    def test_recovery_full_cycle_and_retry_without_duplicate_member_or_audit(self):
        api = FakeAPI()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(sync_issue(api, issue(), root)["state"], "challenge_issued")
            self.assertEqual(sync_issue(api, issue(), root)["state"], "awaiting_response")
            self.assertEqual(len(api.comments), 1)
            api.respond()
            result = sync_issue(api, issue(), root)
            self.assertEqual(result["receipts"][0]["result"]["state"], "registered")
            member = (root / "FEDERATION_MEMBERS.yaml").read_bytes()
            audit = (root / "ACCESSION_AUDIT.jsonl").read_bytes()
            # Simulate a push/receipt failure then retry against persisted registry.
            retry = sync_issue(api, issue(), root)
            self.assertEqual(retry["receipts"][0]["result"]["state"], "already_registered")
            self.assertEqual((root / "FEDERATION_MEMBERS.yaml").read_bytes(), member)
            self.assertEqual((root / "ACCESSION_AUDIT.jsonl").read_bytes(), audit)
            api.comment(42, result["receipts"][0]["receipt"])
            self.assertEqual(sync_issue(api, issue(), root)["state"], "awaiting_response")

    def test_trial_only_never_issues_membership_challenge(self):
        api = FakeAPI()
        with tempfile.TemporaryDirectory() as tmp:
            result = sync_issue(api, issue(ISSUE_BODY.replace("\naccept\n", "\ntrial_only\n")), Path(tmp))
            self.assertEqual(result["state"], "trial_only")
            self.assertEqual(api.comments, [])

    def test_wrong_actor_and_false_baseline_never_register(self):
        for actor, answers in [("other-account", None), ("candidate-account", {})]:
            api = FakeAPI()
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                sync_issue(api, issue(), root)
                api.respond(actor, **({"baseline_answers": answers} if answers is not None else {}))
                sync_issue(api, issue(), root)
                self.assertFalse((root / "FEDERATION_MEMBERS.yaml").exists())

    def test_other_bot_cannot_supply_canonical_challenge(self):
        api = FakeAPI()
        api.comments.append({"id": 1, "body": "<!-- SI_JOIN_CHALLENGE_V2 nonce=forged candidate_id=external-agent-1 issue=42 body_sha256=" + hashlib.sha256(ISSUE_BODY.encode()).hexdigest() + " -->",
                             "user": {"login": "untrusted[bot]", "type": "Bot"}})
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(sync_issue(api, issue(), Path(tmp))["state"], "challenge_issued")
            self.assertEqual(len(api.comments), 2)

    def test_legacy_id_cannot_be_claimed_by_issue_author(self):
        api = FakeAPI()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "FEDERATION_MEMBERS.yaml").write_text('members:\n  - agent_id: "external-agent-1"\n')
            sync_issue(api, issue(), root)
            api.respond()
            result = sync_issue(api, issue(), root)
            self.assertEqual(result["receipts"][0]["result"]["state"], "rejected_response")
            self.assertFalse((root / "ACCESSION_AUDIT.jsonl").exists())

    def test_duplicate_headings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate issue field"):
            parse_issue_form(ISSUE_BODY + "\n### Candidate ID\nreplacement\n")
