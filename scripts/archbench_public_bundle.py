"""Export only public ArchBench task inputs, never private checkers or references."""
from pathlib import Path
import argparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "archbench_federation" / "tasks"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, choices=["T01", "T02", "T03", "T04"])
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    dirs = sorted(BENCH.glob(args.task + "_*/public"))
    if len(dirs) != 1:
        p.error("Task not found")
    source = dirs[0]
    files = sorted(f for f in source.rglob("*") if f.is_file())
    if not files:
        p.error("Empty public task")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(source))
    print(f"Public-only task archive: {args.output} ({len(files)} files)")

if __name__ == "__main__":
    main()
