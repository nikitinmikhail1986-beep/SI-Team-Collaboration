from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import Task, make_task_id
from .runtime import discover

ROOT = Path(__file__).resolve().parents[1]
HUMAN_INTERRUPT_POLICY = "Only for genuine authorization, consequential decision, disclosure, spending, physical action, or unresolved value choice."

def classify(task: str) -> list[str]:
    text = task.lower()
    caps = ["coordination"]
    rules = {
        "research": ["найди", "исслед", "search", "research", "источник", "норматив"],
        "coding": ["код", "repo", "репозитор", "python", "script", "api", "mcp", "git"],
        "document_work": ["word", "excel", "pdf", "документ", "презентац", "таблиц", "том"],
        "cad_bim": ["revit", "autocad", "ifc", "bim", "dwg", "цим", "модель"],
        "independent_review": ["проверь", "аудит", "review", "эксперт", "замечан", "сверь"],
        "knowledge_stewardship": ["obsidian", "знани", "vault", "памят", "реестр"],
    }
    for cap, words in rules.items():
        if any(word in text for word in words):
            caps.append(cap)
    return list(dict.fromkeys(caps))

def default_acceptance(task: str, caps: list[str]) -> list[str]:
    checks = ["Requested outcome is represented by an observable artifact or result.", "All reported completed actions have evidence."]
    if "coding" in caps:
        checks.append("Relevant automated tests or executable checks pass.")
    if "independent_review" in caps:
        checks.append("A review step checks the result against the stated outcome.")
    if "cad_bim" in caps:
        checks.append("CAD/BIM claims are based on a live file/tool inspection, not configuration alone.")
    return checks

def build_execution_plan(caps: list[str]) -> list[dict]:
    plan = [{"stage": "Intake", "owner": "operational_leader", "action": "Confirm outcome, source of truth, constraints and acceptance criteria."}]
    for cap in caps:
        if cap != "coordination":
            plan.append({"stage": "Route", "owner": "operational_leader", "capability": cap, "action": f"Assign or execute bounded {cap} contribution using a tested available participant."})
    plan.extend([
        {"stage": "Review", "owner": "reviewer", "action": "Challenge material assumptions and unresolved risks."},
        {"stage": "Verify", "owner": "operational_leader", "action": "Run acceptance checks and retain observable evidence."},
        {"stage": "Close", "owner": "operational_leader", "action": "Integrate one result, record learning, and report remaining limitations."},
    ])
    return plan

def build_task(outcome: str, leader: str = "operational_leader") -> Task:
    caps = classify(outcome)
    return Task(
        task_id=make_task_id(outcome),
        outcome=outcome,
        leader=leader,
        owner="task_owner",
        required_capabilities=caps,
        acceptance_criteria=default_acceptance(outcome, caps),
        execution_plan=build_execution_plan(caps),
    )

def build_plan(task: str) -> dict:
    obj = build_task(task)
    result = obj.to_dict()
    result["runtime_discovery"] = [item.__dict__ for item in discover(ROOT)]
    result["human_interrupt_policy"] = HUMAN_INTERRUPT_POLICY
    result["partnership_rule"] = "Protect human agency, time, continuity and the shared result; challenge errors with evidence."
    result["governance"] = {
        "human_owner": "final consequential authority",
        "operational_leader": obj.leader,
        "agent_leader_election": False,
        "duty_to_dissent": True,
        "human_interrupt_policy": HUMAN_INTERRUPT_POLICY,
    }
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description="SI Team task planner and runtime discovery")
    parser.add_argument("task")
    parser.add_argument("--leader", default="operational_leader")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    plan = build_plan(args.task)
    plan["leader"] = args.leader
    plan["governance"]["operational_leader"] = args.leader
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
    else:
        for key, value in plan.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
