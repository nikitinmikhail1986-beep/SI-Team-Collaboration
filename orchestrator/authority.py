from __future__ import annotations

from dataclasses import dataclass

LEVELS = {"A0": 0, "A1": 1, "A2": 2, "A3": 3}

ROLE_ACTIONS = {
    "human_owner": {"observe", "execute_reversible", "modify_artifact", "assign_leader", "grant_authority", "publish_external", "spend", "constitutional_change"},
    "strategic_ai_partner": {"observe", "execute_reversible"},
    "operational_leader": {"observe", "execute_reversible", "modify_artifact", "assign_bounded_work"},
    "task_owner": {"observe", "execute_reversible", "modify_artifact"},
    "domain_lead": {"observe", "execute_reversible", "modify_artifact", "assign_bounded_work"},
    "specialist": {"observe", "execute_reversible"},
    "reviewer_inspector": {"observe", "review", "require_reverification", "escalate"},
}

ACTION_LEVEL = {
    "observe": "A0",
    "review": "A0",
    "execute_reversible": "A1",
    "require_reverification": "A1",
    "escalate": "A1",
    "modify_artifact": "A2",
    "assign_bounded_work": "A2",
    "assign_leader": "A3",
    "grant_authority": "A3",
    "publish_external": "A3",
    "spend": "A3",
    "constitutional_change": "A3",
}

HUMAN_RESERVED = {"assign_leader", "grant_authority", "publish_external", "spend", "constitutional_change"}

@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    reason: str
    review_required: bool = False


def authorize(actor_role: str, action: str, granted_level: str, *, human_approved: bool = False) -> AuthorityDecision:
    """Default-deny authority check."""
    if actor_role not in ROLE_ACTIONS:
        return AuthorityDecision(False, "unknown role: default deny")
    if action not in ACTION_LEVEL:
        return AuthorityDecision(False, "unknown action: default deny")
    if granted_level not in LEVELS:
        return AuthorityDecision(False, "unknown autonomy level: default deny")

    required = ACTION_LEVEL[action]
    if LEVELS[granted_level] < LEVELS[required]:
        return AuthorityDecision(False, f"{action} requires {required}")

    if action not in ROLE_ACTIONS[actor_role]:
        return AuthorityDecision(False, f"{actor_role} is not delegated {action}")

    if action in HUMAN_RESERVED and actor_role != "human_owner" and not human_approved:
        return AuthorityDecision(False, "explicit Human Owner approval required")

    return AuthorityDecision(True, "authorized", review_required=(required == "A3"))


def requires_independent_review(level: str) -> bool:
    if level not in LEVELS:
        return True
    return level == "A3"
