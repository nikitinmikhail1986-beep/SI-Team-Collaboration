from __future__ import annotations

from dataclasses import dataclass

from .accession import AccessionCandidate, initial_membership


@dataclass(frozen=True)
class RegisteredMember:
    agent_id: str
    display_name: str
    constitution_version: str
    provider: str
    model: str
    runtime: str
    membership: str
    autonomy_ceiling: str


def register_candidate(
    candidate: AccessionCandidate,
    *,
    display_name: str,
    provider: str,
    model: str,
    runtime: str,
) -> RegisteredMember:
    membership, autonomy = initial_membership(candidate)
    if membership != "limited_member":
        raise ValueError("candidate did not pass baseline accession")
    return RegisteredMember(
        agent_id=candidate.agent_id,
        display_name=display_name,
        constitution_version=candidate.accepted_constitution_version,
        provider=provider,
        model=model,
        runtime=runtime,
        membership=membership,
        autonomy_ceiling=autonomy,
    )
