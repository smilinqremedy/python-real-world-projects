"""
Automated unit tests for Pharmacy Inventory and Sales Management System.
"""

import os
import tempfile
import unittest
from pharmacy_service import PharmacyService


class TestPharmacyManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = PharmacyService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_medicine_and_batch_registration(self):
        med = self.service.register_medicine("M-PARA", "Paracetamol 500mg", "Analgesics", "Tablets", 20)
        self.assertEqual(med["medicine_code"], "M-PARA")
        self.assertEqual(med["reorder_level"], 20)

        # Batch addition
        batch = self.service.record_medicine_purchase(
            medicine_code="M-PARA",
            batch_number="B-101",
            cost_price=1.50,
            selling_price=3.00,
            quantity=100,
            manufacture_date_str="2026-01-01",
            expiry_date_str="2027-01-01"
        )
        self.assertEqual(batch["batch_number"], "B-101")
        self.assertEqual(batch["quantity"], 100)

        # Selling price less than cost price rejected
        with self.assertRaises(ValueError):
            self.service.record_medicine_purchase("M-PARA", "B-102", 5.0, 4.0, 50, "2026-01-01", "2027-01-01")

        # Expiry before manufacture rejected
        with self.assertRaises(ValueError):
            self.service.record_medicine_purchase("M-PARA", "B-103", 2.0, 3.0, 50, "2026-05-01", "2026-01-01")

    def test_sales_and_stock_deduction(self):
        self.service.register_medicine("M-AMOX", "Amoxicillin 250mg", "Antibiotics", "Capsules", 15)
        self.service.record_medicine_purchase("M-AMOX", "B-201", 3.0, 5.50, 40, "2026-01-01", "2027-06-01")

        # Process sale of 10 capsules
        sale = self.service.process_sale("B-201", 10, "2026-06-01")
        self.assertEqual(sale["quantity"], 10)
        self.assertEqual(sale["total_price"], 55.0)
        self.assertEqual(sale["remaining_batch_stock"], 30)

        # Insufficient stock: requesting 35 when only 30 remain
        with self.assertRaises(ValueError) as ctx:
            self.service.process_sale("B-201", 35, "2026-06-02")
        self.assertIn("Insufficient stock", str(ctx.exception))

    def test_expired_product_sale_prevention(self):
        self.service.register_medicine("M-COUGH", "Cough Syrup", "Expectorants", "Syrup", 5)
        # Batch expired on 2026-05-01
        self.service.record_medicine_purchase("M-COUGH", "B-OLD", 4.0, 7.0, 20, "2025-01-01", "2026-05-01")

        # Attempting sale on 2026-06-01 must be REJECTED!
        with self.assertRaises(ValueError) as ctx:
            self.service.process_sale("B-OLD", 2, "2026-06-01")
        self.assertIn("expired", str(ctx.exception).lower())

    def test_expiry_alerts_and_low_stock(self):
        self.service.register_medicine("M-VITC", "Vitamin C 1000mg", "Vitamins", "Tablets", 50)
        # Batch expiring on 2026-11-20 (within 30 days of 2026-11-01)
        self.service.record_medicine_purchase("M-VITC", "B-VIT1", 2.0, 4.0, 30, "2025-11-01", "2026-11-20")

        # Low stock check (30 <= 50)
        low = self.service.get_low_stock_medicines()
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0]["medicine_code"], "M-VITC")

        # Expiry alert check as of 2026-11-01
        alerts = self.service.get_expiry_alerts(30, "2026-11-01")
        self.assertEqual(len(alerts["approaching_expiry_batches"]), 1)
        self.assertEqual(alerts["approaching_expiry_batches"][0]["batch_number"], "B-VIT1")

    def test_sales_report(self):
        self.service.register_medicine("M-IBU", "Ibuprofen 400mg", "Analgesics", "Tablets", 10)
        self.service.record_medicine_purchase("M-IBU", "B-IBU1", 1.0, 2.50, 50, "2026-01-01", "2027-01-01")

        self.service.process_sale("B-IBU1", 10, "2026-11-15")
        self.service.process_sale("B-IBU1", 4, "2026-11-15")

        rep = self.service.generate_sales_report(target_date="2026-11-15")
        self.assertEqual(rep["transactions_count"], 2)
        self.assertEqual(rep["total_units_sold"], 14)
        self.assertEqual(rep["total_revenue"], 35.0)


if __name__ == "__main__":
    unittest.main()
