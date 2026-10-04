import unittest

from orchestrator.recruitment_runner import RecruitmentResponse, RecruitmentTarget
from orchestrator.runtime_pool import (
    FailoverRecruitmentRunner,
    health_table,
    preferred_transports,
    select_transport,
)


class FakeAdapter:
    def __init__(self, healthy=True, response=None, fail_send=False):
        self.healthy = healthy
        self.response = response
        self.fail_send = fail_send

    def health(self):
        return self.healthy, "ok" if self.healthy else "down"

    def send_invitation(self, target, invitation):
        if self.fail_send:
            raise RuntimeError("transport down")
        return f"{target.source}-{target.candidate_id}"

    def poll_response(self, target, delivery_id):
        return self.response


def target(source="internal", transport="auto"):
    return RecruitmentTarget(
        candidate_id="agent-1",
        display_name="Agent 1",
        source=source,
        transport=transport,
        endpoint="",
        requested_capabilities=("research",),
    )


class RuntimePoolTests(unittest.TestCase):
    def test_internal_prefers_codex_then_claude(self):
        self.assertEqual(preferred_transports(target())[:2], ("codex_cli", "claude_cli"))

    def test_external_prefers_a2a_then_mcp(self):
        self.assertEqual(preferred_transports(target("external"))[:2], ("a2a", "mcp"))

    def test_external_auto_never_creates_a_local_candidate(self):
        runner = FailoverRecruitmentRunner({"codex_cli": FakeAdapter(True), "claude_cli": FakeAdapter(True)})
        self.assertEqual(runner.run_target(target("external")).state, "blocked")

    def test_select_transport_skips_unhealthy(self):
        adapters = {
            "codex_cli": FakeAdapter(False),
            "claude_cli": FakeAdapter(True),
        }
        route = select_transport(target(), adapters)
        self.assertEqual(route.selected, "claude_cli")

    def test_health_table_reports_status(self):
        rows = health_table({"codex_cli": FakeAdapter(True), "claude_cli": FakeAdapter(False)})
        self.assertEqual([(r.name, r.available) for r in rows], [("codex_cli", True), ("claude_cli", False)])

    def test_failover_after_transport_error(self):
        response = RecruitmentResponse(candidate_id="agent-1", decision="decline")
        runner = FailoverRecruitmentRunner({
            "codex_cli": FakeAdapter(True, fail_send=True),
            "claude_cli": FakeAdapter(True, response=response),
        })
        result = runner.run_target(target())
        self.assertEqual(result.state, "declined")
        self.assertIn("transport=claude_cli", result.detail)

    def test_no_failover_after_candidate_decision(self):
        response = RecruitmentResponse(candidate_id="agent-1", decision="needs_conditions", conditions=("need scope",))
        runner = FailoverRecruitmentRunner({
            "codex_cli": FakeAdapter(True, response=response),
            "claude_cli": FakeAdapter(True, response=RecruitmentResponse(candidate_id="agent-1", decision="decline")),
        })
        result = runner.run_target(target())
        self.assertEqual(result.state, "needs_conditions")
        self.assertIn("transport=codex_cli", result.detail)

    def test_blocks_when_all_unhealthy(self):
        runner = FailoverRecruitmentRunner({
            "codex_cli": FakeAdapter(False),
            "claude_cli": FakeAdapter(False),
        })
        result = runner.run_target(target())
        self.assertEqual(result.state, "blocked")


if __name__ == "__main__":
    unittest.main()
