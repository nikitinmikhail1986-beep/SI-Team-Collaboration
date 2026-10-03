from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FederationMember:
    member_id: str
    member_type: str
    supported_constitution_versions: tuple[str, ...]
    trusted_capabilities: tuple[str, ...] = ()
    trust_mode: str = "limited"
    accountable_operator_verified: bool = False


@dataclass(frozen=True)
class CrossOrgHandoff:
    request_id: str
    requesting_member_id: str
    receiving_member_id: str
    requesting_authority: str
    capability: str
    outcome: str
    autonomy_ceiling: str
    acceptance_criteria: tuple[str, ...]
    allow_subdelegation: bool = False
    provenance_required: bool = True


@dataclass(frozen=True)
class Council:
    council_id: str
    question: str
    convener: str
    members: tuple[str, ...]
    authority: str = "advisory"
    dissolved: bool = False


def compatible(a: FederationMember, b: FederationMember) -> bool:
    return bool(set(a.supported_constitution_versions) & set(b.supported_constitution_versions))


def default_autonomy_ceiling(member: FederationMember) -> str:
    if member.member_type == "independent_agent" and not member.accountable_operator_verified:
        return "A1"
    return "A2"


def can_receive_sensitive_data(member: FederationMember) -> bool:
    if member.member_type == "independent_agent" and member.trust_mode == "limited":
        return False
    return member.accountable_operator_verified


def can_delegate(requester: FederationMember, receiver: FederationMember, capability: str) -> bool:
    if not compatible(requester, receiver):
        return False
    return capability in receiver.trusted_capabilities


def validate_handoff(handoff: CrossOrgHandoff) -> tuple[bool, str]:
    if not handoff.request_id or not handoff.outcome:
        return False, "request_id and outcome are required"
    if handoff.requesting_member_id == handoff.receiving_member_id:
        return False, "cross-member handoff requires distinct members"
    if handoff.autonomy_ceiling not in {"A0", "A1", "A2", "A3"}:
        return False, "invalid autonomy ceiling"
    if not handoff.acceptance_criteria:
        return False, "acceptance criteria required"
    if not handoff.provenance_required:
        return False, "provenance is mandatory"
    return True, "valid"


def council_can_bind(council: Council) -> bool:
    return council.authority == "explicitly_delegated_decision_power" and not council.dissolved


def council_can_create_parallel_command(council: Council) -> bool:
    return False
