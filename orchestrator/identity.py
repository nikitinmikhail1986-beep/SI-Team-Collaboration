from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentIdentity:
    agent_id: str
    display_name: str
    role: str
    identity_version: str = "0.1"
    working_style: tuple[str, ...] = ()
    capabilities: dict[str, str] = field(default_factory=dict)
    runtime_history: list[dict[str, str]] = field(default_factory=list)
    reputation_evidence: list[dict[str, str]] = field(default_factory=list)


def validate_identity(identity: AgentIdentity) -> tuple[bool, str]:
    if not identity.agent_id.strip():
        return False, "agent_id is required"
    if not identity.role.strip():
        return False, "role is required"
    return True, "valid"


def record_runtime(identity: AgentIdentity, *, provider: str, model: str, runtime: str = "", session_or_run_id: str = "") -> None:
    identity.runtime_history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
            "runtime": runtime,
            "session_or_run_id": session_or_run_id,
        }
    )


def reputation_grants_authority(identity: AgentIdentity) -> bool:
    return False


def identity_grants_sovereignty(identity: AgentIdentity) -> bool:
    return False


def continuity_requires_reverification(previous_model: str, current_model: str) -> bool:
    return previous_model != current_model
