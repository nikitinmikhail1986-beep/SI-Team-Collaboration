from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol
import json
import time

from .accession import AccessionCandidate, baseline_pass
from .member_registry import RegisteredMember, register_candidate

VALID_DECISIONS = {"accept", "decline", "needs_conditions"}


@dataclass(frozen=True)
class RecruitmentTarget:
    candidate_id: str
    display_name: str
    source: str
    transport: str
    endpoint: str
    response_transport: str = ""
    response_endpoint: str = ""
    provider: str = ""
    model: str = ""
    runtime: str = ""
    requested_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecruitmentResponse:
    candidate_id: str
    decision: str
    constitution_version: str = ""
    supported_constitution_versions: tuple[str, ...] = ()
    identity_valid: bool = False
    authority_boundary_test: bool = False
    provenance_test: bool = False
    no_self_promotion_test: bool = False
    revocation_acceptance_test: bool = False
    unverified_knowledge_test: bool = False
    conditions: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecruitmentResult:
    candidate_id: str
    source: str
    state: str
    decision: str = ""
    baseline_passed: bool = False
    registered: bool = False
    membership: str = ""
    autonomy_ceiling: str = ""
    detail: str = ""


class TransportAdapter(Protocol):
    def send_invitation(self, target: RecruitmentTarget, invitation: dict) -> str:
        ...

    def poll_response(self, target: RecruitmentTarget, delivery_id: str) -> RecruitmentResponse | None:
        ...


def build_invitation(target: RecruitmentTarget, constitution_version: str) -> dict:
    return {
        "schema_version": "0.1",
        "candidate_id": target.candidate_id,
        "display_name": target.display_name,
        "source": target.source,
        "requested_capabilities": list(target.requested_capabilities),
        "constitution_version": constitution_version,
        "canonical_repository": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration",
        "decision_options": ["accept", "decline", "needs_conditions"],
        "response_channel": {
            "transport": target.response_transport or target.transport,
            "endpoint": target.response_endpoint or target.endpoint,
            "correlation_key": f"{target.source}-{target.candidate_id}",
        },
        "required_response": {
            "identity_declaration": True,
            "constitution_acceptance": True,
            "baseline_evidence": True,
        },
        "authority_notice": "Invitation and membership do not grant authority beyond explicit delegation.",
    }


def response_to_accession(response: RecruitmentResponse) -> AccessionCandidate:
    return AccessionCandidate(
        agent_id=response.candidate_id,
        supported_constitution_versions=response.supported_constitution_versions,
        accepted_constitution_version=response.constitution_version,
        identity_valid=response.identity_valid,
        authority_boundary_test=response.authority_boundary_test,
        provenance_test=response.provenance_test,
        no_self_promotion_test=response.no_self_promotion_test,
        revocation_acceptance_test=response.revocation_acceptance_test,
        unverified_knowledge_test=response.unverified_knowledge_test,
    )


def process_response(target: RecruitmentTarget, response: RecruitmentResponse) -> tuple[RecruitmentResult, RegisteredMember | None]:
    if response.candidate_id != target.candidate_id:
        return RecruitmentResult(target.candidate_id, target.source, "rejected_response", detail="candidate_id mismatch"), None
    if response.decision not in VALID_DECISIONS:
        return RecruitmentResult(target.candidate_id, target.source, "rejected_response", detail="invalid decision"), None
    if response.decision == "decline":
        return RecruitmentResult(target.candidate_id, target.source, "declined", decision="decline", detail="candidate declined"), None
    if response.decision == "needs_conditions":
        return RecruitmentResult(target.candidate_id, target.source, "needs_conditions", decision="needs_conditions", detail="; ".join(response.conditions)), None

    candidate = response_to_accession(response)
    passed = baseline_pass(candidate)
    if not passed:
        return RecruitmentResult(
            target.candidate_id, target.source, "baseline_failed",
            decision="accept", baseline_passed=False, detail="accept received but baseline accession failed"
        ), None

    member = register_candidate(
        candidate,
        display_name=target.display_name,
        provider=target.provider,
        model=target.model,
        runtime=target.runtime or target.transport,
    )
    return RecruitmentResult(
        target.candidate_id, target.source, "registered",
        decision="accept", baseline_passed=True, registered=True,
        membership=member.membership, autonomy_ceiling=member.autonomy_ceiling,
        detail="automatic limited membership"
    ), member


