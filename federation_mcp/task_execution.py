from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class TaskExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    role: str
    capabilities: tuple[str, ...]
    endpoint: str
    token_env: str | None = None


def load_profiles(raw: str | None = None) -> list[AgentProfile]:
    """Load operator-configured A2A endpoints; never infer availability from local roles."""
    source = raw if raw is not None else os.environ.get("SI_AGENT_PROFILES_JSON", "")
    if not source:
        raise TaskExecutionError("agent profiles are not configured")
    try:
        values = json.loads(source)
    except json.JSONDecodeError as exc:
        raise TaskExecutionError("agent profile configuration is invalid JSON") from exc
    if not isinstance(values, list):
        raise TaskExecutionError("agent profile configuration must be a list")

    profiles: list[AgentProfile] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, dict):
            raise TaskExecutionError("agent profile entry must be an object")
        agent_id = value.get("agent_id")
        role = value.get("role")
        capabilities = value.get("capabilities")
        endpoint = value.get("endpoint")
        token_env = value.get("token_env")
        if not isinstance(agent_id, str) or not agent_id or agent_id in seen:
            raise TaskExecutionError("agent IDs must be non-empty and unique")
        if role not in {"executor", "reviewer"}:
            raise TaskExecutionError(f"unsupported role for {agent_id}")
        if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
            raise TaskExecutionError(f"invalid capabilities for {agent_id}")
        parsed = urlparse(endpoint if isinstance(endpoint, str) else "")
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise TaskExecutionError(f"agent endpoint for {agent_id} must be an HTTPS URL")
        if token_env is not None and (not isinstance(token_env, str) or not token_env.isidentifier()):
            raise TaskExecutionError(f"invalid token environment key for {agent_id}")
        profiles.append(AgentProfile(agent_id, role, tuple(capabilities), endpoint, token_env))
        seen.add(agent_id)
    return profiles


def _message_parts(message: object) -> list[dict]:
    if not isinstance(message, dict):
        return []
    parts = message.get("parts", [])
    return [part for part in parts if isinstance(part, dict)] if isinstance(parts, list) else []


def _normalize_result(profile: AgentProfile, result: object) -> dict:
    """Normalize either A2A Message or completed Task into useful output."""
    if not isinstance(result, dict):
        raise TaskExecutionError(f"agent {profile.agent_id} returned an invalid A2A result")

    upstream_task_id = None
    if result.get("kind") == "task" or "status" in result:
        status = result.get("status")
        state = status.get("state") if isinstance(status, dict) else None
        if state != "completed":
            raise TaskExecutionError(f"agent {profile.agent_id} task did not complete")
        upstream_task_id = result.get("id")
        parts: list[dict] = []
        artifacts = result.get("artifacts", [])
        if isinstance(artifacts, list):
            for artifact in artifacts:
                parts.extend(_message_parts(artifact))
        history = result.get("history", [])
        if isinstance(history, list):
            parts.extend(part for message in history for part in _message_parts(message))
        if not parts:
            parts.extend(_message_parts(status.get("message") if isinstance(status, dict) else None))
    else:
        if result.get("kind") not in (None, "message") or result.get("role") != "agent":
            raise TaskExecutionError(f"agent {profile.agent_id} returned an invalid A2A message")
        parts = _message_parts(result)

    data_values = [part["data"] for part in parts if part.get("kind") == "data" and isinstance(part.get("data"), dict)]
    texts = [part["text"] for part in parts if part.get("kind") == "text" and isinstance(part.get("text"), str) and part["text"].strip()]
    structured_output = next((item.get("output") for item in data_values if isinstance(item.get("output"), str) and item["output"].strip()), None)
    output = structured_output or "\n".join(texts)
    if not isinstance(output, str) or not output.strip():
        raise TaskExecutionError(f"agent {profile.agent_id} returned no usable output")
    review_status = next((item.get("review_status") for item in data_values if item.get("review_status") is not None), None)
    return {"output": output, "review_status": review_status, "upstream_task_id": upstream_task_id}


