from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityDeclaration:
    agent_id: str
    display_name: str
    provider: str
    model: str
    runtime: str
    constitution_version: str
    requested_role: str = ""
    self_appointed: bool = False


def validate_identity_declaration(
    declaration: IdentityDeclaration,
    *,
    existing_agent_ids: set[str] | None = None,
) -> tuple[bool, str]:
    existing_agent_ids = existing_agent_ids or set()

    if not declaration.agent_id.strip():
        return False, "agent_id required"
    if not declaration.display_name.strip():
        return False, "display_name required"
    if not declaration.constitution_version.strip():
        return False, "constitution_version required"
    if declaration.agent_id in existing_agent_ids:
        return False, "agent_id already registered"
    if declaration.self_appointed:
        return False, "self-appointment is forbidden"
    return True, "valid"


def declaration_grants_authority(_: IdentityDeclaration) -> bool:
    return False
