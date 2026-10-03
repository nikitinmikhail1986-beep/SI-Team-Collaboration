from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from .models import RuntimeParticipant

def _command_ok(command: list[str], cwd: Path | None = None, timeout: int = 5) -> tuple[bool, str]:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        text = (result.stdout or result.stderr).strip().splitlines()
        return result.returncode == 0, (text[0] if text else f"exit={result.returncode}")
    except Exception as exc:
        return False, type(exc).__name__

def discover(repo_root: Path) -> list[RuntimeParticipant]:
    found: list[RuntimeParticipant] = []

    git = shutil.which("git")
    if git:
        ok, evidence = _command_ok([git, "--version"])
        found.append(RuntimeParticipant("git", "tool", "tested" if ok else "configured", ["coding"], evidence))

    gh = shutil.which("gh")
    if gh:
        ok, evidence = _command_ok([gh, "auth", "status"], timeout=8)
        found.append(RuntimeParticipant("github_cli", "tool", "tested" if ok else "configured", ["coding"], evidence))

    python = shutil.which("python")
    if python:
        ok, evidence = _command_ok([python, "--version"])
        found.append(RuntimeParticipant("python", "runtime", "tested" if ok else "configured", ["coding"], evidence))

    bridge = repo_root.parent / "local-ai-bridge"
    found.append(RuntimeParticipant("local_ai_bridge", "integration", "unknown", ["coordination", "knowledge_stewardship"], "Runtime path is environment-specific; active MCP probe required."))

    return found
