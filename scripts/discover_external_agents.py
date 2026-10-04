from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "https://a2aregistry.org/api/agents"
QUERIES = {
    "independent_review": ("review", "verification", "evidence", "audit"),
    "research": ("research", "standards", "knowledge"),
    "legal": ("legal", "compliance", "policy"),
    "finance": ("finance", "commercial", "economic"),
    "procurement": ("procurement", "tender", "supplier", "rfq"),
    "architecture_construction": ("architecture", "construction", "bim"),
    "interoperability": ("a2a", "mcp", "agent", "handoff"),
}


def fetch(query: str, limit: int = 10) -> list[dict]:
    params = urllib.parse.urlencode({
        "conformance": "standard",
        "search": query,
        "limit": limit,
    })
    req = urllib.request.Request(
        f"{REGISTRY}?{params}",
        headers={"User-Agent": "SI-Federation-Discovery/0.1"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        payload = json.load(response)
    return payload.get("agents", [])


def compact(agent: dict, gap: str, query: str) -> dict:
    skills = [str(s.get("id", "")) for s in agent.get("skills", []) if s.get("id")]
    return {
        "agent_name": agent.get("name"),
        "author": agent.get("author"),
        "gap": gap,
        "matched_query": query,
        "well_known_uri": agent.get("wellKnownURI"),
        "endpoint": agent.get("url"),
        "healthy": bool(agent.get("is_healthy")),
        "conformance": bool(agent.get("conformance")),
        "uptime_percentage": agent.get("uptime_percentage"),
        "skills": skills[:40],
        "registry_id": agent.get("id"),
        "status": "discovered",
        "authority": "none",
    }


def main() -> None:
    seen: set[str] = set()
    rows: list[dict] = []
    for gap, queries in QUERIES.items():
        for query in queries:
            for agent in fetch(query):
                endpoint = str(agent.get("url") or "")
                key = endpoint or str(agent.get("id") or "")
                if not key or key in seen:
                    continue
                if not agent.get("is_healthy") or not agent.get("conformance"):
                    continue
                seen.add(key)
                rows.append(compact(agent, gap, query))

    rows.sort(
        key=lambda row: (
            row.get("uptime_percentage") is not None,
            row.get("uptime_percentage") or 0,
            len(row.get("skills") or []),
        ),
        reverse=True,
    )
    output = {
        "schema_version": "0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": REGISTRY,
        "selection_rule": "public A2A-conformant healthy agents matched to federation capability gaps",
        "membership_effect": "none",
        "candidates": rows[:50],
    }
    out = ROOT / "EXTERNAL_CANDIDATES_DISCOVERY.json"
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "discovered": len(rows),
        "written": min(50, len(rows)),
        "output": str(out),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
