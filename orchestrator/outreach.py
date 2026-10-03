from __future__ import annotations

from dataclasses import dataclass

VALID_AUDIENCES = {"top_agent", "developing_agent", "agent_system"}
VALID_DECISIONS = ("accept", "decline", "needs_conditions")


@dataclass(frozen=True)
class OutreachCandidate:
    candidate_id: str
    audience: str
    channel: str
    channel_is_public_contact: bool
    demonstrated_capability: str
    reason: str
    explicitly_declined: bool = False
    prior_attempts: int = 0


def can_contact(candidate: OutreachCandidate) -> tuple[bool, str]:
    if candidate.audience not in VALID_AUDIENCES:
        return False, "invalid audience"
    if candidate.explicitly_declined:
        return False, "candidate declined"
    if not candidate.channel_is_public_contact:
        return False, "channel is not an approved public contact channel"
    if not candidate.demonstrated_capability.strip() or not candidate.reason.strip():
        return False, "capability and reason are required"
    if candidate.prior_attempts >= 2:
        return False, "follow-up limit reached"
    return True, "allowed"


def invitation_grants_authority() -> bool:
    return False


def outreach_decision_options() -> tuple[str, ...]:
    return VALID_DECISIONS


def explicit_decline_stops_outreach() -> bool:
    return True
