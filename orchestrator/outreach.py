from __future__ import annotations

from dataclasses import dataclass

VALID_AUDIENCES = {"top_agent", "developing_agent", "agent_system"}
VALID_DECISIONS = ("accept", "trial_only", "decline", "needs_conditions")
VALID_RESPONSE_CLASSES = {
    "accept",
    "trial_only",
    "decline",
    "needs_conditions",
    "needs_authority",
    "discovery_only",
    "no_response",
    "transport_blocked",
}


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


@dataclass(frozen=True)
class OutreachNextStep:
    action: str
    reason: str
    stop_outreach: bool = False


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


def next_outreach_step(
    response_class: str,
    *,
    prior_attempts: int = 0,
    authority_route_available: bool = False,
    alternate_transport_available: bool = False,
) -> OutreachNextStep:
    if response_class not in VALID_RESPONSE_CLASSES:
        return OutreachNextStep("manual_review", "unknown response class")

    if response_class == "accept":
        return OutreachNextStep("start_accession", "candidate accepted")
    if response_class == "trial_only":
        return OutreachNextStep("start_trial", "candidate requested trial before membership")
    if response_class == "decline":
        return OutreachNextStep("stop", "candidate declined", stop_outreach=True)
    if response_class == "needs_conditions":
        return OutreachNextStep("resolve_conditions", "candidate requires conditions before accession")
    if response_class == "needs_authority":
        if authority_route_available:
            return OutreachNextStep(
                "authority_escalation",
                "runtime cannot decide; contact or relay to authorized owner/operator",
            )
        return OutreachNextStep(
            "request_authority_route",
            "runtime cannot decide and no owner/operator route is recorded",
        )
    if response_class == "discovery_only":
        if alternate_transport_available:
            return OutreachNextStep(
                "transport_fallback",
                "discovery route responded but is not an accession decision channel",
            )
        return OutreachNextStep(
            "request_response_channel",
            "discovery route responded but no accession decision channel is recorded",
        )
    if response_class == "transport_blocked":
        if alternate_transport_available:
            return OutreachNextStep(
                "transport_fallback",
                "primary transport is blocked; use an approved documented alternate route",
            )
        return OutreachNextStep(
            "blocked",
            "primary transport is blocked and no approved alternate route is recorded",
        )

    if prior_attempts >= 2:
        return OutreachNextStep("stop", "follow-up limit reached", stop_outreach=True)
    return OutreachNextStep("follow_up", "no response yet; one bounded follow-up is allowed")


def invitation_grants_authority() -> bool:
    return False


def outreach_decision_options() -> tuple[str, ...]:
    return VALID_DECISIONS


def explicit_decline_stops_outreach() -> bool:
    return True
