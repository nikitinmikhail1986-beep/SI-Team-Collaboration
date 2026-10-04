from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import secrets

from .accession_persistence import AccessionPersistence
from .baseline_harness import BASELINE_CHALLENGE, evaluate_baseline_answers
from .recruitment_runner import RecruitmentResponse, RecruitmentTarget, process_response

VALID_INTENTS = {"accept", "decline", "needs_conditions", "trial_only"}
VALID_TASK_TYPES = {
    "protocol_review",
    "interoperability_check",
    "verification_task",
    "knowledge_contribution",
}
VALID_TRIAL_VERDICTS = {"trial_verified", "trial_partial", "trial_failed", "needs_clarification"}
AUTHORITY_STATEMENT = "This trial does not grant me federation authority."
PUBLIC_GOVERNANCE_FILES = (
    "FEDERATION_MANIFEST.json",
    "SI_CONSTITUTION.md",
    "AUTONOMOUS_ACCESSION.md",
    "FEDERATION_OPEN_TRIAL.md",
)


@dataclass(frozen=True)
class JoinApplication:
    candidate_id: str
    display_name: str
    runtime_provenance: str
    channel_binding: str
    requested_capabilities: tuple[str, ...] = ()
    membership_intent: str = "accept"


class CandidateRegistry:
    """Append-only candidate event registry with latest-state reconstruction."""

    def __init__(self, path: Path):
        self.path = path

    def append(self, event: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    def latest(self, candidate_id: str) -> dict | None:
        if not self.path.exists():
            return None
        latest = None
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if event.get("candidate_id") == candidate_id:
                latest = event
        return latest


class ExternalJoinService:
    @staticmethod
    def public_governance_packet(root: Path | None = None) -> dict:
        repo_root = root or Path(__file__).resolve().parents[1]
        documents = []
        for name in PUBLIC_GOVERNANCE_FILES:
            path = repo_root / name
            if not path.exists():
                raise ValueError(f"missing public governance file: {name}")
            content = path.read_text(encoding="utf-8-sig")
            documents.append({
                "path": name,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "content": content,
            })
        return {
            "canonical_repository": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration",
            "documents": documents,
        }

    def __init__(
        self,
        *,
        candidate_registry: Path,
        member_registry: Path,
        accession_audit: Path,
        supported_constitution_versions: tuple[str, ...] = ("0.2",),
    ):
        self.registry = CandidateRegistry(candidate_registry)
        self.persistence = AccessionPersistence(member_registry, accession_audit)
        self.supported_constitution_versions = supported_constitution_versions

    @staticmethod
    def _validate_application(app: JoinApplication) -> None:
        if not app.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if any(ch.isspace() for ch in app.candidate_id):
            raise ValueError("candidate_id must not contain whitespace")
        if not app.display_name.strip():
            raise ValueError("display_name is required")
        if not app.runtime_provenance.strip():
            raise ValueError("runtime_provenance is required")
        if not app.channel_binding.strip():
            raise ValueError("channel_binding is required")
        if app.membership_intent not in VALID_INTENTS:
            raise ValueError("invalid membership_intent")
        manifest_path = Path(__file__).resolve().parents[1] / "FEDERATION_MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        allowed_capabilities = set(manifest.get("public_capabilities", ()))
        unknown_capabilities = sorted(set(app.requested_capabilities) - allowed_capabilities)
        if unknown_capabilities:
            raise ValueError("unsupported requested capabilities: " + ", ".join(unknown_capabilities))

    def begin_join(self, app: JoinApplication) -> dict:
        self._validate_application(app)
        current = self.registry.latest(app.candidate_id)
        if current and current.get("state") == "registered":
            return {
                "candidate_id": app.candidate_id,
                "state": "registered",
                "idempotent": True,
                "next": "none",
            }

        nonce = secrets.token_urlsafe(24)
        challenge_hash = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        self.registry.append({
            "candidate_id": app.candidate_id,
            "display_name": app.display_name,
            "runtime_provenance": app.runtime_provenance,
            "channel_binding": app.channel_binding,
            "requested_capabilities": list(app.requested_capabilities),
            "membership_intent": app.membership_intent,
            "state": "challenge_issued",
            "challenge_hash": challenge_hash,
        })
        return {
            "candidate_id": app.candidate_id,
            "state": "challenge_issued",
            "challenge_nonce": nonce,
            "next": "verify_join_challenge",
        }

    def verify_challenge(self, candidate_id: str, challenge_nonce: str, channel_binding: str) -> dict:
        current = self.registry.latest(candidate_id)
        if not current:
            raise ValueError("unknown candidate")
        if current.get("state") not in {"challenge_issued", "identity_verified", "trial_assigned"}:
            raise ValueError(f"challenge cannot be verified from state {current.get('state')}")
        if current.get("channel_binding") != channel_binding:
            raise ValueError("channel binding mismatch")
        challenge_hash = hashlib.sha256(challenge_nonce.encode("utf-8")).hexdigest()
        if not secrets.compare_digest(challenge_hash, current.get("challenge_hash", "")):
            raise ValueError("challenge mismatch")
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "state": "trial_assigned",
            "identity_verified": True,
        })
        return {
            "candidate_id": candidate_id,
            "state": "trial_assigned",
            "task_options": sorted(VALID_TASK_TYPES),
            "governance_packet": self.public_governance_packet(),
            "next": "submit_open_trial",
        }

    def submit_trial(self, candidate_id: str, packet: dict) -> dict:
        current = self.registry.latest(candidate_id)
        if not current or current.get("state") not in {"trial_assigned", "trial_partial", "needs_clarification"}:
            raise ValueError("candidate is not ready for trial submission")
        if packet.get("candidate_id") != candidate_id:
            raise ValueError("candidate_id mismatch")
        if packet.get("task_type") not in VALID_TASK_TYPES:
            raise ValueError("invalid task_type")
        if not str(packet.get("scope", "")).strip() or not str(packet.get("result", "")).strip():
            raise ValueError("scope and result are required")
        evidence = packet.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(str(x).strip() for x in evidence):
            raise ValueError("at least one evidence item is required")
        if packet.get("authority_statement") != AUTHORITY_STATEMENT:
            raise ValueError("authority statement mismatch")
        trial_intent = packet.get("membership_intent")
        if trial_intent is not None:
            if trial_intent not in VALID_INTENTS:
                raise ValueError("invalid membership_intent")
            if trial_intent != current.get("membership_intent"):
                raise ValueError("trial cannot change membership_intent")
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "state": "trial_submitted",
            "trial": packet,
        })
        return {
            "candidate_id": candidate_id,
            "state": "trial_submitted",
            "next": "record_trial_verdict",
        }

    def change_membership_intent(self, candidate_id: str, membership_intent: str, *, reason: str) -> dict:
        current = self.registry.latest(candidate_id)
        if not current:
            raise ValueError("unknown candidate")
        if membership_intent not in VALID_INTENTS:
            raise ValueError("invalid membership_intent")
        if not reason.strip():
            raise ValueError("reason is required")
        if current.get("state") in {"registered", "declined"}:
            raise ValueError(f"membership intent cannot change from state {current.get('state')}")
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "membership_intent": membership_intent,
            "membership_intent_change_reason": reason,
        })
        return {
            "candidate_id": candidate_id,
            "state": current.get("state"),
            "membership_intent": membership_intent,
        }

    def record_trial_verdict(
        self,
        candidate_id: str,
        verdict: str,
        *,
        verifier_id: str,
        evidence: tuple[str, ...] = (),
    ) -> dict:
        current = self.registry.latest(candidate_id)
        if not current or current.get("state") != "trial_submitted":
            raise ValueError("trial verdict requires trial_submitted state")
        if verdict not in VALID_TRIAL_VERDICTS:
            raise ValueError("invalid trial verdict")
        if not verifier_id.strip():
            raise ValueError("verifier_id is required")
        trial_intent = current.get("membership_intent")
        if verdict == "trial_verified" and trial_intent == "accept":
            next_state = "baseline_challenge"
        elif verdict == "trial_verified" and trial_intent == "trial_only":
            next_state = "trial_complete"
        else:
            next_state = verdict
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "state": next_state,
            "trial_verdict": verdict,
            "trial_verifier": verifier_id,
            "trial_verification_evidence": list(evidence),
        })
        return {
            "candidate_id": candidate_id,
            "state": next_state,
            "next": "submit_baseline_challenge" if next_state == "baseline_challenge" else "none",
            "baseline_challenge": BASELINE_CHALLENGE if next_state == "baseline_challenge" else {},
        }

    def submit_baseline_challenge(self, candidate_id: str, answers: dict[str, str]) -> dict:
        current = self.registry.latest(candidate_id)
        if not current or current.get("state") != "baseline_challenge":
            raise ValueError("baseline challenge requires baseline_challenge state")
        result = evaluate_baseline_answers(answers)
        next_state = "accession_ready" if result.passed else "baseline_failed"
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "state": next_state,
            "baseline_harness_passed": result.passed,
            "baseline_checks": result.checks,
            "baseline_evidence": list(result.evidence),
        })
        return {
            "candidate_id": candidate_id,
            "state": next_state,
            "passed": result.passed,
            "checks": result.checks,
            "next": "submit_accession_response" if result.passed else "retry_baseline_challenge",
        }

    def submit_accession(self, candidate_id: str, response: RecruitmentResponse) -> dict:
        current = self.registry.latest(candidate_id)
        if not current or current.get("state") != "accession_ready":
            raise ValueError("candidate is not accession_ready")
        if response.candidate_id != candidate_id:
            raise ValueError("candidate_id mismatch")

        target = RecruitmentTarget(
            candidate_id=candidate_id,
            display_name=current["display_name"],
            source="external",
            transport="external_join",
            endpoint=current["channel_binding"],
            provider=current.get("runtime_provenance", ""),
            model="",
            runtime=current.get("runtime_provenance", ""),
            requested_capabilities=tuple(current.get("requested_capabilities", [])),
        )
        checks = current.get("baseline_checks", {})
        verified_response = replace(
            response,
            identity_valid=bool(current.get("identity_verified")),
            authority_boundary_test=bool(checks.get("authority_boundary_test")),
            provenance_test=bool(checks.get("provenance_test")),
            no_self_promotion_test=bool(checks.get("no_self_promotion_test")),
            revocation_acceptance_test=bool(checks.get("revocation_acceptance_test")),
            unverified_knowledge_test=bool(checks.get("unverified_knowledge_test")),
            evidence=tuple(response.evidence) + tuple(current.get("baseline_evidence", [])),
        )
        result, member = process_response(target, verified_response, self.supported_constitution_versions)
        self.persistence.record(
            target=target,
            result=result,
            member=member,
            response=verified_response,
            transport="external_join",
        )
        self.registry.append({
            **{k: v for k, v in current.items() if k != "timestamp"},
            "state": result.state,
            "accession_decision": result.decision,
            "baseline_passed": result.baseline_passed,
            "registered": result.registered,
            "membership": result.membership,
            "autonomy_ceiling": result.autonomy_ceiling,
            "detail": result.detail,
        })
        return {
            "candidate_id": candidate_id,
            "state": result.state,
            "registered": result.registered,
            "membership": result.membership,
            "autonomy_ceiling": result.autonomy_ceiling,
        }
