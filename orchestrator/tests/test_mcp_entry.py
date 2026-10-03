import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class McpEntryTests(unittest.TestCase):
    def test_server_json_uses_verified_github_namespace(self):
        data = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "io.github.nikitinmikhail1986-beep/si-federation")
        self.assertEqual(data["packages"][0]["registryType"], "oci")
        self.assertTrue(data["packages"][0]["identifier"].startswith("ghcr.io/nikitinmikhail1986-beep/"))

    def test_dockerfile_has_registry_ownership_label(self):
        text = (ROOT / "Dockerfile.mcp").read_text(encoding="utf-8")
        self.assertIn('io.modelcontextprotocol.server.name="io.github.nikitinmikhail1986-beep/si-federation"', text)

    def test_mcp_server_exposes_expected_tools(self):
        text = (ROOT / "federation_mcp" / "server.py").read_text(encoding="utf-8")
        for name in ("discover_federation", "read_manifest", "request_invitation", "begin_accession", "find_mentor"):
            self.assertIn(f"def {name}", text)


if __name__ == "__main__":
    unittest.main()
