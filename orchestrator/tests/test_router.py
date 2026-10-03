import unittest
from orchestrator.si_router import classify, build_plan

class RouterTests(unittest.TestCase):
    def test_ifc_routes_bim(self):
        self.assertIn("cad_bim", classify("Проверь IFC модель и замечания BIM"))

    def test_repo_routes_coding(self):
        self.assertIn("coding", classify("Обнови репозиторий и проверь git"))

    def test_review_routes_independent_review(self):
        self.assertIn("independent_review", classify("Проверь замечания эксперта"))

    def test_plan_preserves_human_boundary(self):
        plan = build_plan("Настрой MCP")
        self.assertEqual(plan["status"], "Planned")
        self.assertIn("authorization", plan["human_interrupt_policy"])

if __name__ == "__main__":
    unittest.main()
