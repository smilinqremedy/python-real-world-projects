"""
Automated Unit Tests for Small Business Sales and Profit Analysis System
Validates product registration, sales recording, COGS computation, gross profit,
operational expenses, net profit, best-selling product ranking, daily/monthly reports.
"""

import os
import unittest
import tempfile
from database import initialize_database
from analytics_service import ProfitAnalyticsService


class TestSalesProfitAnalytics(unittest.TestCase):

    def setUp(self):
        # Create a temporary file database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        initialize_database(self.db_path)
        self.service = ProfitAnalyticsService(self.db_path)

        # Register sample products
        # Product 1: Cost 20, Selling 50 -> Gross margin: 30 per unit (60%)
        self.p1 = self.service.register_product("Wireless Keyboard", 20.0, 50.0, "Electronics & Accessories")
        # Product 2: Cost 5, Selling 15 -> Gross margin: 10 per unit (66.7%)
        self.p2 = self.service.register_product("Mouse Pad", 5.0, 15.0, "Electronics & Accessories")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_register_product_and_pricing(self):
        """Features 1, 2, 3: Register products and update pricing."""
        p3 = self.service.register_product("USB-C Hub", 12.0, 30.0)
        self.assertEqual(p3["cost_price"], 12.0)
        self.assertEqual(p3["selling_price"], 30.0)

        # Pricing update
        updated = self.service.update_product_pricing(p3["product_id"], new_cost_price=14.0, new_selling_price=35.0)
        self.assertEqual(updated["cost_price"], 14.0)
        self.assertEqual(updated["selling_price"], 35.0)

    def test_pricing_validation(self):
        """Test negative or zero prices are rejected."""
        with self.assertRaises(ValueError):
            self.service.register_product("Bad Prod", -10.0, 20.0)
        with self.assertRaises(ValueError):
            self.service.register_product("Bad Prod 2", 10.0, 0.0)

    def test_record_sales_and_cogs_calculation(self):
        """Features 4, 5, 6, 7: Record sale, calculate revenue, COGS, and gross profit."""
        # Sell 4 units of Product 1 (Cost 20, Price 50)
        # Revenue = 4 * 50 = 200. COGS = 4 * 20 = 80. Gross Profit = 200 - 80 = 120
        sale = self.service.record_sale(self.p1["product_id"], quantity=4, sale_date="2026-11-10")
        self.assertEqual(sale["quantity"], 4)
        self.assertEqual(sale["total_revenue"], 200.0)
        self.assertEqual(sale["total_cogs"], 80.0)
        self.assertEqual(sale["gross_profit"], 120.0)

    def test_record_operational_expenses(self):
        """Feature 8: Record operational expenses."""
        exp = self.service.record_operational_expense(
            expense_date="2026-11-05",
            category="Rent & Facilities",
            amount=50.0,
            description="Office monthly rent share"
        )
        self.assertEqual(exp["amount"], 50.0)
        self.assertEqual(exp["category"], "Rent & Facilities")

    def test_calculate_net_profit(self):
        """Feature 9 & 13: Calculate net profit = Gross Profit - Operating Expenses."""
        # Sale: 10 units of p1 -> Rev = 500, COGS = 200, Gross Profit = 300
        self.service.record_sale(self.p1["product_id"], quantity=10, sale_date="2026-11-15")

        # Operational expenses: $100 Rent + $40 Internet = $140
        self.service.record_operational_expense("2026-11-01", "Rent & Facilities", 100.0, "Store Rent")
        self.service.record_operational_expense("2026-11-02", "Utilities (Power, Water, Internet)", 40.0, "Fiber Internet")

        summary = self.service.calculate_overall_financial_summary()
        self.assertEqual(summary["total_revenue"], 500.0)
        self.assertEqual(summary["total_cogs"], 200.0)
        self.assertEqual(summary["gross_profit"], 300.0)
        self.assertEqual(summary["total_operational_expenses"], 140.0)
        self.assertEqual(summary["total_expenses"], 340.0)  # 200 + 140
        self.assertEqual(summary["net_profit"], 160.0)      # 300 - 140 = 160
        self.assertEqual(summary["gross_margin_pct"], 60.0) # 300 / 500
        self.assertEqual(summary["net_margin_pct"], 32.0)   # 160 / 500

    def test_identify_best_selling_products(self):
        """Feature 10: Identify best-selling products by units and revenue."""
        # Product 1: 3 units -> 150 rev
        self.service.record_sale(self.p1["product_id"], quantity=3)
        # Product 2: 10 units -> 150 rev
        self.service.record_sale(self.p2["product_id"], quantity=10)

        # Ranked by units: Product 2 should be #1 (10 units vs 3 units)
        ranked_units = self.service.identify_best_selling_products(rank_by="units")
        self.assertEqual(ranked_units[0]["product_id"], self.p2["product_id"])
        self.assertEqual(ranked_units[0]["total_units_sold"], 10)

    def test_daily_sales_report(self):
        """Feature 11: Generate daily sales report."""
        target = "2026-11-18"
        self.service.record_sale(self.p1["product_id"], quantity=2, sale_date=target)
        self.service.record_sale(self.p2["product_id"], quantity=4, sale_date=target)

        rep = self.service.generate_daily_sales_report(target)
        self.assertEqual(rep["report_date"], target)
        self.assertEqual(rep["transaction_count"], 2)
        self.assertEqual(rep["units_sold"], 6)  # 2 + 4
        # Rev: 2*50 + 4*15 = 100 + 60 = 160
        self.assertEqual(rep["total_revenue"], 160.0)
        # COGS: 2*20 + 4*5 = 40 + 20 = 60
        self.assertEqual(rep["total_cogs"], 60.0)
        # Profit: 160 - 60 = 100
        self.assertEqual(rep["gross_profit"], 100.0)

    def test_monthly_financial_report(self):
        """Feature 12: Generate monthly P&L financial statement."""
        month = "2026-11"
        self.service.record_sale(self.p1["product_id"], quantity=5, sale_date="2026-11-05")  # Rev 250, COGS 100, GP 150
        self.service.record_operational_expense("2026-11-08", "Staff Salaries & Wages", 50.0, "Part-time assistant")

        pnl = self.service.generate_monthly_financial_report(month)
        self.assertEqual(pnl["month"], month)
        self.assertEqual(pnl["revenue"], 250.0)
        self.assertEqual(pnl["cogs"], 100.0)
        self.assertEqual(pnl["gross_profit"], 150.0)
        self.assertEqual(pnl["operational_expenses_total"], 50.0)
        self.assertEqual(pnl["net_profit"], 100.0)  # 150 - 50 = 100


if __name__ == "__main__":
    unittest.main()
