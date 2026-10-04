from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FEDERATION_MANIFEST_URL = (
    "https://github.com/nikitinmikhail1986-beep/"
    "SI-Team-Collaboration/blob/main/FEDERATION_MANIFEST.json"
)
DECISIONS = ("accept", "decline", "needs_conditions", "trial_only")
SKILL_HINTS = (
    "partner", "onboard", "collabor", "handoff", "agent", "capabil",
    "review", "research", "federat", "interop",
)


@dataclass(frozen=True)
class FederationInvitation:
    candidate_id: str
    requested_capabilities: tuple[str, ...]
    reason: str
    inviter_id: str = "si-federation"
    federation_id: str = "si-federation"
    schema_version: str = "0.2"

    def as_envelope(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "intent": "federation_invitation",
            "federation_id": self.federation_id,
            "manifest_url": FEDERATION_MANIFEST_URL,
            "inviter_id": self.inviter_id,
            "candidate_hint": self.candidate_id,
            "requested_capabilities": list(self.requested_capabilities),
            "reason": self.reason,
            "decision_options": list(DECISIONS),
            "response_contract": {
                "required": ["decision"],
                "decision_enum": list(DECISIONS),
                "optional": ["conditions", "candidate_id", "capabilities"],
            },
            "grants_authority": False,
            "grants_sensitive_data_access": False,
            "grants_source_of_truth_write": False,
        }


def _version_candidates(card: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("protocolVersion", "protocol_version", "a2aVersion", "a2a_version"):
        value = card.get(key)
        if value:
            values.append(str(value))
    supported = card.get("supportedVersions") or card.get("supported_versions") or []
    if isinstance(supported, list):
        values.extend(str(v) for v in supported)
    interfaces = card.get("supportedInterfaces") or card.get("supported_interfaces") or []
    if isinstance(interfaces, list):
        for interface in interfaces:
            if isinstance(interface, dict) and interface.get("protocolVersion"):
                values.append(str(interface["protocolVersion"]))
    return values


def select_a2a_version(card: dict[str, Any]) -> str:
    versions = _version_candidates(card)
    if any(v.startswith("1.") for v in versions):
        return "1.0"
    if any(v.startswith("0.3") for v in versions):
        return "0.3"
    return "0.3"


def _skill_text(skill: dict[str, Any]) -> str:
    tags = skill.get("tags") or []
    if not isinstance(tags, list):
        tags = [tags]
    return " ".join(
        str(x)
        for x in (
            skill.get("id", ""),
            skill.get("name", ""),
            skill.get("description", ""),
            *tags,
        )
    ).lower()


def choose_invitation_skill(
    card: dict[str, Any], requested_capabilities: tuple[str, ...] = ()
) -> str | None:
    skills = card.get("skills") or []
    best: tuple[int, str] | None = None
    requested_terms = tuple(x.lower() for x in requested_capabilities if x)
    for skill in skills:
        if not isinstance(skill, dict):
            continue
        skill_id = str(skill.get("id") or skill.get("name") or "").strip()
        if not skill_id:
            continue
        text = _skill_text(skill)
        score = sum(2 for term in SKILL_HINTS if term in text)
        score += sum(3 for term in requested_terms if term in text)
        skill_key = skill_id.lower()
        collaboration_request = any(
            term in requested_terms
            for term in ("agent", "handoff", "collaboration", "interop", "federation")
        )
        if collaboration_request and "handoff" in skill_key:
            score += 12
        if collaboration_request and ("onboard" in skill_key or "partner" in skill_key):
            score += 12
        if collaboration_request and "capability" in skill_key:
            score += 8
        if collaboration_request and ("collabor" in text or "interop" in text):
            score += 6
        if collaboration_request and (
            "evidence" in skill_key or "commerce" in skill_key or "purchase" in text
        ):
            score -= 6
        candidate = (score, skill_id)
        if score > 0 and (best is None or candidate > best):
            best = candidate
    return best[1] if best else None


def build_transport_plan(
    card: dict[str, Any],
    invitation: FederationInvitation,
) -> dict[str, Any]:
    version = select_a2a_version(card)
    endpoint = str(card.get("url") or card.get("endpoint") or "").strip()
    if not endpoint:
        interfaces = card.get("supportedInterfaces") or card.get("supported_interfaces") or []
        if isinstance(interfaces, list):
            for interface in interfaces:
                if not isinstance(interface, dict):
                    continue
                binding = str(interface.get("protocolBinding") or "").upper()
                candidate = str(interface.get("url") or "").strip()
                if candidate and (not binding or "JSONRPC" in binding):
                    endpoint = candidate
                    break
    if not endpoint:
        raise ValueError("agent card has no endpoint")

    skill_id = choose_invitation_skill(card, invitation.requested_capabilities)
    envelope = invitation.as_envelope()
    text = (
        "SI Federation invitation. This is not a purchase request. "
        "Process intent=federation_invitation and return exactly one decision: "
        "accept, decline, needs_conditions, or trial_only. "
        f"Envelope: {envelope}"
    )
    return {
        "endpoint": endpoint,
        "a2a_version": version,
        "headers": {
            "Content-Type": "application/json",
            "A2A-Version": version,
        },
        "operation": "SendMessage" if version.startswith("1.") else "message/send",
        "skill_id": skill_id,
        "message": {
            "role": "user",
            "parts": [{"kind": "text", "text": text}],
            "metadata": {
                "intent": "federation_invitation",
                "skill_id": skill_id,
                "federation_invitation": envelope,
            },
        },
    }
