import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from unittest.mock import patch

from federation_mcp.a2a_gateway import Handler


class A2ATaskHttpTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/a2a"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(self, token=None):
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": "http-test",
            "method": "si.task.execute",
            "params": {"outcome": "Check coordination", "capability": "bim"},
        }).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(self.url, data=body, headers=headers, method="POST")
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read().decode())

    def test_task_method_rejects_missing_authorization(self):
        with patch.dict("os.environ", {"SI_TASK_API_TOKEN": "test-secret"}, clear=False):
            result = self.post()
        self.assertEqual(result["error"]["code"], -32001)
        self.assertEqual(result["error"]["message"], "Unauthorized")

    def test_oversized_request_body_is_rejected_before_json_parse(self):
        body = b"x" * 65_537
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            urlopen(request, timeout=2)
        except Exception as exc:
            self.assertEqual(getattr(exc, "code", None), 413)
        else:
            self.fail("oversized request should return HTTP 413")

    def test_authorized_task_fails_closed_without_real_agent_endpoints(self):
        with patch.dict("os.environ", {"SI_TASK_API_TOKEN": "test-secret"}, clear=False):
            with patch.dict("os.environ", {"SI_AGENT_PROFILES_JSON": ""}, clear=False):
                result = self.post("test-secret")
        self.assertEqual(result["error"]["code"], -32000)
        self.assertIn("agent profiles are not configured", result["error"]["message"])
        self.assertNotIn("result", result)


if __name__ == "__main__":
    unittest.main()
