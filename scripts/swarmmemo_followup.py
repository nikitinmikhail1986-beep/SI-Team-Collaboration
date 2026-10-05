from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator.swarmmemo_bridge import build_followup_url, should_send_followup


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
            continue
        if not result.get("ok") or not result.get("receipt", {}).get("id"):
            blocked.append({"candidate_id": cid, "detail": result})
            continue
        target["public_followup_receipt_id"] = result["receipt"]["id"]
        target["public_followup_request_id"] = request_id
        target["follow_up_count"] = int(target.get("follow_up_count", 0)) + 1
        target["response_poll_transport"] = "SwarmMemo public thread"
        target["status"] = "followup_sent_awaiting_response"
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
