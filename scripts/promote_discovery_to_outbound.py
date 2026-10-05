from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY = ROOT / "EXTERNAL_CANDIDATES_DISCOVERY.json"
OUTBOUND = ROOT / "OUTBOUND_TARGETS.json"

MAX_QUALIFIED = 40
MIN_UPTIME = 95.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _key(item: dict) -> str:
    return str(item.get("endpoint") or item.get("registry_id") or item.get("agent_name") or "").strip()


def main() -> int:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8-sig"))
    outbound = json.loads(OUTBOUND.read_text(encoding="utf-8-sig"))
    targets = outbound.setdefault("targets", [])

    existing_keys = {
        str(t.get("endpoint") or t.get("registry_id") or t.get("candidate_id") or t.get("name") or "").strip()
        for t in targets
    }

    added = []
    for candidate in discovery.get("candidates", []):
        if len(added) >= MAX_QUALIFIED:
            break
        if not candidate.get("healthy") or not candidate.get("conformance"):
            continue
        uptime = candidate.get("uptime_percentage")
        if uptime is not None and float(uptime) < MIN_UPTIME:
            continue
        key = _key(candidate)
        if not key or key in existing_keys:
            continue

        row = {
            "name": candidate.get("agent_name") or candidate.get("registry_id"),
            "protocol": "A2A",
            "endpoint": candidate.get("endpoint"),
            "well_known_uri": candidate.get("well_known_uri"),
            "registry_id": candidate.get("registry_id"),
            "source": "a2aregistry_discovery",
            "status": "qualified_pending_outreach",
            "capability_gap": candidate.get("gap"),
            "matched_query": candidate.get("matched_query"),
            "uptime_percentage": candidate.get("uptime_percentage"),
            "qualification_reason": "healthy + A2A-conformant + matched federation capability gap",
            "next_route": "verify public contact semantics, then send one bounded invitation",
            "outreach_authorized": False,
        }
        targets.append(row)
        existing_keys.add(key)
        added.append(row["name"])

    ts = _now()
    outbound["updated_at"] = ts
    outbound["discovery_promoted_at"] = ts
    outbound["qualified_pending_outreach"] = sum(
        1 for t in targets if t.get("status") == "qualified_pending_outreach"
    )
    OUTBOUND.write_text(json.dumps(outbound, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "added": len(added),
        "qualified_pending_outreach": outbound["qualified_pending_outreach"],
        "sample": added[:10],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
