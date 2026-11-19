"""
Automated unit tests for Vehicle Maintenance Tracking System.
"""

import os
import tempfile
import unittest
from maintenance_service import MaintenanceService


class TestVehicleMaintenance(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = MaintenanceService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_vehicle_registration(self):
        v = self.service.register_vehicle("CAR-100", "Honda", "Civic", 2022, 15000)
        self.assertEqual(v["reg_number"], "CAR-100")
        self.assertEqual(v["current_mileage"], 15000)

        # Duplicate registration
        with self.assertRaises(ValueError):
            self.service.register_vehicle("CAR-100", "Honda", "Civic", 2022)

        # Invalid year
        with self.assertRaises(ValueError):
            self.service.register_vehicle("CAR-200", "Ford", "Model T", 1850)

    def test_mileage_updates(self):
        self.service.register_vehicle("TRK-01", "Ford", "F-150", 2020, 50000)

        updated = self.service.update_mileage("TRK-01", 52000)
        self.assertEqual(updated["current_mileage"], 52000)

        # Decreasing mileage not allowed
        with self.assertRaises(ValueError):
            self.service.update_mileage("TRK-01", 49000)

    def test_maintenance_recording(self):
        self.service.register_vehicle("VAN-01", "Mercedes", "Sprinter", 2021, 30000)

        rec = self.service.record_maintenance(
            reg_number="VAN-01",
            service_type="Oil Change & Filter",
            cost=120.0,
            mileage_at_service=31000,
            service_date_str="2026-10-01",
            next_due_date_str="2027-04-01",
            next_due_mileage=36000,
            provider="QuickLube Auto"
        )
        self.assertEqual(rec["cost"], 120.0)

        # Mileage automatically updated to 31000
        v = self.service.get_vehicle_by_reg("VAN-01")
        self.assertEqual(v["current_mileage"], 31000)
        self.assertEqual(len(v["history"]), 1)

    def test_overdue_maintenance_detection(self):
        self.service.register_vehicle("SEDAN-01", "Toyota", "Camry", 2019, 45000)

        # Service performed in the past with past due date: 2026-09-01
        self.service.record_maintenance(
            reg_number="SEDAN-01",
            service_type="Brake Pad Replacement",
            cost=250.0,
            mileage_at_service=40000,
            service_date_str="2026-03-01",
            next_due_date_str="2026-09-01",
            next_due_mileage=44000
        )
        # Vehicle current mileage is 45000, exceeding 44000 AND date 2026-09-01 is past as of 2026-11-01
        overdue = self.service.get_overdue_maintenance("2026-11-01")
        self.assertEqual(len(overdue), 1)
        self.assertIn("Date overdue", overdue[0]["overdue_reasons"])
        self.assertIn("Mileage exceeded", overdue[0]["overdue_reasons"])

    def test_expense_report(self):
        self.service.register_vehicle("V-1", "Nissan", "Rogue", 2021, 20000)
        self.service.register_vehicle("V-2", "Toyota", "RAV4", 2022, 10000)

        self.service.record_maintenance("V-1", "Oil Change", 80.0, 20000)
        self.service.record_maintenance("V-1", "Tire Rotation", 50.0, 20000)
        self.service.record_maintenance("V-2", "Oil Change", 90.0, 10000)

        rep = self.service.generate_expense_report()
        self.assertEqual(rep["total_vehicles"], 2)
        self.assertEqual(rep["total_services_logged"], 3)
        self.assertEqual(rep["total_spent"], 220.0)


if __name__ == "__main__":
    unittest.main()
