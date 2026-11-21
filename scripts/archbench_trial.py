"""Local, non-admitting ArchBench trial adapter. Never executes candidate code."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "archbench_federation"
ALLOWED = {"T01", "T02", "T03", "T04"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--task", required=True, choices=sorted(ALLOWED))
    parser.add_argument("--solution", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "archbench_trial_result.json")
    args = parser.parse_args()
    if not (BENCH / "run_check.py").is_file():
        parser.error("Federation bench copy is missing")
    if not args.solution.is_file() or args.solution.stat().st_size > 1_000_000:
        parser.error("Solution missing or too large")
    try:
        data = json.loads(args.solution.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        parser.error(f"Invalid JSON: {exc}")
    if not isinstance(data, (dict, list)):
        parser.error("Solution must be JSON object or array")
    result = subprocess.run(
        [sys.executable, str(BENCH / "run_check.py"), args.task,
         str(args.solution.resolve()), "--json"],
        cwd=BENCH, capture_output=True, text=True, timeout=30,
    )
    receipt = {
        "candidate": args.candidate, "task": args.task,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "exit_code": result.returncode,
        "checker_stdout": result.stdout[-12000:],
        "checker_stderr": result.stderr[-2000:],
        "membership_action": "none",
        "status": "evaluated" if result.returncode == 0 else "checker_failed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if result.returncode == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
