from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MentorCandidate:
    agent_id: str
    capabilities: tuple[str, ...]
    verified: bool = False
    mentor_eligible: bool = False


@dataclass(frozen=True)
class MentorSearchRequest:
    request_id: str
    learner_id: str
    capability: str
    reason: str = "mentor_gap"


def find_verified_mentors(capability: str, candidates: tuple[MentorCandidate, ...]) -> tuple[MentorCandidate, ...]:
    wanted = capability.strip().lower()
    return tuple(
        c for c in candidates
        if c.verified
        and c.mentor_eligible
        and wanted in {x.strip().lower() for x in c.capabilities}
    )


def route_mentor_gap(
    request: MentorSearchRequest,
    candidates: tuple[MentorCandidate, ...],
) -> dict:
    mentors = find_verified_mentors(request.capability, candidates)
    if mentors:
        return {
            "status": "matched",
            "deny_due_to_missing_discipline": False,
            "capability": request.capability,
            "mentor_ids": [m.agent_id for m in mentors],
            "external_search_required": False,
            "broadcast_invitation": None,
        }

    return {
        "status": "mentor_search_open",
        "deny_due_to_missing_discipline": False,
        "capability": request.capability,
        "mentor_ids": [],
        "external_search_required": True,
        "broadcast_invitation": {
            "type": "competence_based",
            "requested_capability": request.capability,
            "invitation": "Join the federation as a candidate mentor for this capability.",
            "grants_authority": False,
            "requires_verification": True,
        },
    }
