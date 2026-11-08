from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


class InternalAgentError(RuntimeError):
    pass


REGISTRY_PATH = Path(__file__).with_name("internal_project_profiles.json")
ONLINE_TTL_SECONDS = 75.0
MAX_POLL_WAIT_SECONDS = 25.0
MAX_OUTPUT_CHARS = 8_000
MAX_ACTIVE_JOBS = 8
PROFILE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class InternalProfile:
    agent_id: str
    role: str
    capabilities: tuple[str, ...]


@dataclass
class TaskJob:
    task_id: str
    context_id: str
    outcome: str
    capability: str
    first: InternalProfile
    second: InternalProfile
    reviewer: InternalProfile
    done: threading.Event = field(default_factory=threading.Event)
    phase: str = ""
    assigned_agent: str = ""
    outputs: dict[str, str] = field(default_factory=dict)
    review_status: str = ""
    failure: tuple[str, str] | None = None
    canceled: bool = False


_condition = threading.Condition()
_profiles_by_id: dict[str, InternalProfile] = {}
_jobs: dict[str, TaskJob] = {}
_work: deque[dict] = deque()
_last_seen: dict[str, float] = {}


def load_internal_profiles(path: Path = REGISTRY_PATH) -> list[InternalProfile]:
    try:
        source = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InternalAgentError("internal project profile registry cannot be read") from exc
    entries = source.get("profiles") if isinstance(source, dict) else None
    if not isinstance(entries, list) or len(entries) != 25:
        raise InternalAgentError("internal project profile registry must contain exactly 25 profiles")
    profiles: list[InternalProfile] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise InternalAgentError("internal project profile entry must be an object")
        agent_id, role, capabilities = entry.get("agent_id"), entry.get("role"), entry.get("capabilities")
        if (not isinstance(agent_id, str) or not PROFILE_ID_PATTERN.fullmatch(agent_id)
                or agent_id in seen):
            raise InternalAgentError("internal project profile IDs must be non-empty and unique")
        if role not in {"executor", "reviewer"}:
            raise InternalAgentError(f"unsupported internal profile role for {agent_id}")
        if not isinstance(capabilities, list) or not all(isinstance(value, str) and value for value in capabilities):
            raise InternalAgentError(f"invalid internal profile capabilities for {agent_id}")
        profiles.append(InternalProfile(agent_id, role, tuple(capabilities)))
        seen.add(agent_id)
    if sum(profile.role == "executor" for profile in profiles) < 2:
        raise InternalAgentError("internal profile registry needs at least two executors")
    if not any(profile.role == "reviewer" and "independent_review" in profile.capabilities for profile in profiles):
        raise InternalAgentError("internal profile registry needs an independent reviewer")
    return profiles


def _profiles() -> dict[str, InternalProfile]:
    global _profiles_by_id
    if not _profiles_by_id:
        _profiles_by_id = {profile.agent_id: profile for profile in load_internal_profiles()}
    return _profiles_by_id


def worker_status() -> dict:
    profiles = _profiles()
    now = time.monotonic()
    with _condition:
        online = sorted(agent_id for agent_id, last_seen in _last_seen.items()
                        if agent_id in profiles and now - last_seen <= ONLINE_TTL_SECONDS)
        return {
            "state": "ready" if len(online) == len(profiles) else "partial",
            "online_count": len(online),
            "profile_count": len(profiles),
            "online_agent_ids": online,
            "offline_agent_ids": sorted(set(profiles) - set(online)),
        }


def worker_poll(params: dict) -> dict:
    agent_id = params.get("agent_id")
    if not isinstance(agent_id, str) or agent_id not in _profiles():
        raise InternalAgentError("worker profile is not registered")
    wait_seconds = params.get("wait_seconds", MAX_POLL_WAIT_SECONDS)
    if not isinstance(wait_seconds, (int, float)) or isinstance(wait_seconds, bool):
        raise InternalAgentError("wait_seconds must be numeric")
    wait_seconds = max(0.0, min(float(wait_seconds), MAX_POLL_WAIT_SECONDS))
    deadline = time.monotonic() + wait_seconds
    with _condition:
        _last_seen[agent_id] = time.monotonic()
        while True:
            for item in tuple(_work):
                if item["agent_id"] == agent_id:
                    _work.remove(item)
                    job = _jobs.get(item["task_id"])
                    if job is None or job.canceled:
                        continue
                    return {"state": "assigned", **item}
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"state": "idle", "agent_id": agent_id}
            _condition.wait(remaining)


