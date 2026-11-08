from __future__ import annotations

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://si-federation-a2a.onrender.com"
OPENER = build_opener(type("NoRedirect", (HTTPRedirectHandler,), {"redirect_request": lambda self, *args, **kwargs: None})())


def get_json(path: str) -> dict:
    request = Request(BASE_URL + path, headers={"Accept": "application/json"})
    with OPENER.open(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"{path} returned HTTP {response.status}")
        value = json.loads(response.read(65_537).decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} response was not an object")
    return value


def main() -> int:
    try:
        health = get_json("/health")
        card = get_json("/.well-known/agent-card.json")
        request_id = "health-auth-check"
        body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": "si.worker/status", "params": {}}).encode("utf-8")
        request = Request(BASE_URL + "/a2a", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with OPENER.open(request, timeout=20) as response:
            result = json.loads(response.read(65_537).decode("utf-8"))
        if health.get("ok") is not True or health.get("service") != "si-federation-a2a":
            raise RuntimeError("primary Render health response is invalid")
        if card.get("name") != "SI Federation" or not any(skill.get("id") == "federation_discovery" for skill in card.get("skills", [])):
            raise RuntimeError("primary Render agent card is invalid")
        if result.get("id") != request_id or result.get("error", {}).get("message") != "Unauthorized":
            raise RuntimeError("worker endpoint did not reject an anonymous request")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        print(f"Primary gateway check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("Primary Render health, agent card, and anonymous worker-auth boundary verified.")
    print("SI_FEDERATION_PRIMARY_GATEWAY_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
