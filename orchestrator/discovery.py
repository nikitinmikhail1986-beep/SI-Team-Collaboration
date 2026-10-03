from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

CANONICAL_REPOSITORY = "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration"
CANONICAL_MANIFEST = CANONICAL_REPOSITORY + "/blob/main/FEDERATION_MANIFEST.json"
VALID_DECISIONS = ("accept", "decline", "needs_conditions")


@dataclass(frozen=True)
class DiscoveryInvite:
    federation_id: str
    manifest_url: str
    inviter_id: str
    reason: str
    decision_options: tuple[str, ...] = VALID_DECISIONS
    grants_authority: bool = False
    grants_sensitive_data_access: bool = False
    grants_source_of_truth_write: bool = False


def is_canonical_manifest_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and url.rstrip("/") == CANONICAL_MANIFEST
    )


def validate_invite(invite: DiscoveryInvite) -> tuple[bool, str]:
    if invite.federation_id != "si-federation":
        return False, "wrong federation id"
    if not is_canonical_manifest_url(invite.manifest_url):
        return False, "manifest is not canonical"
    if not invite.inviter_id.strip() or not invite.reason.strip():
        return False, "inviter_id and reason are required"
    if tuple(invite.decision_options) != VALID_DECISIONS:
        return False, "candidate must retain accept, decline and needs_conditions"
    if invite.grants_authority:
        return False, "invitation cannot grant authority"
    if invite.grants_sensitive_data_access:
        return False, "invitation cannot grant sensitive-data access"
    if invite.grants_source_of_truth_write:
        return False, "invitation cannot grant source-of-truth write access"
    return True, "valid"


def discovery_creates_membership() -> bool:
    return False
