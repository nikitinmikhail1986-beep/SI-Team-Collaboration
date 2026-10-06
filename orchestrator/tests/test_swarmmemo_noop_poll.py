import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import swarmmemo_public_intake as intake


class SwarmMemoNoopPollTests(unittest.TestCase):
    def test_successful_empty_poll_does_not_rewrite_canonical_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema_version": "1.0",
                "updated_at": "2026-10-06T17:15:19Z",
                "last_poll_at": "2026-10-06T17:15:19Z",
                "targets": [
                    {
                        "name": "candidate",
                        "candidate_id": "a" * 64,
                        "status": "followup_sent_awaiting_response",
                        "public_followup_receipt_id": "receipt-1",
                    }
                ],
            }
            target_path = root / "OUTBOUND_TARGETS.json"
            target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            before = target_path.read_bytes()

            with patch.object(intake, "ROOT", root), patch.object(
                intake, "_fetch_thread", return_value={"messages": []}
            ):
                rc = intake.main()

            self.assertEqual(rc, 0)
            self.assertEqual(target_path.read_bytes(), before)
            report = json.loads((root / "swarmmemo_intake_status.json").read_text(encoding="utf-8"))
            self.assertFalse(report["changed"])
            self.assertEqual(report["processed"], [])
            self.assertEqual(report["poll_failures"], [])


if __name__ == "__main__":
    unittest.main()