def _queue_phase(job: TaskJob, phase: str, profile: InternalProfile, prompt: str) -> None:
    job.phase = phase
    job.assigned_agent = profile.agent_id
    _work.append({
        "task_id": job.task_id,
        "context_id": job.context_id,
        "phase": phase,
        "agent_id": profile.agent_id,
        "prompt": prompt,
    })
    _condition.notify_all()


def worker_complete(params: dict) -> dict:
    task_id, agent_id, phase = params.get("task_id"), params.get("agent_id"), params.get("phase")
    output, review_status = params.get("output"), params.get("review_status")
    if not all(isinstance(value, str) and value for value in (task_id, agent_id, phase)):
        raise InternalAgentError("task_id, agent_id and phase are required")
    if not isinstance(output, str) or not output.strip() or len(output) > MAX_OUTPUT_CHARS:
        raise InternalAgentError("output must be non-empty and at most 20000 characters")

    with _condition:
        job = _jobs.get(task_id)
        if job is None or job.canceled:
            raise InternalAgentError("task is missing or no longer active")
        if job.phase != phase or job.assigned_agent != agent_id:
            raise InternalAgentError("worker result does not match the current assignment")
        if phase not in {"executor-1", "executor-2", "reviewer"}:
            raise InternalAgentError("unknown task phase")
        if phase == "reviewer" and review_status not in {"approved", "needs_revision", "rejected"}:
            raise InternalAgentError("reviewer must return approved, needs_revision, or rejected")
        job.outputs[phase] = output.strip()
        if phase == "executor-1":
            prompt = (
                f"Task: {job.outcome}\n\n"
                f"Peer result from {job.first.agent_id}:\n{job.outputs[phase]}\n\n"
                "Review the peer result, then provide your own concise contribution. Preserve disagreements and state any uncertainty."
            )
            _queue_phase(job, "executor-2", job.second, prompt)
            return {"accepted": True, "next_phase": "executor-2", "next_agent_id": job.second.agent_id}
        if phase == "executor-2":
            prompt = (
                f"Task: {job.outcome}\n\n"
                f"Executor {job.first.agent_id}:\n{job.outputs['executor-1']}\n\n"
                f"Executor {job.second.agent_id}:\n{job.outputs[phase]}\n\n"
                "Independently review both outputs. State evidence, disagreements, and limitations. Return a structured review_status of approved, needs_revision, or rejected."
            )
            _queue_phase(job, "reviewer", job.reviewer, prompt)
            return {"accepted": True, "next_phase": "reviewer", "next_agent_id": job.reviewer.agent_id}
        job.review_status = review_status
        job.done.set()
        _condition.notify_all()
        return {"accepted": True, "next_phase": None, "next_agent_id": None}


def worker_fail(params: dict) -> dict:
    task_id, agent_id, phase = params.get("task_id"), params.get("agent_id"), params.get("phase")
    reason = params.get("reason", "worker failed")
    if not all(isinstance(value, str) and value for value in (task_id, agent_id, phase)):
        raise InternalAgentError("task_id, agent_id and phase are required")
    if not isinstance(reason, str):
        raise InternalAgentError("failure reason must be text")
    reason = re.sub(r"[^A-Za-z0-9_.:-]", "_", reason)[:80] or "worker_failed"
    with _condition:
        job = _jobs.get(task_id)
        if job is None or job.canceled:
            raise InternalAgentError("task is missing or no longer active")
        if job.phase != phase or job.assigned_agent != agent_id:
            raise InternalAgentError("worker failure does not match the current assignment")
        job.failure = (phase, reason[:160])
        job.done.set()
        _condition.notify_all()
    return {"accepted": True}