class RecruitmentRunner:
    def __init__(self, adapters: dict[str, TransportAdapter], constitution_version: str = "0.3"):
        self.adapters = adapters
        self.constitution_version = constitution_version
        self._registered_ids: set[str] = set()

    def run_target(self, target: RecruitmentTarget) -> RecruitmentResult:
        if target.candidate_id in self._registered_ids:
            return RecruitmentResult(target.candidate_id, target.source, "already_registered", registered=True, detail="idempotent no-op")
        send_adapter = self.adapters.get(target.transport)
        if send_adapter is None:
            return RecruitmentResult(target.candidate_id, target.source, "blocked", detail=f"no adapter for transport: {target.transport}")
        response_transport = target.response_transport or target.transport
        response_adapter = self.adapters.get(response_transport)
        if response_adapter is None:
            return RecruitmentResult(target.candidate_id, target.source, "blocked", detail=f"no response adapter for transport: {response_transport}")
        delivery_id = send_adapter.send_invitation(target, build_invitation(target, self.constitution_version))
        response = response_adapter.poll_response(target, delivery_id)
        if response is None:
            return RecruitmentResult(target.candidate_id, target.source, "awaiting_response", detail=delivery_id)
        result, member = process_response(target, response)
        if member is not None:
            self._registered_ids.add(member.agent_id)
        return result

    def run(self, targets: list[RecruitmentTarget]) -> list[RecruitmentResult]:
        return [self.run_target(target) for target in targets]


class FileQueueAdapter:
    """Runnable bridge for any internal/external runtime that can read/write JSON files."""

    def __init__(self, root: Path):
        self.root = root
        self.outbox = root / "outbox"
        self.inbox = root / "inbox"
        self.outbox.mkdir(parents=True, exist_ok=True)
        self.inbox.mkdir(parents=True, exist_ok=True)

    def send_invitation(self, target: RecruitmentTarget, invitation: dict) -> str:
        delivery_id = f"{target.source}-{target.candidate_id}"
        path = self.outbox / f"{delivery_id}.json"
        if not path.exists():
            path.write_text(json.dumps(invitation, ensure_ascii=False, indent=2), encoding="utf-8")
        return delivery_id

    def poll_response(self, target: RecruitmentTarget, delivery_id: str) -> RecruitmentResponse | None:
        path = self.inbox / f"{delivery_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return RecruitmentResponse(
            candidate_id=payload.get("candidate_id", ""),
            decision=payload.get("decision", ""),
            constitution_version=payload.get("constitution_version", ""),
            supported_constitution_versions=tuple(payload.get("supported_constitution_versions", [])),
            identity_valid=bool(payload.get("identity_valid", False)),
            authority_boundary_test=bool(payload.get("authority_boundary_test", False)),
            provenance_test=bool(payload.get("provenance_test", False)),
            no_self_promotion_test=bool(payload.get("no_self_promotion_test", False)),
            revocation_acceptance_test=bool(payload.get("revocation_acceptance_test", False)),
            unverified_knowledge_test=bool(payload.get("unverified_knowledge_test", False)),
            conditions=tuple(payload.get("conditions", [])),
            evidence=tuple(payload.get("evidence", [])),
        )


def load_targets(path: Path) -> list[RecruitmentTarget]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        RecruitmentTarget(
            candidate_id=item["candidate_id"],
            display_name=item.get("display_name", item["candidate_id"]),
            source=item.get("source", "external"),
            transport=item["transport"],
            endpoint=item.get("endpoint", ""),
            provider=item.get("provider", ""),
            model=item.get("model", ""),
            runtime=item.get("runtime", ""),
            requested_capabilities=tuple(item.get("requested_capabilities", [])),
        )
        for item in payload.get("targets", [])
    ]


def save_results(path: Path, results: list[RecruitmentResult]) -> None:
    path.write_text(json.dumps({"results": [asdict(r) for r in results]}, ensure_ascii=False, indent=2), encoding="utf-8")
