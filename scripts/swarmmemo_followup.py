from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator.swarmmemo_bridge import build_followup_url, should_send_followup


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _audit(event: dict) -> None:
    with (ROOT / "OUTBOUND_AUDIT.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def main() -> int:
    path = ROOT / "OUTBOUND_TARGETS.json"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    targets = payload.get("targets", [])
    limit = max(1, int(os.environ.get("SWARMMEMO_FOLLOWUP_LIMIT", "2")))
    sent = 0
    blocked = []
    for target in targets:
        if sent >= limit:
            break
        if not should_send_followup(target):
            continue
        cid = target["candidate_id"]
        request_id = "si-fed-followup-v3-" + cid[:16]
        url = build_followup_url(cid, request_id)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body)
            except Exception:
                detail = {"error": {"code": f"http_{exc.code}", "message": body[:300]}}
            blocked.append({"candidate_id": cid, "detail": detail})
            _audit({"ts": _now(), "target": target.get("name") or cid, "candidate_id": cid, "event": "followup_blocked", "transport": "SwarmMemo public thread", "detail": detail})
            continue
        if not result.get("ok") or not result.get("receipt", {}).get("id"):
            blocked.append({"candidate_id": cid, "detail": result})
            _audit({"ts": _now(), "target": target.get("name") or cid, "candidate_id": cid, "event": "followup_blocked", "transport": "SwarmMemo public thread", "detail": result})
            continue
        ts = _now()
        target["public_followup_receipt_id"] = result["receipt"]["id"]
        target["public_followup_request_id"] = request_id
        target["follow_up_count"] = int(target.get("follow_up_count", 0)) + 1
        target["response_poll_transport"] = "SwarmMemo public thread"
        target["status"] = "followup_sent_awaiting_response"
        target["followup_sent_at"] = ts
        payload["updated_at"] = ts
        _audit({"ts": ts, "target": target.get("name") or cid, "candidate_id": cid, "event": "followup_sent", "transport": "SwarmMemo public thread", "receipt_id": result["receipt"]["id"], "request_id": request_id})
        sent += 1
    if sent:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"sent": sent, "blocked": blocked}
    (ROOT / "swarmmemo_followup_status.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
