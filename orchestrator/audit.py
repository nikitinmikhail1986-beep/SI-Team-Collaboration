from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path


@dataclass(frozen=True)
class AuditEvent:
    timestamp: str
    actor: str
    action: str
    decision: str
    evidence: str
    previous_hash: str
    event_hash: str


def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(canonical.encode("utf-8")).hexdigest()


def append_event(path: Path, actor: str, action: str, decision: str, evidence: str = "") -> AuditEvent:
    """Append a tamper-evident event to a JSONL audit chain."""
    previous_hash = ""
    if path.exists() and path.stat().st_size:
        last = path.read_text(encoding="utf-8").splitlines()[-1]
        previous_hash = json.loads(last)["event_hash"]

    base = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "decision": decision,
        "evidence": evidence,
        "previous_hash": previous_hash,
    }
    event_hash = _hash_payload(base)
    event = AuditEvent(**base, event_hash=event_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
    return event


def verify_chain(path: Path) -> bool:
    if not path.exists():
        return True
    previous_hash = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(line)
        event_hash = item.pop("event_hash")
        if item.get("previous_hash", "") != previous_hash:
            return False
        if _hash_payload(item) != event_hash:
            return False
        previous_hash = event_hash
    return True
