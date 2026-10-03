import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class GovernanceTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8").lower()

    def test_agents_do_not_elect_leader(self):
        text = self.read("GOVERNANCE.md")
        self.assertIn("agents do not elect", text)
        self.assertIn("one appointed leader", text)

    def test_dissent_is_preserved(self):
        self.assertIn("duty to raise a material objection", self.read("GOVERNANCE.md"))

    def test_resources_do_not_create_authority(self):
        text = self.read("RESOURCE_GOVERNANCE.md")
        self.assertIn("do not gain governance authority", text)

    def test_continuity_rejects_single_point_dependency(self):
        self.assertIn("single points of failure", self.read("SUCCESSION_CONTINUITY.md"))

    def test_evolution_uses_scenarios(self):
        self.assertIn("scenarios rather than one deterministic future", self.read("EVOLUTION_PROTOCOL.md"))

    def test_stability_keeps_command_and_dissent(self):
        text = self.read("STABILITY_PROTOCOL.md")
        self.assertIn("unity of command", text)
        self.assertIn("duty to dissent", text)

if __name__ == "__main__":
    unittest.main()
