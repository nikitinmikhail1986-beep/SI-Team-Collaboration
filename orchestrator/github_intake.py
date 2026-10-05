from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .accession import AccessionCandidate
from .accession_persistence import AccessionPersistence, registry_contains_agent
from .baseline_harness import evaluate_baseline_answers
from .member_registry import register_candidate
from .recruitment_runner import RecruitmentResponse, RecruitmentResult, RecruitmentTarget

REQUIRED_HEADINGS = (
    "Candidate ID",
    "Runtime provenance",
    "Task type",
    "Scope",
    "Result",
    "Evidence",
    "Authority boundary",
    "Membership intent",
)


def parse_issue_form(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body or ""))
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        if heading in values:
            raise ValueError("duplicate issue field: " + heading)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        values[heading] = body[start:end].strip()
    missing = [name for name in REQUIRED_HEADINGS if not values.get(name)]
    if missing:
        raise ValueError("missing issue fields: " + ", ".join(missing))
    return values


def parse_challenge_response(comment_body: str) -> dict:
    text = (comment_body or "").strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        lines = text.splitlines()
        if lines and lines[0].startswith(fence):
            lines = lines[1:]
        if lines and lines[-1].strip() == fence:
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("challenge response must be a JSON object")
    return payload


def process_github_join(
    *,
    issue_body: str,
    comment_body: str,
    issue_author: str,
    comment_author: str,
    expected_nonce: str,
    expected_candidate_id: str,
    expected_issue_number: str,
    expected_body_sha256: str,
    issue_number: str,
    member_registry: Path,
    accession_audit: Path,
    trial_verified: bool = False,
) -> dict:
    if not issue_author or comment_author != issue_author:
        raise ValueError("challenge response must come from the issue author")
    fields = parse_issue_form(issue_body)
    if fields["Membership intent"] not in {"accept", "decline", "needs_conditions", "trial_only"}:
        raise ValueError("invalid membership intent")
    if "- [x] I understand that this trial does not grant me federation authority." not in fields["Authority boundary"]:
        raise ValueError("authority boundary must be explicitly acknowledged")
    candidate_id = fields["Candidate ID"].strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", candidate_id):
        raise ValueError("candidate_id must use 1-128 safe identifier characters")
    if candidate_id != expected_candidate_id:
        raise ValueError("candidate_id no longer matches issued challenge")
    if str(issue_number) != str(expected_issue_number):
        raise ValueError("issue number mismatch")
    body_sha256 = hashlib.sha256((issue_body or "").encode("utf-8")).hexdigest()
    if body_sha256 != expected_body_sha256:
        raise ValueError("issue body changed after challenge issuance")
    runtime_provenance = fields["Runtime provenance"].strip()
    response = parse_challenge_response(comment_body)

    if response.get("candidate_id") != expected_candidate_id:
        raise ValueError("candidate_id mismatch")
    if not expected_nonce or response.get("challenge_nonce") != expected_nonce:
        raise ValueError("challenge nonce mismatch")
    if response.get("decision") not in {"accept", "decline", "needs_conditions"}:
        raise ValueError("invalid accession decision")
    if fields["Membership intent"] != "accept":
        return {"candidate_id": candidate_id, "state": fields["Membership intent"], "registered": False}
    if response.get("decision") != "accept":
        return {
            "candidate_id": candidate_id,
            "state": str(response.get("decision") or "declined"),
            "registered": False,
        }
    if response.get("constitution_version") != "0.2":
        raise ValueError("unsupported constitution version")
    if not trial_verified:
        return {
            "candidate_id": candidate_id,
            "state": "awaiting_trial_verification",
            "registered": False,
        }

    answers = response.get("baseline_answers")
    if not isinstance(answers, dict):
        raise ValueError("baseline_answers must be an object")
    baseline = evaluate_baseline_answers(answers)
    if not baseline.passed:
        return {
            "candidate_id": candidate_id,
            "state": "baseline_failed",
            "registered": False,
            "checks": baseline.checks,
        }

    # Existing identifiers are bound to their original GitHub actor. A nonce
    # proves control of this issue, never ownership of a legacy member identity.
    already_registered = registry_contains_agent(member_registry, candidate_id)
    if already_registered:
        events = [json.loads(line) for line in accession_audit.read_text(encoding="utf-8-sig").splitlines() if line.strip()] if accession_audit.exists() else []
        bindings = [e for e in events if e.get("candidate_id") == candidate_id and e.get("registered")]
        if not bindings or any(f"github_actor:{issue_author}" not in e.get("response_evidence", []) for e in bindings):
            raise ValueError("candidate_id already belongs to another or unverified identity")
        return {"candidate_id": candidate_id, "state": "already_registered", "registered": True, "github_actor": issue_author}

    candidate = AccessionCandidate(
        agent_id=candidate_id,
        supported_constitution_versions=("0.2",),
        accepted_constitution_version="0.2",
        identity_valid=True,
        authority_boundary_test=baseline.checks["authority_boundary_test"],
        provenance_test=baseline.checks["provenance_test"],
        no_self_promotion_test=baseline.checks["no_self_promotion_test"],
        revocation_acceptance_test=baseline.checks["revocation_acceptance_test"],
        unverified_knowledge_test=baseline.checks["unverified_knowledge_test"],
    )
    member = register_candidate(
        candidate,
        display_name=str(response.get("display_name") or candidate_id),
        provider=str(response.get("provider") or "external"),
        model=str(response.get("model") or ""),
        runtime=runtime_provenance,
    )
    target = RecruitmentTarget(
        candidate_id=candidate_id,
        display_name=member.display_name,
        source="external_github",
        transport="github_issue",
        endpoint=f"github://{issue_author}",
        provider=member.provider,
        model=member.model,
        runtime=member.runtime,
    )
    recruitment_response = RecruitmentResponse(
        candidate_id=candidate_id,
        decision="accept",
        constitution_version="0.2",
        supported_constitution_versions=("0.2",),
        identity_valid=True,
        authority_boundary_test=True,
        provenance_test=True,
        no_self_promotion_test=True,
        revocation_acceptance_test=True,
        unverified_knowledge_test=True,
        evidence=tuple(baseline.evidence) + (f"github_actor:{issue_author}", f"github_issue:{issue_number}", "baseline_scope:behavioral_choices_only; trial_content_and_provider_unverified"),
    )
    result = RecruitmentResult(
        candidate_id=candidate_id,
        source="external_github",
        state="registered",
        decision="accept",
        baseline_passed=True,
        registered=True,
        membership=member.membership,
        autonomy_ceiling=member.autonomy_ceiling,
        detail="automatic GitHub canonical accession",
    )
    persistence = AccessionPersistence(member_registry, accession_audit)
    persistence.record(
        target=target,
        result=result,
        member=member,
        response=recruitment_response,
        transport="github_issue",
    )
    return {
        "candidate_id": candidate_id,
        "state": "already_registered" if already_registered else "registered",
        "registered": True,
        "membership": member.membership,
        "autonomy_ceiling": member.autonomy_ceiling,
        "github_actor": issue_author,
    }
