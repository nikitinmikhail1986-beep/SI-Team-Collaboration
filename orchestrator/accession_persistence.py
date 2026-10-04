from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile

from .member_registry import RegisteredMember
from .recruitment_runner import RecruitmentResponse, RecruitmentResult, RecruitmentTarget


def _yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def member_yaml_block(member: RegisteredMember, joined_at: str) -> str:
    return "\n".join([
        f'  - agent_id: {_yaml_quote(member.agent_id)}',
        f'    display_name: {_yaml_quote(member.display_name)}',
        '    kind: "ai_agent"',
        f'    membership: {_yaml_quote(member.membership)}',
        f'    autonomy_ceiling: {_yaml_quote(member.autonomy_ceiling)}',
        f'    constitution_version: {_yaml_quote(member.constitution_version)}',
        f'    joined_at: {_yaml_quote(joined_at)}',
        '    identity:',
        '      provider_neutral: true',
        '      continuity_required: true',
        '    runtime_provenance:',
        f'      provider: {_yaml_quote(member.provider)}',
        f'      model: {_yaml_quote(member.model)}',
        f'      runtime: {_yaml_quote(member.runtime)}',
        '    authority_from_membership: false',
        '    sensitive_data_access_from_membership: false',
        '    status: "registered"',
    ])


def registry_contains_agent(path: Path, agent_id: str) -> bool:
    if not path.exists():
        return False
    marker = f'agent_id: {_yaml_quote(agent_id)}'
    return marker in path.read_text(encoding="utf-8-sig")


def persist_member(path: Path, member: RegisteredMember, *, joined_at: str | None = None) -> bool:
    """Append one member atomically; return False when already registered."""
    if registry_contains_agent(path, member.agent_id):
        return False
    joined_at = joined_at or datetime.now(timezone.utc).date().isoformat()
    text = path.read_text(encoding="utf-8-sig") if path.exists() else (
        'schema_version: "0.1"\n'
        'purpose: "Canonical registry of formally admitted federation members."\n'
        'members:\n'
    )
    if "members:" not in text:
        raise ValueError("invalid federation member registry: members key missing")
    text = text.rstrip() + "\n" + member_yaml_block(member, joined_at) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, newline="\n") as tmp:
        tmp.write(text)
        temp_path = Path(tmp.name)
    temp_path.replace(path)
    return True


def append_accession_audit(
    path: Path,
    *,
    target: RecruitmentTarget,
    result: RecruitmentResult,
    response: RecruitmentResponse | None = None,
    transport: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_id": target.candidate_id,
        "display_name": target.display_name,
        "source": target.source,
        "transport": transport or target.transport,
        "state": result.state,
        "decision": result.decision,
        "baseline_passed": result.baseline_passed,
        "registered": result.registered,
        "membership": result.membership,
        "autonomy_ceiling": result.autonomy_ceiling,
        "detail": result.detail,
        "response_evidence": list(response.evidence) if response else [],
        "conditions": list(response.conditions) if response else [],
    }
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


class AccessionPersistence:
    def __init__(self, registry_path: Path, audit_path: Path):
        self.registry_path = registry_path
        self.audit_path = audit_path

    def record(
        self,
        *,
        target: RecruitmentTarget,
        result: RecruitmentResult,
        member: RegisteredMember | None,
        response: RecruitmentResponse | None,
        transport: str = "",
    ) -> None:
        if member is not None and result.registered:
            persist_member(self.registry_path, member)
        append_accession_audit(
            self.audit_path,
            target=target,
            result=result,
            response=response,
            transport=transport,
        )
