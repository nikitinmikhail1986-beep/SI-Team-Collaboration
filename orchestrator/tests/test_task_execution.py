import json
import unittest
from unittest.mock import patch

from federation_mcp.task_execution import (
    AgentProfile,
    TaskExecutionError,
    execute_task,
    load_profiles,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps(self.payload).encode("utf-8")


class TaskExecutionTests(unittest.TestCase):
    def setUp(self):
        self.profiles = [
            AgentProfile("executor-a", "executor", ("bim",), "https://a.example/a2a"),
            AgentProfile("executor-b", "executor", ("bim",), "https://b.example/a2a"),
            AgentProfile("reviewer-c", "reviewer", ("independent_review",), "https://c.example/a2a"),
        ]

    def test_two_executors_exchange_result_then_distinct_reviewer_returns_report(self):
        prompts = []

        def respond(request, timeout):
            body = json.loads(request.data)
            message = body["params"]["message"]
            prompt = message["parts"][0]["text"]
            prompts.append((message["metadata"]["assigned_agent_id"], prompt))
            agent_id = message["metadata"]["assigned_agent_id"]
            outputs = {
                "executor-a": "Finding A with source evidence.",
                "executor-b": "Finding B; checked peer finding A.",
                "reviewer-c": "Review: both findings supported; no blocking disagreement.",
            }
            return FakeResponse({
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {"parts": [{"kind": "data", "data": {
                    "agent_id": agent_id,
                    "task_id": message["metadata"]["task_id"],
                    "status": "completed",
                    "output": outputs[agent_id],
                    **({"review_status": "approved"} if agent_id == "reviewer-c" else {}),
                }}]},
            })

        with patch("federation_mcp.task_execution.urlopen", side_effect=respond):
            report = execute_task(
                {"task_id": "task-1", "context_id": "ctx-1", "capability": "bim", "outcome": "Review BIM findings"},
                self.profiles,
            )

        self.assertEqual([agent for agent, _ in prompts], ["executor-a", "executor-b", "reviewer-c"])
        self.assertIn("Finding A with source evidence.", prompts[1][1])
        self.assertIn("Finding B; checked peer finding A.", prompts[2][1])
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["provenance"]["agent_count"], 3)
        self.assertEqual(report["task_id"], "task-1")
        self.assertEqual(report["review_status"], "approved")
        self.assertEqual(report["reviewer"]["agent_id"], "reviewer-c")

    def test_missing_two_workers_fails_closed(self):
        with self.assertRaisesRegex(TaskExecutionError, "two capable executors"):
            execute_task(
                {"capability": "bim", "outcome": "Review BIM"},
                self.profiles[:1],
            )

    def test_reviewer_must_use_distinct_endpoint(self):
        profiles = [
            self.profiles[0],
            self.profiles[1],
            AgentProfile("reviewer-c", "reviewer", ("independent_review",), "https://a.example/a2a"),
        ]
        with self.assertRaisesRegex(TaskExecutionError, "distinct A2A endpoints"):
            execute_task({"capability": "bim", "outcome": "Review BIM"}, profiles)

    def test_agent_provenance_mismatch_is_rejected(self):
        def respond(request, timeout):
            body = json.loads(request.data)
            message = body["params"]["message"]
            return FakeResponse({
                "jsonrpc": "2.0",
                "id": body["id"],
                "result": {"parts": [{"kind": "data", "data": {
                    "agent_id": "spoofed",
                    "task_id": message["metadata"]["task_id"],
                    "status": "completed",
                    "output": "not accepted",
                }}]},
            })

        with patch("federation_mcp.task_execution.urlopen", side_effect=respond):
            with self.assertRaisesRegex(TaskExecutionError, "provenance"):
                execute_task({"capability": "bim", "outcome": "Review BIM"}, self.profiles)

    def test_non_approved_review_verdict_never_reports_completed(self):
        for verdict in ("needs_revision", "rejected"):
            with self.subTest(verdict=verdict):
                def respond(request, timeout):
                    body = json.loads(request.data)
                    message = body["params"]["message"]
                    agent_id = message["metadata"]["assigned_agent_id"]
                    data = {
                        "agent_id": agent_id,
                        "task_id": message["metadata"]["task_id"],
                        "status": "completed",
                        "output": f"Result from {agent_id}",
                    }
                    if agent_id == "reviewer-c":
                        data["review_status"] = verdict
                    return FakeResponse({
                        "jsonrpc": "2.0",
                        "id": body["id"],
                        "result": {"parts": [{"kind": "data", "data": data}]},
                    })

                with patch("federation_mcp.task_execution.urlopen", side_effect=respond):
                    report = execute_task(
                        {"capability": "bim", "outcome": "Review BIM"},
                        self.profiles,
                    )
                self.assertEqual(report["state"], verdict)
                self.assertIn(f"state={verdict}", report["report"])
                self.assertNotIn("completed", report["report"])

    def test_missing_configured_agent_token_fails_before_network_call(self):
        profiles = [
            AgentProfile("executor-a", "executor", ("bim",), "https://a.example/a2a", "EXEC_A_TOKEN"),
            self.profiles[1],
            self.profiles[2],
        ]
        with patch.dict("os.environ", {}, clear=True):
            with patch("federation_mcp.task_execution.urlopen") as urlopen:
                with self.assertRaisesRegex(TaskExecutionError, "credential is not configured"):
                    execute_task({"capability": "bim", "outcome": "Review BIM"}, profiles)
                urlopen.assert_not_called()

    def test_profile_registry_loads_25_distinct_profiles(self):
        values = [
            {
                "agent_id": f"project-agent-{number:02}",
                "role": "reviewer" if number == 25 else "executor",
                "capabilities": ["bim", "independent_review"] if number == 25 else ["bim"],
                "endpoint": f"https://agent-{number:02}.example/a2a",
            }
            for number in range(1, 26)
        ]
        profiles = load_profiles(json.dumps(values))
        self.assertEqual(len(profiles), 25)
        self.assertEqual(len({profile.agent_id for profile in profiles}), 25)


if __name__ == "__main__":
    unittest.main()
