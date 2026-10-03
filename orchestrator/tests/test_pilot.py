import unittest

from orchestrator.pilot import run_internal_pilot


class InternalPilotTests(unittest.TestCase):
    def test_internal_pilot_passes_end_to_end_protocol_checks(self):
        result = run_internal_pilot()
        self.assertTrue(result["overall_pass"])
        self.assertTrue(result["identity_preserved_across_runtime_change"])
        self.assertTrue(result["runtime_change_requires_reverification"])
        self.assertTrue(result["council_advisory_only"])


if __name__ == "__main__":
    unittest.main()
