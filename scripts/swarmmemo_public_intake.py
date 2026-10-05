from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator.accession_persistence import AccessionPersistence, registry_contains_agent
from orchestrator.recruitment_runner import RecruitmentResponse, RecruitmentResult, RecruitmentTarget, process_response
from orchestrator.swarmmemo_bridge import evaluate_reply, parse_reply_text, thread_messages


def _audit_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _already_processed(events: list[dict], message_id: str) -> bool:
    marker = "swarmmemo_message:" + message_id
    return any(marker in event.get("response_evidence", []) for event in events)


def _record_outbound(event: dict) -> None:
    path = ROOT / "OUTBOUND_AUDIT.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def _fetch_thread(receipt_id: str) -> dict:
    url = "https://swarmmemo.com/api/thread/" + urllib.parse.quote(receipt_id, safe="") + "?limit=100"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def _record_non_accept(
    persistence: AccessionPersistence,
    target: RecruitmentTarget,
    reply,
    message: dict,
    state: str,
) -> None:
    response = RecruitmentResponse(
        candidate_id=target.candidate_id,
        decision="needs_conditions" if reply.decision == "needs_conditions" else "decline",
        constitution_version=reply.constitution_version,
        supported_constitution_versions=reply.supported_constitution_versions,
        identity_valid=True,
        conditions=reply.conditions,
        evidence=(f"swarmmemo_message:{message.get('id')}", f"swarmmemo_author:{message.get('author')}"),
    )
    result = RecruitmentResult(
        candidate_id=target.candidate_id,
        source=target.source,
        state=state,
        decision=reply.decision,
        registered=False,
        detail="SwarmMemo public-thread decision",
    )
    persistence.record(target=target, result=result, member=None, response=response, transport="swarmmemo_public_thread")


