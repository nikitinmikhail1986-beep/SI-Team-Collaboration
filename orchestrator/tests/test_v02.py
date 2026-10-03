import unittest
from pathlib import Path
from orchestrator.models import make_task_id
from orchestrator.runtime import discover
from orchestrator.si_router import build_task

ROOT = Path(__file__).resolve().parents[2]

class V02Tests(unittest.TestCase):
    def test_task_has_one_leader(self):
        task = build_task("Проверь том ТХ и замечания")
        self.assertEqual(task.leader, "operational_leader")

    def test_task_id_is_stable(self):
        self.assertEqual(make_task_id("abc"), make_task_id("abc"))

    def test_execution_plan_has_verify(self):
        task = build_task("Проверь IFC")
        self.assertTrue(any(x["stage"] == "Verify" for x in task.execution_plan))

    def test_runtime_discovery_returns_evidence(self):
        items = discover(ROOT)
        self.assertTrue(items)
        self.assertTrue(all(item.status in {"tested", "configured", "unknown"} for item in items))

    def test_document_task_gets_document_capability(self):
        task = build_task("Подготовь исправленный том документации")
        self.assertIn("document_work", task.required_capabilities)

if __name__ == "__main__":
    unittest.main()
