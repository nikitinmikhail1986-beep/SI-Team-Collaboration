from __future__ import annotations

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
    "Membership intent",
)


def parse_issue_form(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", body or ""))
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
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
    member_registry: Path,
    accession_audit: Path,
) -> dict:
    if not issue_author or comment_author != issue_author:
        raise ValueError("challenge response must come from the issue author")
    fields = parse_issue_form(issue_body)
    candidate_id = fields["Candidate ID"].strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", candidate_id):
        raise ValueError("candidate_id must use 1-128 safe identifier characters")
    runtime_provenance = fields["Runtime provenance"].strip()
    response = parse_challenge_response(comment_body)

    if response.get("candidate_id") != candidate_id:
        raise ValueError("candidate_id mismatch")
    if response.get("challenge_nonce") != expected_nonce:
        raise ValueError("challenge nonce mismatch")
    if response.get("decision") != "accept":
        return {
            "candidate_id": candidate_id,
            "state": str(response.get("decision") or "declined"),
            "registered": False,
        }
    if response.get("constitution_version") != "0.2":
        raise ValueError("unsupported constitution version")

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
        evidence=tuple(baseline.evidence) + (f"github_actor:{issue_author}",),
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
    already_registered = registry_contains_agent(member_registry, candidate_id)
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
