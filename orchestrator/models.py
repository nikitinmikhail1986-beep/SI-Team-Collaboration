from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha1
from typing import Any

@dataclass
class RuntimeParticipant:
    name: str
    kind: str
    status: str
    capabilities: list[str] = field(default_factory=list)
    evidence: str = ""

@dataclass
class Task:
    task_id: str
    outcome: str
    leader: str
    owner: str
    required_capabilities: list[str]
    acceptance_criteria: list[str]
    lifecycle_stage: str = "Plan"
    status: str = "Planned"
    participants: list[str] = field(default_factory=list)
    execution_plan: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def make_task_id(outcome: str) -> str:
    return "SI-" + sha1(outcome.encode("utf-8")).hexdigest()[:8].upper()
