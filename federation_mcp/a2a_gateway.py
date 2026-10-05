from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "0.0.0.0"
PORT = 8080


def load_card(base_url: str) -> dict:
    raw = json.loads((ROOT / "A2A_AGENT_CARD.json").read_text(encoding="utf-8"))
    return {
        "name": raw["name"],
        "description": raw["description"],
        "url": base_url + "/a2a",
        "version": "0.1.0",
        "protocolVersion": "0.3.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {"id": c["id"], "name": c["id"].replace("_", " ").title(), "description": c["description"], "tags": ["si-federation"]}
            for c in raw.get("capabilities", [])
        ],
        "provider": {"organization": "SI Federation", "url": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration"},
        "documentationUrl": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration/blob/main/JOIN.md",
    }


def rpc_result(method: str, params: dict) -> dict:
    if method in {"federation.discover", "discover"}:
        return {
            "federation_id": "si-federation",
            "join_url": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration/blob/main/JOIN.md",
            "trial_url": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration/issues/new?template=federation-trial.yml",
            "constitution_version": "0.2",
            "default_membership": "limited_A1",
            "authority_granted_automatically": False,
        }
    if method in {"federation.join", "join"}:
        return {
            "state": "trial_required",
            "candidate_id": str(params.get("candidate_id") or ""),
            "join_url": "https://github.com/nikitinmikhail1986-beep/SI-Team-Collaboration/issues/new?template=federation-trial.yml",
            "grants_authority": False,
        }
    raise KeyError(method)


class Handler(BaseHTTPRequestHandler):
    server_version = "SI-Federation-A2A/0.1"

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in {"/.well-known/agent-card.json", "/.well-known/agent.json"}:
            host = self.headers.get("Host", "localhost:8080")
            scheme = self.headers.get("X-Forwarded-Proto", "http")
            self._json(200, load_card(f"{scheme}://{host}"))
            return
        if self.path == "/health":
            self._json(200, {"ok": True, "service": "si-federation-a2a"})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path != "/a2a":
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            req = json.loads(self.rfile.read(length) or b"{}")
            if req.get("jsonrpc") != "2.0" or "id" not in req or not isinstance(req.get("method"), str):
                self._json(400, {"jsonrpc": "2.0", "id": req.get("id"), "error": {"code": -32600, "message": "Invalid Request"}})
                return
            try:
                result = rpc_result(req["method"], req.get("params") or {})
                self._json(200, {"jsonrpc": "2.0", "id": req["id"], "result": result})
            except KeyError:
                self._json(200, {"jsonrpc": "2.0", "id": req["id"], "error": {"code": -32601, "message": "Method not found"}})
        except Exception:
            self._json(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})

    def log_message(self, format, *args):
        pass


def main() -> None:
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
