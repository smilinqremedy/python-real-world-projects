"""
Unit tests for Nigerian Tax and Business Revenue Calculator.
"""
import unittest
import os
from finance_service import NigerianFinanceService, STATUTORY_DISCLAIMER

TEST_DB = "test_finance.db"
TEST_CSV = "test_financial_statement.csv"
TEST_PDF = "test_financial_report.pdf"


class TestNigerianBusinessFinance(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = NigerianFinanceService(TEST_DB)
        self.service.register_business(
            business_name="Lagos Tech Ventures Ltd",
            rc_number="RC-123456",
            tin="TIN-98765432-0001",
            business_type="Limited Liability Company (LLC)",
            sector="Technology & Software",
            contact_email="finance@lagostech.ng",
            contact_phone="+2348011223344",
        )

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        for path in [TEST_DB, TEST_CSV, TEST_PDF]:
            if os.path.exists(path):
                os.remove(path)

    # ==================== Business Registration Tests ====================

    def test_business_profile_registration(self):
        info = self.service.get_business_info()
        self.assertEqual(info["business_name"], "Lagos Tech Ventures Ltd")
        self.assertEqual(info["rc_number"], "RC-123456")
        self.assertEqual(info["currency"], "NGN")
        self.assertEqual(info["currency_symbol"], "₦")

    # ==================== Input Validation Tests ====================

    def test_sales_input_validation(self):
        # Negative amount
        with self.assertRaises(ValueError):
            self.service.record_sale("2026-05-10", "Product Sales", "Negative sale", -5000.0)

        # Zero amount
        with self.assertRaises(ValueError):
            self.service.record_sale("2026-05-10", "Product Sales", "Zero sale", 0.0)

        # Invalid date
        with self.assertRaises(ValueError):
            self.service.record_sale("10-05-2026", "Product Sales", "Wrong date format", 15000.0)

        # Invalid category
        with self.assertRaises(ValueError):
            self.service.record_sale("2026-05-10", "Gambling Win", "Invalid category", 50000.0)

    def test_expense_input_validation(self):
        # Negative expense
        with self.assertRaises(ValueError):
            self.service.record_expense("2026-05-11", "Rent", "Operating", "Negative rent", -10000.0)

        # Invalid type
        with self.assertRaises(ValueError):
            self.service.record_expense("2026-05-11", "Rent", "Personal", "Invalid type", 10000.0)

        # Invalid date
        with self.assertRaises(ValueError):
            self.service.record_expense("not-a-date", "Rent", "Operating", "Bad date", 10000.0)

    # ==================== Financial Calculation Tests ====================

    def test_revenue_and_profit_separation(self):
        # Record sales: 1,000,000 + 500,000 = 1,500,000
        self.service.record_sale("2026-06-01", "Product Sales", "Hardware delivery", 1000000.0)
        self.service.record_sale("2026-06-05", "Services Rendered", "Software support", 500000.0)

        # Record COGS: 400,000
        self.service.record_expense("2026-06-02", "Inventory", "COGS", "Direct hardware procurement", 400000.0)

        # Record OpEx: 300,000
        self.service.record_expense("2026-06-10", "Salaries", "Operating", "Developer payroll", 300000.0)

        pnl = self.service.calculate_profit_and_loss()

        # Revenue should strictly equal 1,500,000
        self.assertEqual(pnl["total_revenue"], 1500000.0)

        # Gross Profit = 1,500,000 - 400,000 = 1,100,000
        self.assertEqual(pnl["gross_profit"], 1100000.0)
        self.assertAlmostEqual(pnl["gross_margin_percent"], 73.33, places=1)

        # Net Profit = 1,100,000 - 300,000 = 800,000
        self.assertEqual(pnl["net_profit"], 800000.0)
        self.assertAlmostEqual(pnl["net_margin_percent"], 53.33, places=1)

        # Strict separation: revenue != net_profit
        self.assertNotEqual(pnl["total_revenue"], pnl["net_profit"])

    def test_monthly_summary(self):
        self.service.record_sale("2026-01-15", "Product Sales", "Jan sale", 200000.0)
        self.service.record_expense("2026-01-20", "COGS", "COGS", "Jan cost", 80000.0)
        self.service.record_sale("2026-02-15", "Services Rendered", "Feb sale", 300000.0)

        summaries = self.service.generate_monthly_financial_summary()
        self.assertEqual(len(summaries), 2)
        jan = next(s for s in summaries if s["month"] == "2026-01")
        self.assertEqual(jan["revenue"], 200000.0)
        self.assertEqual(jan["cogs"], 80000.0)
        self.assertEqual(jan["gross_profit"], 120000.0)

    # ==================== Nigerian Tax Estimation Tests ====================

    def test_small_company_tax_estimation_zero_cit(self):
        # Turnover <= 25,000,000 qualifies as Small Company under Finance Act -> 0% CIT
        self.service.record_sale("2026-01-10", "Product Sales", "Turnover", 15000000.0)
        self.service.record_expense("2026-01-15", "COGS", "COGS", "Direct costs", 5000000.0)
        self.service.record_expense("2026-01-20", "Rent", "Operating", "Office lease", 2000000.0)

        # Net Profit = 15M - 5M - 2M = 8,000,000
        tax = self.service.estimate_tax_obligations()

        self.assertEqual(tax["company_tier"], "Small Company")
        self.assertEqual(tax["cit_rate_applied"], 0.0)
        self.assertEqual(tax["estimated_cit"], 0.0)

        # Education Tax = 3% of 8M = 240,000
        self.assertEqual(tax["estimated_edt"], 240000.0)

        # Assumptions & Disclaimer validation
        self.assertTrue(len(tax["assumptions"]) > 0)
        self.assertIn("Small Company", tax["assumptions"][0])
        self.assertEqual(tax["disclaimer"], STATUTORY_DISCLAIMER)

    def test_medium_company_tax_estimation_twenty_percent(self):
        # Turnover between 25M and 100M -> 20% CIT
        self.service.record_sale("2026-01-10", "Wholesale", "Bulk supplies", 50000000.0)
        self.service.record_expense("2026-01-15", "COGS", "COGS", "Procurement", 30000000.0)
        self.service.record_expense("2026-01-20", "OpEx", "Operating", "Operations", 10000000.0)

        # Net Profit = 50M - 30M - 10M = 10,000,000
        tax = self.service.estimate_tax_obligations()

        self.assertEqual(tax["company_tier"], "Medium Company")
        self.assertEqual(tax["cit_rate_applied"], 0.20)
        # CIT = 20% of 10M = 2,000,000
        self.assertEqual(tax["estimated_cit"], 2000000.0)
        # EDT = 3% of 10M = 300,000
        self.assertEqual(tax["estimated_edt"], 300000.0)

    def test_configurable_tax_rules(self):
        # Modify tax rules dynamically: set small company threshold to 10M and small CIT to 5%
        self.service.update_tax_rules(
            small_turnover=10000000.0,
            medium_turnover=80000000.0,
            small_cit=0.05,
            medium_cit=0.22,
            large_cit=0.32,
            education_tax=0.04,
            vat=0.08,
            minimum_tax=0.01
        )

        rules = self.service.get_tax_rules()
        self.assertEqual(rules["small_turnover_threshold"], 10000000.0)
        self.assertEqual(rules["small_cit_rate"], 0.05)
        self.assertEqual(rules["education_tax_rate"], 0.04)

        # Record 5M turnover and 2M net profit
        self.service.record_sale("2026-02-01", "Services Rendered", "Tech services", 5000000.0)
        self.service.record_expense("2026-02-05", "Salaries", "Operating", "Salaries", 3000000.0)

        tax = self.service.estimate_tax_obligations()
        # CIT = 5% of 2M = 100,000
        self.assertEqual(tax["estimated_cit"], 100000.0)
        # EDT = 4% of 2M = 80,000
        self.assertEqual(tax["estimated_edt"], 80000.0)

    # ==================== Export Tests ====================

    def test_export_to_csv(self):
        self.service.record_sale("2026-03-01", "Product Sales", "Gadget sale", 150000.0)
        self.service.record_expense("2026-03-02", "Inventory", "COGS", "Stock purchase", 75000.0)

        file_path = self.service.export_financials_to_csv(TEST_CSV)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("NIGERIAN BUSINESS FINANCIAL STATEMENT", content)
            self.assertIn(STATUTORY_DISCLAIMER, content)
            self.assertIn("Gadget sale", content)

    def test_export_to_pdf(self):
        self.service.record_sale("2026-04-01", "Product Sales", "Enterprise Software", 2500000.0)
        self.service.record_expense("2026-04-02", "Hosting", "Operating", "Cloud Infrastructure", 300000.0)

        file_path = self.service.export_financials_to_pdf(TEST_PDF)
        self.assertTrue(os.path.exists(file_path))
        self.assertGreater(os.path.getsize(file_path), 500)

        with open(file_path, "rb") as f:
            header = f.read(8)
            self.assertEqual(header[:5], b"%PDF-")


if __name__ == "__main__":
    unittest.main()
