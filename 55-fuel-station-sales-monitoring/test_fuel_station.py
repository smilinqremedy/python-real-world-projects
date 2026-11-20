"""
Unit tests for Fuel Station Sales & Tank Monitoring System.
"""
import unittest
import os
from decimal import Decimal
from fuel_service import FuelStationService, to_decimal

TEST_DB = "test_fuel_station.db"


class TestFuelStation(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = FuelStationService(TEST_DB)
        self.service.register_product("PMS", "Petrol", "650.00")
        self.service.register_product("AGO", "Diesel", "1100.00")
        self.service.register_tank("TK-01", "PMS", capacity_litres=40000, initial_volume=10000)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_decimal_precision_no_float_rounding(self):
        # Verify 0.1 + 0.2 == 0.3 without binary floating point inaccuracy
        d1 = to_decimal("0.10")
        d2 = to_decimal("0.20")
        self.assertEqual(d1 + d2, Decimal("0.30"))

    def test_delivery_capacity_boundary(self):
        # Tank capacity is 40,000L with 10,000L currently in tank.
        # Adding 35,000L must raise ValueError (exceeds capacity)
        with self.assertRaises(ValueError):
            self.service.record_delivery("TK-01", "Supplier", 35000.0, "580.00")

        # Valid delivery of 15,000L
        d_ref = self.service.record_delivery("TK-01", "Supplier", 15000.0, "580.00")
        self.assertTrue(d_ref.startswith("DEL-"))

        # Tank current volume should be exactly 25,000L
        tanks = self.service.list_tanks()
        tk1 = next(t for t in tanks if t["tank_code"] == "TK-01")
        self.assertEqual(Decimal(tk1["current_volume_litres"]), Decimal("25000.00"))

    def test_pump_sale_validation_and_revenue(self):
        # Closing meter < Opening meter must fail
        with self.assertRaises(ValueError):
            self.service.record_pump_sale("TK-01", "P-1", opening_meter=5000.0, closing_meter=4000.0)

        # 1,250.5 Litres sold at ₦650.00 = ₦812,825.00
        s_ref = self.service.record_pump_sale("TK-01", "P-1", opening_meter=1000.0, closing_meter=2250.5)
        self.assertTrue(s_ref.startswith("SAL-"))

        # Check revenue calculation with exact Decimal precision
        rep = self.service.generate_daily_report()
        self.assertEqual(rep["total_litres_sold"], Decimal("1250.50"))
        # 1250.5 * 650.00 = 812825.00
        self.assertEqual(rep["total_revenue"], Decimal("812825.00"))

    def test_reconciliation_and_discrepancy_identification(self):
        date_str = "2026-05-15"
        # Opening Dip = 10,000 L
        # Delivery = 5,000 L
        self.service.record_delivery("TK-01", "NNPC", 5000.0, "580.00", delivery_date=date_str)

        # Sales = 3,000 L
        self.service.record_pump_sale("TK-01", "P-1", 1000.0, 4000.0, sale_date=date_str)

        # Expected Closing = 10,000 + 5,000 - 3,000 = 12,000 L
        # Actual Closing Dip = 11,940 L (Shortage of -60 L)
        recon = self.service.reconcile_tank("TK-01", date_str, opening_dip=10000.0, actual_closing_dip=11940.0)

        self.assertEqual(recon["expected_closing"], Decimal("12000.00"))
        self.assertEqual(recon["actual_closing"], Decimal("11940.00"))
        self.assertEqual(recon["discrepancy"], Decimal("-60.00"))
        self.assertIn("Shortage", recon["status"])


if __name__ == "__main__":
    unittest.main()
