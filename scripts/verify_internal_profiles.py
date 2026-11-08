from __future__ import annotations

import compileall
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from federation_mcp.internal_agents import load_internal_profiles


def main() -> int:
    profile_dir = Path(os.environ.get("CODEX_AGENT_PROFILE_DIR", Path.home() / ".codex" / "agents"))
    profiles = load_internal_profiles()
    missing = [profile.agent_id for profile in profiles if not (profile_dir / f"{profile.agent_id}.toml").is_file()]
    without_instructions: list[str] = []
    for profile in profiles:
        profile_path = profile_dir / f"{profile.agent_id}.toml"
        if not profile_path.is_file():
            continue
        try:
            import tomllib
            spec = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"Invalid local profile {profile.agent_id}: {type(exc).__name__}", file=sys.stderr)
            return 1
        if not isinstance(spec.get("developer_instructions"), str) or not spec["developer_instructions"].strip():
            without_instructions.append(profile.agent_id)
    if missing or without_instructions:
        print(f"Missing profile files: {missing}; missing instructions: {without_instructions}", file=sys.stderr)
        return 1
    if not compileall.compile_dir(ROOT / "federation_mcp", quiet=1) or not compileall.compile_dir(ROOT / "orchestrator", quiet=1):
        print("Python compilation failed", file=sys.stderr)
        return 1
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "orchestrator/tests", "-v"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode:
        return result.returncode
    print(f"Verified {len(profiles)} local profile files with developer instructions.")
    print("SI_FEDERATION_LOCAL_VALIDATION_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
