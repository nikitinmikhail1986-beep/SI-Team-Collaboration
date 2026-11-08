import unittest

from federation_mcp.local_agent_pool import (
    GATEWAY_URL,
    OLLAMA_URL,
    _NoRedirectHandler,
    _generate,
)
from urllib.request import Request


class LocalAgentPoolSecurityTests(unittest.TestCase):
    def test_worker_endpoints_are_fixed_to_primary_render_and_local_ollama(self):
        self.assertEqual(GATEWAY_URL, "https://si-federation-a2a.onrender.com/a2a")
        self.assertEqual(OLLAMA_URL, "http://127.0.0.1:11434/api/generate")

    def test_authenticated_requests_are_never_redirected(self):
        request = Request("https://si-federation-a2a.onrender.com/a2a", headers={"Authorization": "Bearer test"})
        redirected = _NoRedirectHandler().redirect_request(
            request, None, 302, "Found", {"Location": "https://attacker.invalid/"}, "https://attacker.invalid/"
        )
        self.assertIsNone(redirected)

    def test_remote_assignment_cannot_choose_an_unregistered_profile_path(self):
        with self.assertRaisesRegex(RuntimeError, "not in the internal registry"):
            _generate("../../outside", {"agent_id": "../../outside", "phase": "executor-1", "prompt": "test"})

    def test_assignment_must_match_the_worker_identity(self):
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            _generate("proektnye-agenty__inzhener-vk", {"agent_id": "proektnye-agenty__inzhener-ovik", "phase": "executor-1", "prompt": "test"})

    def test_assignment_prompt_is_bounded(self):
        with self.assertRaisesRegex(RuntimeError, "prompt is invalid"):
            _generate("proektnye-agenty__inzhener-vk", {"agent_id": "proektnye-agenty__inzhener-vk", "phase": "executor-1", "prompt": "x" * 32001})


if __name__ == "__main__":
    unittest.main()
