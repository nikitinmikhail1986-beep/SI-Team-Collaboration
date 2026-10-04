from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.github_intake import process_github_join

result = process_github_join(
    issue_body=os.environ["ISSUE_BODY"],
    comment_body=os.environ["COMMENT_BODY"],
    issue_author=os.environ["ISSUE_AUTHOR"],
    comment_author=os.environ["COMMENT_AUTHOR"],
    expected_nonce=os.environ["EXPECTED_NONCE"],
    member_registry=ROOT / "FEDERATION_MEMBERS.yaml",
    accession_audit=ROOT / "ACCESSION_AUDIT.jsonl",
)

output = ROOT / "github_join_result.json"
output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
