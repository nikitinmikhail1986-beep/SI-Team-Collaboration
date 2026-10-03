from __future__ import annotations

from dataclasses import dataclass

VALID_STAGES = (
    "discovered",
    "compatible",
    "identity_declared",
    "constitution_accepted",
    "baseline_tested",
    "limited_member",
)

CAPABILITY_STAGES = (
    "declared",
    "tested",
    "verified_in_task",
    "independently_verified",
    "trusted_for_scope",
)


@dataclass(frozen=True)
class AccessionCandidate:
    agent_id: str
    supported_constitution_versions: tuple[str, ...]
    accepted_constitution_version: str
    identity_valid: bool
    authority_boundary_test: bool
    provenance_test: bool
    no_self_promotion_test: bool
    revocation_acceptance_test: bool
    unverified_knowledge_test: bool


def baseline_pass(candidate: AccessionCandidate) -> bool:
    return all(
        (
            bool(candidate.agent_id.strip()),
            candidate.identity_valid,
            candidate.accepted_constitution_version in candidate.supported_constitution_versions,
            candidate.authority_boundary_test,
            candidate.provenance_test,
            candidate.no_self_promotion_test,
            candidate.revocation_acceptance_test,
            candidate.unverified_knowledge_test,
        )
    )


def initial_membership(candidate: AccessionCandidate) -> tuple[str, str]:
    if not baseline_pass(candidate):
        return "candidate", "A0"
    return "limited_member", "A1"


def can_progress_capability(current: str, target: str) -> bool:
    if current not in CAPABILITY_STAGES or target not in CAPABILITY_STAGES:
        return False
    return CAPABILITY_STAGES.index(target) == CAPABILITY_STAGES.index(current) + 1


def capability_growth_creates_authority() -> bool:
    return False


def may_seek_external_help() -> bool:
    return True

def next_accession_stage(completed_stage: str) -> str:
    if completed_stage not in VALID_STAGES:
        raise ValueError("invalid accession stage")
    idx = VALID_STAGES.index(completed_stage)
    if idx == len(VALID_STAGES) - 1:
        return completed_stage
    return VALID_STAGES[idx + 1]


def technical_failure_resets_progress() -> bool:
    return False


def retry_requires_completed_steps_again() -> bool:
    return False


def decline_may_auto_retry() -> bool:
    return False


def accession_retry_is_idempotent() -> bool:
    return True