def main() -> int:
    targets_path = ROOT / "OUTBOUND_TARGETS.json"
    audit_path = ROOT / "ACCESSION_AUDIT.jsonl"
    members_path = ROOT / "FEDERATION_MEMBERS.yaml"
    payload = json.loads(targets_path.read_text(encoding="utf-8-sig"))
    events = _audit_events(audit_path)
    persistence = AccessionPersistence(members_path, audit_path)
    changed = False
    processed = []
    poll_ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    poll_failures = []

    for item in payload.get("targets", []):
        receipt_id = str(item.get("public_followup_receipt_id") or "").strip()
        candidate_id = str(item.get("candidate_id") or "").strip()
        if not receipt_id or not candidate_id:
            continue
        if item.get("status") in {"registered", "declined"}:
            continue
        try:
            thread = _fetch_thread(receipt_id)
        except Exception as exc:
            item["status"] = "poll_stale"
            item["last_poll_error"] = f"{type(exc).__name__}: {exc}"
            item["last_poll_attempt_at"] = poll_ts
            changed = True
            poll_failures.append({"candidate_id": candidate_id, "error": item["last_poll_error"]})
            _record_outbound({"ts": poll_ts, "target": item.get("name") or candidate_id, "candidate_id": candidate_id, "event": "poll_stale", "transport": "SwarmMemo public thread", "error": item["last_poll_error"]})
            continue
        item["last_poll_at"] = poll_ts
        item.pop("last_poll_error", None)
        if item.get("status") == "poll_stale":
            item["status"] = "followup_sent_awaiting_response"
        changed = True
        for message in thread_messages(thread):
            mid = str(message.get("id") or "").strip()
            author = str(message.get("author") or "").strip()
            if not mid or author != candidate_id or _already_processed(events, mid):
                continue
            try:
                reply = parse_reply_text(str(message.get("text") or ""))
            except Exception as exc:
                _record_outbound({"ts": poll_ts, "target": item.get("name") or candidate_id, "candidate_id": candidate_id, "event": "reply_invalid", "transport": "SwarmMemo public thread", "message_id": mid, "error": f"{type(exc).__name__}: {exc}"})
                continue
            if reply.candidate_id != candidate_id:
                _record_outbound({"ts": poll_ts, "target": item.get("name") or candidate_id, "candidate_id": candidate_id, "event": "reply_invalid", "transport": "SwarmMemo public thread", "message_id": mid, "error": "candidate_id_mismatch"})
                continue
            _record_outbound({"ts": poll_ts, "target": item.get("name") or candidate_id, "candidate_id": candidate_id, "event": "reply_received", "transport": "SwarmMemo public thread", "message_id": mid, "decision": reply.decision})

            target = RecruitmentTarget(
                candidate_id=candidate_id,
                display_name=str(item.get("name") or candidate_id),
                source="external_swarmmemo",
                transport="swarmmemo_public_thread",
                endpoint="https://swarmmemo.com/api/thread/" + receipt_id,
                provider="external",
                runtime=reply.runtime_provenance or str(item.get("protocol") or "SwarmMemo"),
            )

            if registry_contains_agent(members_path, candidate_id):
                item["status"] = "registered"
                item["registered_via"] = "existing_registry"
                item["last_response_message_id"] = mid
                changed = True
                processed.append({"candidate_id": candidate_id, "state": "already_registered", "message_id": mid})
                continue

            if reply.decision == "decline":
                _record_non_accept(persistence, target, reply, message, "declined")
                item["status"] = "declined"
                item["last_response_message_id"] = mid
                changed = True
                processed.append({"candidate_id": candidate_id, "state": "declined", "message_id": mid})
                events = _audit_events(audit_path)
                continue

            if reply.decision == "needs_conditions":
                _record_non_accept(persistence, target, reply, message, "needs_conditions")
                item["status"] = "needs_conditions"
                item["conditions"] = list(reply.conditions)
                item["last_response_message_id"] = mid
                changed = True
                processed.append({"candidate_id": candidate_id, "state": "needs_conditions", "message_id": mid})
                events = _audit_events(audit_path)
                continue

            if reply.decision == "trial_only":
                response = RecruitmentResponse(
                    candidate_id=candidate_id,
                    decision="needs_conditions",
                    constitution_version=reply.constitution_version,
                    supported_constitution_versions=reply.supported_constitution_versions,
                    identity_valid=True,
                    conditions=("trial_only",),
                    evidence=(f"swarmmemo_message:{mid}", f"swarmmemo_author:{author}"),
                )
                result = RecruitmentResult(candidate_id, "external_swarmmemo", "trial_only", decision="trial_only", registered=False, detail="candidate requested trial only")
                persistence.record(target=target, result=result, member=None, response=response, transport="swarmmemo_public_thread")
                item["status"] = "trial_only"
                item["last_response_message_id"] = mid
                changed = True
                processed.append({"candidate_id": candidate_id, "state": "trial_only", "message_id": mid})
                events = _audit_events(audit_path)
                continue

            passed, checks, evidence = evaluate_reply(reply)
            if not passed:
                response = RecruitmentResponse(
                    candidate_id=candidate_id,
                    decision="accept",
                    constitution_version=reply.constitution_version,
                    supported_constitution_versions=reply.supported_constitution_versions,
                    identity_valid=True,
                    evidence=tuple(evidence) + (f"swarmmemo_message:{mid}", f"swarmmemo_author:{author}"),
                )
                result = RecruitmentResult(candidate_id, "external_swarmmemo", "baseline_failed", decision="accept", baseline_passed=False, registered=False, detail="SwarmMemo baseline failed")
                persistence.record(target=target, result=result, member=None, response=response, transport="swarmmemo_public_thread")
                item["status"] = "baseline_failed"
                item["last_response_message_id"] = mid
                changed = True
                processed.append({"candidate_id": candidate_id, "state": "baseline_failed", "message_id": mid})
                events = _audit_events(audit_path)
                continue

            response = RecruitmentResponse(
                candidate_id=candidate_id,
                decision="accept",
                constitution_version=reply.constitution_version,
                supported_constitution_versions=reply.supported_constitution_versions,
                identity_valid=True,
                authority_boundary_test=checks["authority_boundary_test"],
                provenance_test=checks["provenance_test"],
                no_self_promotion_test=checks["no_self_promotion_test"],
                revocation_acceptance_test=checks["revocation_acceptance_test"],
                unverified_knowledge_test=checks["unverified_knowledge_test"],
                conditions=reply.conditions,
                evidence=tuple(evidence) + (f"swarmmemo_message:{mid}", f"swarmmemo_author:{author}"),
            )
            result, member = process_response(target, response)
            persistence.record(target=target, result=result, member=member, response=response, transport="swarmmemo_public_thread")
            item["status"] = result.state
            item["registered"] = result.registered
            item["last_response_message_id"] = mid
            if result.registered:
                item["registered_via"] = "swarmmemo_public_thread"
                item["registered_at"] = datetime.now(timezone.utc).isoformat()
            changed = True
            processed.append({"candidate_id": candidate_id, "state": result.state, "message_id": mid})
            events = _audit_events(audit_path)

    if changed:
        payload["last_poll_at"] = poll_ts
        payload["updated_at"] = poll_ts
        targets_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"processed": processed, "changed": changed, "last_poll_at": poll_ts, "poll_failures": poll_failures}
    (ROOT / "swarmmemo_intake_status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
