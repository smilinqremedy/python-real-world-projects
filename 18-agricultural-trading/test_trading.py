"""
Automated unit tests for Agricultural Produce Trading System.
"""

import os
import tempfile
import unittest
from trading_service import TradingService


class TestAgriculturalTrading(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = TradingService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_farmer_and_buyer_registration(self):
        f = self.service.register_farmer("F-01", "Green Valley Farms", "Iowa", "555-1010")
        self.assertEqual(f["farmer_code"], "F-01")

        with self.assertRaises(ValueError):
            self.service.register_farmer("F-01", "Duplicate Farm", "Ohio", "555-2020")

        b = self.service.register_buyer("B-01", "Whole Foods Depo", "555-3030", "Whole Foods LLC")
        self.assertEqual(b["buyer_code"], "B-01")

    def test_produce_addition_and_restock(self):
        self.service.register_farmer("F-02", "Sunshine Fields", "California", "555-4040")

        p = self.service.add_produce("F-02", "PRD-CORN", "Sweet Corn", "Grains", "bag", 50.0, 15.0)
        self.assertEqual(p["produce_code"], "PRD-CORN")
        self.assertEqual(p["available_quantity"], 50.0)

        # Invalid price
        with self.assertRaises(ValueError):
            self.service.add_produce("F-02", "PRD-SOY", "Soybeans", "Legumes", "bag", 20.0, -5.0)

        # Restock
        updated = self.service.restock_produce("PRD-CORN", 25.0)
        self.assertEqual(updated["available_quantity"], 75.0)

    def test_purchase_and_insufficient_stock_prevention(self):
        self.service.register_farmer("F-03", "Valley Harvest", "Oregon", "555-5050")
        self.service.register_buyer("B-02", "Bakery Supply", "555-6060")

        self.service.add_produce("F-03", "PRD-WHEAT", "Hard Red Winter Wheat", "Grains", "bag", 20.0, 30.0)

        # Insufficient stock: requesting 25 bags when only 20 available
        with self.assertRaises(ValueError):
            self.service.process_purchase("B-02", "PRD-WHEAT", 25.0)

        # Valid purchase of 12 bags
        inv = self.service.process_purchase("B-02", "PRD-WHEAT", 12.0, "2026-11-08")
        self.assertEqual(inv["quantity"], 12.0)
        self.assertEqual(inv["total_price"], 360.0)  # 12 * 30.0
        self.assertEqual(inv["remaining_stock"], 8.0)

        # Verify stock updated in db
        prod = self.service.get_produce_by_code("PRD-WHEAT")
        self.assertEqual(prod["available_quantity"], 8.0)

    def test_sales_report(self):
        self.service.register_farmer("F-04", "Midwest Ag", "Nebraska", "555-7070")
        self.service.register_buyer("B-03", "Metro Milling", "555-8080")

        self.service.add_produce("F-04", "PRD-OATS", "Rolled Oats", "Grains", "bag", 100.0, 10.0)
        self.service.process_purchase("B-03", "PRD-OATS", 10.0, "2026-11-09")
        self.service.process_purchase("B-03", "PRD-OATS", 5.0, "2026-11-09")

        rep = self.service.generate_sales_report("2026-11-09", "2026-11-09")
        self.assertEqual(rep["transaction_count"], 2)
        self.assertEqual(rep["total_volume_sold"], 15.0)
        self.assertEqual(rep["total_revenue"], 150.0)
        self.assertEqual(len(rep["sales_by_produce"]), 1)


if __name__ == "__main__":
    unittest.main()
