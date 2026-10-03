from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_registry(name: str) -> str:
    path = ROOT / name
    return path.read_text(encoding="utf-8")

def classify(task: str) -> list[str]:
    text = task.lower()
    caps = ["coordination"]
    rules = {
        "research": ["найди", "исслед", "search", "research", "источник", "норматив"],
        "coding": ["код", "repo", "репозитор", "python", "script", "api", "mcp", "git"],
        "document_work": ["word", "excel", "pdf", "документ", "презентац", "таблиц"],
        "cad_bim": ["revit", "autocad", "ifc", "bim", "dwg", "цим"],
        "independent_review": ["проверь", "аудит", "review", "эксперт", "замечан"],
        "knowledge_stewardship": ["obsidian", "знани", "vault", "памят", "реестр"],
    }
    for cap, words in rules.items():
        if any(word in text for word in words):
            caps.append(cap)
    return list(dict.fromkeys(caps))

def build_plan(task: str) -> dict:
    caps = classify(task)
    return {
        "task": task,
        "lifecycle": ["Intake", "Plan", "Route", "Execute", "Review", "Verify", "Learn", "Close"],
        "required_capabilities": caps,
        "owner": "task_owner",
        "human_interrupt_policy": "Only for genuine authorization, consequential decision, disclosure, spending, physical action, or unresolved value choice.",
        "partnership_rule": "Protect human agency, time, continuity and the shared result; challenge errors with evidence.",
        "status": "Planned",
        "acceptance_prompt": "Define an observable acceptance check before execution.",
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="SI Team deterministic routing planner")
    parser.add_argument("task")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    plan = build_plan(args.task)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        for key, value in plan.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
