import json
import unittest
from unittest.mock import patch

from orchestrator.recruitment_runner import A2AHttpAdapter, McpHttpAdapter, RecruitmentTarget, build_invitation


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode("utf-8")


def target():
    return RecruitmentTarget(
        candidate_id="ext-1",
        display_name="External",
        source="external",
        transport="a2a",
        endpoint="https://example.test/invite",
        response_transport="a2a",
        response_endpoint="https://example.test/response",
    )


class ProtocolAdapterTests(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_a2a_wraps_invitation(self, urlopen):
        urlopen.return_value = FakeResponse({"delivery_id": "a2a-1"})
        adapter = A2AHttpAdapter()
        delivery = adapter.send_invitation(target(), build_invitation(target(), "0.3"))
        self.assertEqual(delivery, "a2a-1")
        body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(body["protocol"], "a2a")
        self.assertEqual(body["kind"], "federation_invitation")

    @patch("urllib.request.urlopen")
    def test_mcp_wraps_invitation(self, urlopen):
        urlopen.return_value = FakeResponse({"delivery_id": "mcp-1"})
        t = target()
        adapter = McpHttpAdapter()
        delivery = adapter.send_invitation(t, build_invitation(t, "0.3"))
        self.assertEqual(delivery, "mcp-1")
        body = json.loads(urlopen.call_args.args[0].data.decode("utf-8"))
        self.assertEqual(body["protocol"], "mcp")
        self.assertEqual(body["tool"], "federation_invite")


if __name__ == "__main__":
    unittest.main()
