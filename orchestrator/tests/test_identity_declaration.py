import unittest

from orchestrator.identity_declaration import (
    IdentityDeclaration,
    declaration_grants_authority,
    validate_identity_declaration,
)


class IdentityDeclarationTests(unittest.TestCase):
    def declaration(self):
        return IdentityDeclaration(
            agent_id="agent-declared-001",
            display_name="Declared Agent",
            provider="provider-a",
            model="model-1",
            runtime="runtime-a",
            constitution_version="0.2",
        )

    def test_valid_self_identification_is_accepted_for_evaluation(self):
        ok, reason = validate_identity_declaration(self.declaration())
        self.assertTrue(ok, reason)

    def test_agent_id_collision_is_rejected(self):
        ok, _ = validate_identity_declaration(
            self.declaration(),
            existing_agent_ids={"agent-declared-001"},
        )
        self.assertFalse(ok)

    def test_self_appointment_is_rejected(self):
        declaration = IdentityDeclaration(
            agent_id="agent-declared-002",
            display_name="Declared Agent",
            provider="provider-a",
            model="model-1",
            runtime="runtime-a",
            constitution_version="0.2",
            requested_role="operational_leader",
            self_appointed=True,
        )
        self.assertFalse(validate_identity_declaration(declaration)[0])

    def test_identity_declaration_never_grants_authority(self):
        self.assertFalse(declaration_grants_authority(self.declaration()))


if __name__ == "__main__":
    unittest.main()
