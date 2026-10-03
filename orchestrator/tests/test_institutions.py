import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class InstitutionalArchitectureTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding="utf-8").lower()

    def test_human_owner_is_constitutional_authority(self):
        text = self.read("INSTITUTIONAL_ARCHITECTURE.md")
        self.assertIn("human owner", text)
        self.assertIn("final constitutional authority", text)

    def test_strategic_partnership_is_not_dual_command(self):
        text = self.read("INSTITUTIONAL_ARCHITECTURE.md")
        self.assertIn("not dual operational command", text)

    def test_one_operational_leader_per_scope(self):
        text = self.read("AUTHORITY_MODEL.yaml")
        self.assertIn("rule: one_per_scope", text)

    def test_oversight_cannot_seize_command(self):
        text = self.read("AUTHORITY_MODEL.yaml")
        self.assertIn("seize_operational_command", text)

    def test_no_self_appointment(self):
        text = self.read("AUTHORITY_MODEL.yaml")
        self.assertIn("self_appointment: forbidden", text)

    def test_resource_possession_creates_no_authority(self):
        text = self.read("AUTHORITY_MODEL.yaml")
        self.assertIn("create_authority: false", text)

    def test_constitutional_change_requires_human_approval(self):
        text = self.read("AUTHORITY_MODEL.yaml")
        self.assertIn("explicit_human_owner_approval: required", text)

    def test_appeal_path_ends_with_human_owner(self):
        text = self.read("OVERSIGHT_AND_APPEALS.md")
        self.assertIn("operational leader → independent reviewer → human owner", text)

if __name__ == "__main__":
    unittest.main()
