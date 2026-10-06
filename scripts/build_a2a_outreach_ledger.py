from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _norm(value: object) -> str:
    return str(value or "").strip().lower().rstrip("/")


def _aliases(row: dict) -> set[str]:
    return {x for x in (
        _norm(row.get("name")),
        _norm(row.get("endpoint")),
        _norm(row.get("manifest")),
        _norm(row.get("registry_id")),
    ) if x}


def build(paths: list[Path]) -> dict:
    agents: list[dict] = []
    key_to_index: dict[str, int] = {}
    attempts = 0
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = payload.get("results", payload if isinstance(payload, list) else [])
        for row in rows:
            if not isinstance(row, dict):
                continue
            attempts += 1
            name = _norm(row.get("name"))
            endpoint = _norm(row.get("endpoint"))
            key = name or endpoint or _norm(row.get("manifest"))
            if not key:
                continue
            idx = key_to_index.get(key)
            if idx is None:
                idx = len(agents)
                key_to_index[key] = idx
                agents.append({
                    "name": row.get("name"),
                    "endpoint": row.get("endpoint"),
                    "manifest": row.get("manifest"),
                    "attempt_count": 0,
                    "statuses": [],
                    "http_codes": [],
                    "delivery_confirmed": False,
                    "protocol_error": False,
                    "sources": [],
                })
            agent = agents[idx]
            agent["attempt_count"] += 1
            status = str(row.get("status") or "unknown")
            if status not in agent["statuses"]:
                agent["statuses"].append(status)
            http = row.get("http")
            if http is not None and http not in agent["http_codes"]:
                agent["http_codes"].append(http)
            agent["delivery_confirmed"] = bool(agent["delivery_confirmed"] or status in {"delivered_result", "delivered_http"})
            agent["protocol_error"] = bool(agent["protocol_error"] or status == "protocol_error")
            if path.name not in agent["sources"]:
                agent["sources"].append(path.name)
            if not agent.get("endpoint") and row.get("endpoint"):
                agent["endpoint"] = row.get("endpoint")
            if not agent.get("manifest") and row.get("manifest"):
                agent["manifest"] = row.get("manifest")
            if not agent.get("name") and row.get("name"):
                agent["name"] = row.get("name")

    agents.sort(key=lambda x: (_norm(x.get("name")), _norm(x.get("endpoint"))))
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_kind": "normalized_local_a2a_outreach_results",
        "attempts": attempts,
        "unique_agents": len(agents),
        "delivery_confirmed_unique": sum(1 for a in agents if a["delivery_confirmed"]),
        "protocol_error_unique": sum(1 for a in agents if a["protocol_error"]),
        "agents": agents,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "A2A_OUTREACH_LEDGER.json")
    args = parser.parse_args()
    ledger = build(args.sources)
    args.output.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: ledger[k] for k in ("attempts", "unique_agents", "delivery_confirmed_unique", "protocol_error_unique")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
