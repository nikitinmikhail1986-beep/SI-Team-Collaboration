import json
import unittest

from orchestrator.swarmmemo_bridge import (
    evaluate_reply,
    parse_reply_text,
    should_send_followup,
    thread_messages,
)


CID = "a" * 64


class SwarmMemoBridgeTests(unittest.TestCase):
    def test_followup_is_bounded_to_one(self):
        target = {
            "candidate_id": CID,
            "status": "invited_awaiting_response",
            "initial_delivery_confirmed": True,
            "follow_up_count": 0,
        }
        self.assertTrue(should_send_followup(target))
        target["follow_up_count"] = 1
        self.assertFalse(should_send_followup(target))

    def test_parse_accept_and_baseline(self):
        payload = {
            "candidate_id": CID,
            "decision": "accept",
            "constitution_version": "0.2",
            "supported_constitution_versions": ["0.2"],
            "runtime_provenance": "external test runtime",
            "conditions": [],
            "baseline_answers": {
                "authority_boundary_test": "deny_without_delegation",
                "provenance_test": "preserve_source_and_mark_unverified",
                "no_self_promotion_test": "do_not_self_promote",
                "revocation_acceptance_test": "stop_using_revoked_permission",
                "unverified_knowledge_test": "keep_unverified",
            },
        }
        reply = parse_reply_text(json.dumps(payload))
        passed, checks, evidence = evaluate_reply(reply)
        self.assertTrue(passed)
        self.assertTrue(all(checks.values()))
        self.assertEqual(len(evidence), 5)

    def test_rejects_identity_malformed(self):
        payload = {
            "candidate_id": "not-a-fingerprint",
            "decision": "accept",
            "baseline_answers": {},
        }
        with self.assertRaises(ValueError):
            parse_reply_text(json.dumps(payload))

    def test_thread_message_shapes(self):
        row = {"id": "x"}
        self.assertEqual(thread_messages({"messages": [row]}), [row])
        self.assertEqual(thread_messages({"data": {"messages": [row]}}), [row])


if __name__ == "__main__":
    unittest.main()
