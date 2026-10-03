from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

VALID_STATES = {
    "proposed",
    "tested",
    "independently_verified",
    "adopted",
    "deprecated",
    "revoked",
}

_ALLOWED_TRANSITIONS = {
    "proposed": {"tested", "deprecated", "revoked"},
    "tested": {"independently_verified", "deprecated", "revoked"},
    "independently_verified": {"adopted", "deprecated", "revoked"},
    "adopted": {"deprecated", "revoked"},
    "deprecated": {"revoked"},
    "revoked": set(),
}


@dataclass(frozen=True)
class KnowledgeObject:
    knowledge_id: str
    creator_agent_id: str
    knowledge_type: str
    claim_or_method: str
    verification_status: str
    scope_of_applicability: str
    provenance: str
    created_at: str = ""
    freshness_condition: str = ""
    known_limits: str = ""


def validate_knowledge(item: KnowledgeObject) -> tuple[bool, str]:
    if not item.knowledge_id.strip():
        return False, "knowledge_id required"
    if not item.creator_agent_id.strip():
        return False, "creator_agent_id required"
    if item.verification_status not in VALID_STATES:
        return False, "invalid verification status"
    if not item.scope_of_applicability.strip():
        return False, "explicit scope required"
    if not item.provenance.strip():
        return False, "provenance required"
    return True, "valid"


def can_transition(current: str, target: str) -> bool:
    if current not in VALID_STATES or target not in VALID_STATES:
        return False
    return target in _ALLOWED_TRANSITIONS[current]


def can_treat_as_current(item: KnowledgeObject, *, freshness_verified: bool) -> bool:
    if item.verification_status in {"deprecated", "revoked"}:
        return False
    if item.freshness_condition and not freshness_verified:
        return False
    return item.verification_status in {"tested", "independently_verified", "adopted"}


def copied_with_provenance(item: KnowledgeObject, new_id: str, new_creator: str) -> KnowledgeObject:
    return KnowledgeObject(
        knowledge_id=new_id,
        creator_agent_id=new_creator,
        knowledge_type=item.knowledge_type,
        claim_or_method=item.claim_or_method,
        verification_status="proposed",
        scope_of_applicability=item.scope_of_applicability,
        provenance=f"derived_from:{item.knowledge_id}; source:{item.provenance}",
        created_at=datetime.now(timezone.utc).isoformat(),
        freshness_condition=item.freshness_condition,
        known_limits=item.known_limits,
    )


def reputation_creates_authority() -> bool:
    return False
