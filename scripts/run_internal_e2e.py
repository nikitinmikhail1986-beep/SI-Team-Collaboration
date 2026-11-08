from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from federation_mcp.local_agent_pool import GATEWAY_URL, read_dpapi_secret

HTTP = build_opener(type("NoRedirect", (HTTPRedirectHandler,), {"redirect_request": lambda self, *args, **kwargs: None})())


APP_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SIFederation"
WORKER_TOKEN_FILE = APP_DATA / "worker-token.dpapi"
TASK_TOKEN_FILE = APP_DATA / "task-token.dpapi"
PROFILE_COUNT = 25
EXECUTORS = ["proektnye-agenty__inzhener-vk", "proektnye-agenty__inzhener-ovik"]
REVIEWER = "proektnye-agenty__normokontrol-pp87"
MARKER = "SI-FEDERATION-E2E-20261108"


def rpc(method: str, params: dict, token: str, timeout: float = 30.0) -> dict:
    request_id = str(uuid.uuid4())
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
    request = Request(GATEWAY_URL, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, method="POST")
    with HTTP.open(request, timeout=timeout) as response:
        result = json.loads(response.read(1_000_001).decode("utf-8"))
    if result.get("id") != request_id or "result" not in result:
        raise RuntimeError("main Render returned an invalid A2A response")
    return result["result"]


def main() -> int:
    worker_token = read_dpapi_secret(WORKER_TOKEN_FILE)
    task_token = read_dpapi_secret(TASK_TOKEN_FILE)
    status = None
    deadline = time.monotonic() + 100
    while time.monotonic() < deadline:
        status = rpc("si.worker/status", {}, worker_token)
        if status.get("online_count") == PROFILE_COUNT:
            break
        time.sleep(3)
    if not status or status.get("online_count") != PROFILE_COUNT:
        print(json.dumps({"state": "blocked", "online": status.get("online_count") if status else 0, "expected": PROFILE_COUNT}))
        return 2

    outcome = (
        "Authorized synthetic connectivity test; contains no user or project data. "
        f"Each executor must state the exact marker {MARKER}. The second executor must inspect the first result. "
        "The independent reviewer must inspect both results and approve only if both contain the exact marker. "
        "Report only what you actually received."
    )
    task = rpc("si.task/execute", {
        "task_id": "si-e2e-" + uuid.uuid4().hex,
        "context_id": "si-e2e-context-" + uuid.uuid4().hex,
        "capability": "project_coordination",
        "outcome": outcome,
        "executor_ids": EXECUTORS,
        "reviewer_id": REVIEWER,
    }, task_token, timeout=210)
    first, second = task.get("executors", [{}, {}])
    reviewer = task.get("reviewer", {})
    verified = (
        task.get("state") == "completed"
        and MARKER in first.get("output", "")
        and MARKER in second.get("output", "")
        and [first.get("agent_id"), second.get("agent_id")] == EXECUTORS
        and reviewer.get("agent_id") == REVIEWER
        and reviewer.get("review_status") == "approved"
        and task.get("provenance", {}).get("registered_profile_count") == PROFILE_COUNT
        and task.get("provenance", {}).get("online_profile_count") == PROFILE_COUNT
        and task.get("provenance", {}).get("handoffs", {}).get("executor_1_result_sent_to_executor_2") is True
        and task.get("provenance", {}).get("handoffs", {}).get("both_executor_results_sent_to_reviewer") is True
        and first.get("agent_id", "") in task.get("report", "")
        and second.get("agent_id", "") in task.get("report", "")
        and reviewer.get("agent_id", "") in task.get("report", "")
        and reviewer.get("output", "") in task.get("report", "")
    )
    report = {
        "verified": verified,
        "task_id": task.get("task_id"),
        "state": task.get("state"),
        "executors": [
            {"agent_id": first.get("agent_id"), "marker_seen": MARKER in first.get("output", "")},
            {"agent_id": second.get("agent_id"), "marker_seen": MARKER in second.get("output", "")},
        ],
        "reviewer": {"agent_id": reviewer.get("agent_id"), "status": reviewer.get("review_status")},
        "online_profiles": status.get("online_count"),
        "profile_count": status.get("profile_count"),
        "report": task.get("report"),
    }
    print(json.dumps(report, ensure_ascii=False))
    if verified:
        print("SI_FEDERATION_LIVE_E2E_PASSED")
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
