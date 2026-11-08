import threading
import unittest

from federation_mcp.internal_agents import (
    InternalAgentError,
    execute_internal_task,
    load_internal_profiles,
    reset_state_for_tests,
    worker_complete,
    worker_fail,
    worker_poll,
    worker_status,
)


class InternalAgentCoordinatorTests(unittest.TestCase):
    def setUp(self):
        reset_state_for_tests()
        self.profiles = load_internal_profiles()
        for profile in self.profiles:
            worker_poll({"agent_id": profile.agent_id, "wait_seconds": 0})

    def tearDown(self):
        reset_state_for_tests()

    def test_registry_contains_25_distinct_internal_project_profiles(self):
        ids = [profile.agent_id for profile in self.profiles]
        self.assertEqual(len(ids), 25)
        self.assertEqual(len(set(ids)), 25)
        self.assertGreaterEqual(sum(p.role == "executor" for p in self.profiles), 2)
        self.assertTrue(any(p.role == "reviewer" and "independent_review" in p.capabilities for p in self.profiles))
        self.assertEqual(next(p.role for p in self.profiles if p.agent_id == "gip"), "reviewer")

    def test_status_reports_all_25_profiles_after_each_profile_polls(self):
        status = worker_status()
        self.assertEqual(status["state"], "ready")
        self.assertEqual(status["online_count"], 25)
        self.assertEqual(status["profile_count"], 25)

    def test_two_executors_exchange_results_before_independent_review(self):
        first = "proektnye-agenty__inzhener-vk"
        second = "proektnye-agenty__inzhener-ovik"
        reviewer = "proektnye-agenty__normokontrol-pp87"
        outcome = "Echo marker SI-FEDERATION-LIVE-TEST and report whether it is present."
        params = {
            "task_id": "live-shape-test-1",
            "context_id": "live-shape-context-1",
            "capability": "project_coordination",
            "outcome": outcome,
            "executor_ids": [first, second],
            "reviewer_id": reviewer,
        }
        result_box = {}

        def run():
            try:
                result_box["result"] = execute_internal_task(params, timeout=5)
            except Exception as exc:  # returned to the test thread for an assertion
                result_box["error"] = exc

        thread = threading.Thread(target=run)
        thread.start()
        assigned_first = worker_poll({"agent_id": first, "wait_seconds": 1})
        self.assertEqual(assigned_first["phase"], "executor-1")
        self.assertEqual(assigned_first["agent_id"], first)
        worker_complete({"task_id": params["task_id"], "agent_id": first, "phase": "executor-1", "output": "SI-FEDERATION-LIVE-TEST confirmed by executor one."})

        assigned_second = worker_poll({"agent_id": second, "wait_seconds": 1})
        self.assertEqual(assigned_second["phase"], "executor-2")
        self.assertIn("confirmed by executor one", assigned_second["prompt"])
        worker_complete({"task_id": params["task_id"], "agent_id": second, "phase": "executor-2", "output": "SI-FEDERATION-LIVE-TEST checked against executor one."})

        assigned_reviewer = worker_poll({"agent_id": reviewer, "wait_seconds": 1})
        self.assertEqual(assigned_reviewer["phase"], "reviewer")
        self.assertIn("executor one", assigned_reviewer["prompt"])
        self.assertIn(second, assigned_reviewer["prompt"])
        worker_complete({"task_id": params["task_id"], "agent_id": reviewer, "phase": "reviewer", "output": "Both executor results carry the marker.", "review_status": "approved"})
        thread.join(timeout=2)

        self.assertFalse(thread.is_alive())
        self.assertNotIn("error", result_box)
        result = result_box["result"]
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["provenance"]["registered_profile_count"], 25)
        self.assertEqual(result["provenance"]["online_profile_count"], 25)
        self.assertEqual(result["executors"][0]["agent_id"], first)
        self.assertEqual(result["executors"][1]["agent_id"], second)
        self.assertEqual(result["reviewer"]["agent_id"], reviewer)

    def test_worker_cannot_submit_for_another_profile(self):
        first = "proektnye-agenty__inzhener-vk"
        second = "proektnye-agenty__inzhener-ovik"
        reviewer = "proektnye-agenty__normokontrol-pp87"
        params = {"task_id": "wrong-worker-1", "capability": "project_coordination", "outcome": "Short check", "executor_ids": [first, second], "reviewer_id": reviewer}
        errors = []
        thread = threading.Thread(target=lambda: _capture_error(execute_internal_task, params, errors))
        thread.start()
        worker_poll({"agent_id": first, "wait_seconds": 1})
        with self.assertRaisesRegex(InternalAgentError, "does not match"):
            worker_complete({"task_id": params["task_id"], "agent_id": second, "phase": "executor-1", "output": "spoofed result"})
        thread.join(timeout=0.05)
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        reset_state_for_tests()

    def test_worker_failure_terminates_task_with_sanitized_reason(self):
        first = "proektnye-agenty__inzhener-vk"
        second = "proektnye-agenty__inzhener-ovik"
        reviewer = "proektnye-agenty__normokontrol-pp87"
        params = {"task_id": "worker-failure-1", "capability": "project_coordination", "outcome": "Short check", "executor_ids": [first, second], "reviewer_id": reviewer}
        errors = []
        thread = threading.Thread(target=lambda: _capture_error(execute_internal_task, params, errors))
        thread.start()
        assignment = worker_poll({"agent_id": first, "wait_seconds": 1})
        self.assertEqual(assignment["phase"], "executor-1")
        self.assertEqual(worker_fail({
            "task_id": params["task_id"],
            "agent_id": first,
            "phase": "executor-1",
            "reason": "Ollama\nUnavailable",
        }), {"accepted": True})
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0]), "internal worker failed in executor-1: Ollama_Unavailable")

    def test_worker_failure_cannot_fail_another_assignment(self):
        first = "proektnye-agenty__inzhener-vk"
        second = "proektnye-agenty__inzhener-ovik"
        reviewer = "proektnye-agenty__normokontrol-pp87"
        params = {"task_id": "worker-failure-spoof-1", "capability": "project_coordination", "outcome": "Short check", "executor_ids": [first, second], "reviewer_id": reviewer}
        thread = threading.Thread(target=lambda: _capture_error(execute_internal_task, params, []))
        thread.start()
        worker_poll({"agent_id": first, "wait_seconds": 1})
        with self.assertRaisesRegex(InternalAgentError, "does not match"):
            worker_fail({"task_id": params["task_id"], "agent_id": second, "phase": "executor-1", "reason": "spoof"})
        worker_fail({"task_id": params["task_id"], "agent_id": first, "phase": "executor-1", "reason": "test_cleanup"})
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())


def _capture_error(function, params, errors):
    try:
        function(params, timeout=0.1)
    except Exception as exc:
        errors.append(exc)


if __name__ == "__main__":
    unittest.main()
