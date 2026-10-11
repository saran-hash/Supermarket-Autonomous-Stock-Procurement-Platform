import unittest
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

run_forecast = importlib.import_module("skills.festival-demand.forecast_demand").run_forecast
run_audit = importlib.import_module("skills.stock-monitor.audit_stock").run_audit
run_optimizer = importlib.import_module("skills.procurement-optimizer.select_dealer").run_optimizer
import agent.guardrails as guardrails


class TestSkills(unittest.TestCase):
    def test_festival_forecast(self):
        res = run_forecast("2026-10-25")
        self.assertIn("category_multipliers", res)
        self.assertEqual(res["category_multipliers"].get("Edible Oils"), 2.2)

    def test_stock_audit(self):
        reqs = run_audit()
        self.assertIsInstance(reqs, list)
        self.assertTrue(len(reqs) > 0)
        skus = [r["sku_id"] for r in reqs]
        self.assertIn("SKU-OIL-SUN-001", skus)

    def test_procurement_optimizer(self):
        plan = run_optimizer()
        self.assertIsInstance(plan, dict)
        self.assertTrue(len(plan) > 0)
        self.assertIn("DLR-001", plan)

    def test_guardrails(self):
        ok, msg = guardrails.check_order_spending_limit(15000.0)
        self.assertTrue(ok)

        ok, msg = guardrails.check_order_spending_limit(75000.0)
        self.assertFalse(ok)
        self.assertIn("HIGH_VALUE_THRESHOLD", msg)


if __name__ == "__main__":
    unittest.main()