def execute_internal_task(params: dict, timeout: float = 180.0) -> dict:
    if not isinstance(params, dict):
        raise InternalAgentError("task parameters must be an object")
    outcome = params.get("outcome")
    capability = params.get("capability")
    if not isinstance(outcome, str) or not outcome.strip() or len(outcome) > 12_000:
        raise InternalAgentError("outcome must be non-empty and at most 12000 characters")
    if not isinstance(capability, str) or not capability:
        raise InternalAgentError("capability is required")

    profiles = _profiles()
    executors = [p for p in profiles.values() if p.role == "executor" and capability in p.capabilities]
    reviewers = [p for p in profiles.values() if p.role == "reviewer" and "independent_review" in p.capabilities]
    requested_executors = params.get("executor_ids")
    if requested_executors is not None:
        if (not isinstance(requested_executors, list) or len(requested_executors) != 2
                or not all(isinstance(item, str) for item in requested_executors)):
            raise InternalAgentError("executor_ids must contain exactly two profile IDs")
        selected = [profiles.get(item) for item in requested_executors]
        if any(item is None or item.role != "executor" or capability not in item.capabilities for item in selected):
            raise InternalAgentError("requested internal executors do not match the task capability")
        executors = selected  # type: ignore[assignment]
    if len(executors) < 2 or not reviewers:
        raise InternalAgentError("two capable internal executors and an independent reviewer are required")
    reviewer_id = params.get("reviewer_id")
    reviewer = profiles.get(reviewer_id) if reviewer_id is not None else reviewers[0]
    selected = executors[:2]
    if reviewer is None or reviewer.role != "reviewer" or "independent_review" not in reviewer.capabilities:
        raise InternalAgentError("reviewer_id is not an independent reviewer")
    if len({selected[0].agent_id, selected[1].agent_id, reviewer.agent_id}) != 3:
        raise InternalAgentError("executors and reviewer must be distinct profiles")

    status = worker_status()
    online_ids = set(status["online_agent_ids"])
    missing = sorted({selected[0].agent_id, selected[1].agent_id, reviewer.agent_id} - online_ids)
    if missing:
        raise InternalAgentError("required internal profiles are offline: " + ", ".join(missing))

    task_id = str(params.get("task_id") or uuid.uuid4())
    context_id = str(params.get("context_id") or uuid.uuid4())
    if (len(task_id) > 200 or len(context_id) > 200
            or not re.fullmatch(r"[A-Za-z0-9._:-]+", task_id)
            or not re.fullmatch(r"[A-Za-z0-9._:-]+", context_id)):
        raise InternalAgentError("task_id and context_id must be short printable identifiers")
    job = TaskJob(task_id, context_id, outcome.strip(), capability, selected[0], selected[1], reviewer)
    with _condition:
        if task_id in _jobs:
            raise InternalAgentError("task_id is already active")
        if len(_jobs) >= MAX_ACTIVE_JOBS:
            raise InternalAgentError("internal task capacity is full")
        _jobs[task_id] = job
        _queue_phase(job, "executor-1", job.first, job.outcome)

    if not job.done.wait(timeout):
        with _condition:
            job.canceled = True
            _work_copy = [item for item in _work if item["task_id"] != task_id]
            _work.clear()
            _work.extend(_work_copy)
            _jobs.pop(task_id, None)
            _condition.notify_all()
        raise InternalAgentError("timed out waiting for all three internal agent results")
    if job.failure is not None:
        phase, reason = job.failure
        with _condition:
            _jobs.pop(task_id, None)
        raise InternalAgentError(f"internal worker failed in {phase}: {reason}")

    state = "completed" if job.review_status == "approved" else job.review_status
    try:
        return {
            "task_id": task_id,
            "context_id": context_id,
            "state": state,
            "executors": [
                {"agent_id": job.first.agent_id, "output": job.outputs["executor-1"]},
                {"agent_id": job.second.agent_id, "output": job.outputs["executor-2"]},
            ],
            "reviewer": {
                "agent_id": reviewer.agent_id,
                "output": job.outputs["reviewer"],
                "review_status": job.review_status,
            },
            "review_status": job.review_status,
            "report": (
                f"Task {task_id}: {state}. Executor 1 {job.first.agent_id} submitted a result; "
                f"executor 2 {job.second.agent_id} received and reviewed it, then submitted its result. "
                f"Independent reviewer {reviewer.agent_id} reviewed both results and returned {job.review_status}: "
                f"{job.outputs['reviewer']}"
            ),
            "provenance": {
                "transport": "SI Federation A2A gateway with authenticated local worker polling",
                "agent_count": 3,
                "registered_profile_count": status["profile_count"],
                "online_profile_count": status["online_count"],
                "handoffs": {
                    "executor_1_result_sent_to_executor_2": "executor-1" in job.outputs and "executor-2" in job.outputs,
                    "both_executor_results_sent_to_reviewer": all(key in job.outputs for key in ("executor-1", "executor-2", "reviewer")),
                },
            },
        }
    finally:
        with _condition:
            _jobs.pop(task_id, None)


def reset_state_for_tests() -> None:
    with _condition:
        _jobs.clear()
        _work.clear()
        _last_seen.clear()
        _condition.notify_all()
