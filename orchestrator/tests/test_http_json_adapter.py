import io
import json
import unittest
from unittest.mock import patch

from orchestrator.recruitment_runner import HttpJsonAdapter, RecruitmentTarget, build_invitation


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class HttpJsonAdapterTests(unittest.TestCase):
    def target(self):
        return RecruitmentTarget(
            candidate_id="external-1",
            display_name="External 1",
            source="external",
            transport="http_json",
            endpoint="https://example.test/invite",
            response_transport="http_json",
            response_endpoint="https://example.test/response",
        )

    @patch("urllib.request.urlopen")
    def test_send_invitation_returns_delivery_id(self, urlopen):
        urlopen.return_value = FakeResponse({"delivery_id": "d-123"})
        adapter = HttpJsonAdapter()
        delivery_id = adapter.send_invitation(self.target(), build_invitation(self.target(), "0.3"))
        self.assertEqual(delivery_id, "d-123")

    @patch("urllib.request.urlopen")
    def test_poll_response_parses_decision(self, urlopen):
        urlopen.return_value = FakeResponse({
            "candidate_id": "external-1",
            "decision": "decline",
            "constitution_version": "0.3",
            "supported_constitution_versions": ["0.3"],
            "conditions": [],
            "evidence": [],
        })
        adapter = HttpJsonAdapter()
        response = adapter.poll_response(self.target(), "d-123")
        self.assertEqual(response.decision, "decline")
        self.assertEqual(response.candidate_id, "external-1")


if __name__ == "__main__":
    unittest.main()
