"""
Automated unit tests for Technical Repair Service Management System.
"""

import os
import tempfile
import unittest
from repair_service import RepairService


class TestTechnicalRepair(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = RepairService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_customer_and_tech_registration(self):
        c = self.service.register_customer("C-01", "Walter White", "555-0199", "walter@heisenberg.com")
        self.assertEqual(c["customer_code"], "C-01")

        with self.assertRaises(ValueError):
            self.service.register_customer("C-01", "Duplicate Walter", "555-0000")

        t = self.service.register_technician("T-01", "Jesse Pinkman", "Smartphones", "555-0299")
        self.assertEqual(t["tech_code"], "T-01")

    def test_device_checkin_and_assignment(self):
        self.service.register_customer("C-10", "Gus Fring", "555-0399")
        self.service.register_technician("T-10", "Mike Ehrmantraut", "Electronics", "555-0499")

        d = self.service.check_in_device(
            customer_code="C-10",
            device_type="Smartphone",
            brand="Apple",
            model="iPhone 13 Pro",
            problem_description="Cracked screen and swollen battery"
        )
        self.assertTrue(d["reference_number"].startswith("REP-"))
        self.assertEqual(d["status"], "Received")

        # Assign technician transitions status to Diagnosing
        assigned = self.service.assign_technician(d["reference_number"], "T-10")
        self.assertEqual(assigned["technician_name"], "Mike Ehrmantraut")
        self.assertEqual(assigned["status"], "Diagnosing")

    def test_collection_prevention_rules(self):
        self.service.register_customer("C-20", "Saul Goodman", "555-0599")
        self.service.register_technician("T-20", "Kim Wexler", "Laptops", "555-0699")

        d = self.service.check_in_device("C-20", "Laptop", "Dell", "XPS 15", "Liquid spill on keyboard")
        ref = d["reference_number"]
        self.service.assign_technician(ref, "T-20")

        # Set costs: $150 parts + $100 labor = $250
        self.service.set_repair_costs(ref, 150.0, 100.0)

        # 1. Attempting to collect while in Diagnosing status fails
        with self.assertRaises(ValueError) as ctx1:
            self.service.update_repair_status(ref, "Collected")
        self.assertIn("before repair is completed", str(ctx1.exception))

        # Move to Repairing then Completed
        self.service.update_repair_status(ref, "Repairing")
        self.service.update_repair_status(ref, "Completed")

        # 2. Attempting to collect when Completed but UNPAID fails
        with self.assertRaises(ValueError) as ctx2:
            self.service.update_repair_status(ref, "Collected")
        self.assertIn("before payment confirmation", str(ctx2.exception))

        # Partial payment: $100 paid out of $250
        self.service.record_payment(ref, 100.0)
        with self.assertRaises(ValueError):
            self.service.update_repair_status(ref, "Collected")

        # Full payment: remaining $150 paid
        self.service.record_payment(ref, 150.0)

        # 3. Now collection succeeds
        collected = self.service.update_repair_status(ref, "Collected")
        self.assertEqual(collected["status"], "Collected")

    def test_search_and_reports(self):
        self.service.register_customer("C-30", "Hank Schrader", "555-0799")
        d = self.service.check_in_device("C-30", "Tablet", "Samsung", "Galaxy Tab S8", "Won't turn on")

        # Search by brand
        res = self.service.search_repairs("Samsung")
        self.assertEqual(len(res), 1)

        # Search by customer name
        res_name = self.service.search_repairs("Hank")
        self.assertEqual(len(res_name), 1)

        # Report
        rep = self.service.generate_report()
        self.assertEqual(rep["total_repairs_logged"], 1)
        self.assertIn("Received", rep["status_breakdown"])


if __name__ == "__main__":
    unittest.main()
