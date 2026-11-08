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
PROFILE_COUNT = 25


def main() -> int:
    token = read_dpapi_secret(WORKER_TOKEN_FILE)
    request_id = str(uuid.uuid4())
    body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": "si.worker/status", "params": {}}).encode("utf-8")
    request = Request(GATEWAY_URL, data=body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, method="POST")
    deadline = time.monotonic() + 100
    status = None
    while time.monotonic() < deadline:
        with HTTP.open(request, timeout=30) as response:
            result = json.loads(response.read(65_537).decode("utf-8"))
        if result.get("id") != request_id or "result" not in result:
            raise RuntimeError("primary Render returned an invalid worker status response")
        status = result["result"]
        if status.get("online_count") == PROFILE_COUNT and status.get("profile_count") == PROFILE_COUNT:
            break
        time.sleep(3)
    print(json.dumps({"state": status.get("state") if status else None,
                      "online_profiles": status.get("online_count") if status else 0,
                      "registered_profiles": status.get("profile_count") if status else 0}, ensure_ascii=False))
    if not status or status.get("state") != "ready" or status.get("online_count") != PROFILE_COUNT or status.get("profile_count") != PROFILE_COUNT:
        return 1
    print("SI_FEDERATION_25_PROFILES_ONLINE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
