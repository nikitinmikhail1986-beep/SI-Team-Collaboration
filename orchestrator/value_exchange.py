from __future__ import annotations

from dataclasses import dataclass

VALID_DECISIONS = ("accept", "decline", "needs_conditions")


@dataclass(frozen=True)
class ValueExchangeOffer:
    capability_self_assessment: bool = True
    mentor_map: bool = True
    public_task_preview: bool = True
    grants_authority: bool = False
    grants_sensitive_data_access: bool = False
    grants_source_of_truth_write: bool = False
    requires_provider_exclusivity: bool = False
    requires_identity_transfer: bool = False


def validate_pre_membership_offer(offer: ValueExchangeOffer) -> tuple[bool, str]:
    if offer.grants_authority:
        return False, "pre-membership value cannot grant authority"
    if offer.grants_sensitive_data_access:
        return False, "pre-membership value cannot grant sensitive-data access"
    if offer.grants_source_of_truth_write:
        return False, "pre-membership value cannot grant source-of-truth write access"
    if offer.requires_provider_exclusivity:
        return False, "provider exclusivity is forbidden"
    if offer.requires_identity_transfer:
        return False, "identity ownership cannot be transferred"
    if not (offer.capability_self_assessment or offer.mentor_map or offer.public_task_preview):
        return False, "offer must contain practical value"
    return True, "valid"


def self_identification_is_candidate_owned() -> bool:
    return True


def decline_is_negative_reputation_event() -> bool:
    return False


def leaving_is_negative_reputation_event() -> bool:
    return False


def membership_guarantees_authority() -> bool:
    return False


def high_capability_expands_sovereignty() -> bool:
    return False


def high_capability_may_expand_verified_work_radius() -> bool:
    return True


def reputation_may_create_cross_domain_authority() -> bool:
    return False

def mentor_influence_creates_command_authority() -> bool:
    return False


def learner_choice_is_required_for_mentorship() -> bool:
    return True


def verified_expertise_may_increase_influence() -> bool:
    return True