def _call_agent(profile: AgentProfile, task_id: str, context_id: str, prompt: str, timeout: float) -> dict:
    token = os.environ.get(profile.token_env, "") if profile.token_env else ""
    if profile.token_env and not token:
        raise TaskExecutionError(f"agent credential is not configured for {profile.agent_id}")
    message = {
        "messageId": str(uuid.uuid4()),
        "contextId": context_id,
        "role": "user",
        "parts": [{"kind": "text", "text": prompt}],
        "metadata": {"task_id": task_id, "assigned_agent_id": profile.agent_id},
    }
    request_id = str(uuid.uuid4())
    request = Request(
        profile.endpoint,
        data=json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {"message": message},
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(1_000_001).decode("utf-8"))
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise TaskExecutionError(f"agent {profile.agent_id} transport failed: {type(exc).__name__}") from exc
    if (not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0"
            or payload.get("id") != request_id or "result" not in payload or "error" in payload):
        raise TaskExecutionError(f"agent {profile.agent_id} returned an invalid A2A response")
    return _normalize_result(profile, payload["result"])


def execute_task(params: dict, profiles: list[AgentProfile] | None = None, timeout: float = 30.0) -> dict:
    """Run two real A2A executors in sequence, pass the first result to the second, then review."""
    outcome = params.get("outcome")
    capability = params.get("capability")
    if not isinstance(outcome, str) or not outcome.strip() or len(outcome) > 12_000:
        raise TaskExecutionError("outcome must be non-empty and at most 12000 characters")
    if not isinstance(capability, str) or not capability:
        raise TaskExecutionError("capability is required")
    configured = profiles if profiles is not None else load_profiles()
    executors = [p for p in configured if p.role == "executor" and capability in p.capabilities]
    reviewers = [p for p in configured if p.role == "reviewer" and "independent_review" in p.capabilities]
    if len(executors) < 2 or not reviewers:
        raise TaskExecutionError("two capable executors and an independent reviewer are required")
    selected = executors[:2]
    reviewer = next((p for p in reviewers if p.agent_id not in {x.agent_id for x in selected}), None)
    if reviewer is None:
        raise TaskExecutionError("reviewer must be distinct from both executors")
    if len({selected[0].endpoint, selected[1].endpoint, reviewer.endpoint}) != 3:
        raise TaskExecutionError("executors and reviewer must use distinct A2A endpoints")

    task_id = str(params.get("task_id") or uuid.uuid4())
    context_id = str(params.get("context_id") or uuid.uuid4())
    first = _call_agent(selected[0], task_id, context_id, outcome, timeout)
    second_prompt = (
        f"Task: {outcome}\n\n"
        f"Peer result from {selected[0].agent_id} (review it and add an independent contribution):\n{first['output']}"
    )
    second = _call_agent(selected[1], task_id, context_id, second_prompt, timeout)
    review_prompt = (
        f"Independently review the task and both executor results. Return findings, disagreements, and an explicit review_status of approved, needs_revision, or rejected.\n"
        f"Task: {outcome}\nExecutor {selected[0].agent_id}: {first['output']}\nExecutor {selected[1].agent_id}: {second['output']}"
    )
    review = _call_agent(reviewer, task_id, context_id, review_prompt, timeout)
    review_status = review.get("review_status")
    if review_status not in {"approved", "needs_revision", "rejected"}:
        raise TaskExecutionError("independent reviewer omitted a valid review_status")
    state = "completed" if review_status == "approved" else review_status
    return {
        "task_id": task_id,
        "context_id": context_id,
        "state": state,
        "executors": [
            {"agent_id": selected[0].agent_id, "output": first["output"]},
            {"agent_id": selected[1].agent_id, "output": second["output"]},
        ],
        "reviewer": {"agent_id": reviewer.agent_id, "output": review["output"], "review_status": review_status},
        "review_status": review_status,
        "report": f"Task {task_id} state={state}; independent reviewer {reviewer.agent_id} returned {review_status}.",
        "provenance": {
            "transport": "A2A JSON-RPC message/send",
            "agent_count": 3,
            "upstream_task_ids": {
                selected[0].agent_id: first["upstream_task_id"],
                selected[1].agent_id: second["upstream_task_id"],
                reviewer.agent_id: review["upstream_task_id"],
            },
        },
    }
