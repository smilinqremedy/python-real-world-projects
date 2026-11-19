"""
Automated Unit and Integration Tests for Electricity and Power Consumption Tracker
Validates prepaid recharges, daily consumption logs, balance calculations,
monthly estimations, generator fuel isolation, and energy report generation.
"""

import os
import unittest
import tempfile
from database import initialize_database
from tracker_service import PowerTrackerService


class TestPowerTracker(unittest.TestCase):

    def setUp(self):
        # Create a temporary file database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        initialize_database(self.db_path)
        self.service = PowerTrackerService(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_record_prepaid_purchase(self):
        """Feature 1 & 4: Record prepaid purchases and compute unit rate."""
        p = self.service.record_prepaid_purchase("2026-11-01", 50.0, 250.0, token_number="1234-5678-9012")
        self.assertEqual(p["amount_paid"], 50.0)
        self.assertEqual(p["units_credited"], 250.0)
        self.assertEqual(p["unit_rate"], 0.20)  # 50 / 250 = 0.20/kWh

    def test_reject_invalid_purchase_amounts(self):
        """Test validation rejects negative or zero amounts and units."""
        with self.assertRaises(ValueError):
            self.service.record_prepaid_purchase("2026-11-01", -20.0, 100.0)
        with self.assertRaises(ValueError):
            self.service.record_prepaid_purchase("2026-11-01", 50.0, 0.0)

    def test_record_daily_consumption_direct_and_meter(self):
        """Feature 2 & 5: Record electricity units consumed directly and via meter reading."""
        # Direct
        c1 = self.service.record_daily_consumption("2026-11-01", units_consumed=12.5, notes="A/C and fridge")
        self.assertEqual(c1["units_consumed"], 12.5)

        # Base meter reading
        self.service.record_daily_consumption("2026-11-02", meter_reading=1000.0)
        # Next day meter reading delta
        c3 = self.service.record_daily_consumption("2026-11-03", meter_reading=1015.0)
        self.assertEqual(c3["units_consumed"], 15.0)  # 1015 - 1000 = 15.0 kWh

    def test_calculate_remaining_units_and_low_alert(self):
        """Feature 3 & 11: Calculate remaining units and trigger low-stock alert."""
        # Recharge 100 kWh
        self.service.record_prepaid_purchase("2026-11-01", 20.0, 100.0)

        # Consume 75 kWh -> 25 kWh left (threshold is 20) -> not low
        self.service.record_daily_consumption("2026-11-01", units_consumed=75.0)
        status1 = self.service.get_remaining_units_status()
        self.assertEqual(status1["remaining_units_kwh"], 25.0)
        self.assertFalse(status1["is_low"])

        # Consume 10 kWh -> 15 kWh left (below 20 threshold) -> is_low = True
        self.service.record_daily_consumption("2026-11-02", units_consumed=10.0)
        status2 = self.service.get_remaining_units_status()
        self.assertEqual(status2["remaining_units_kwh"], 15.0)
        self.assertTrue(status2["is_low"])

    def test_average_daily_consumption(self):
        """Feature 6: Calculate average daily consumption."""
        self.service.record_daily_consumption("2026-11-01", units_consumed=10.0)
        self.service.record_daily_consumption("2026-11-02", units_consumed=14.0)
        self.service.record_daily_consumption("2026-11-03", units_consumed=12.0)

        avg_data = self.service.get_average_daily_consumption()
        self.assertEqual(avg_data["tracked_days"], 3)
        self.assertEqual(avg_data["total_kwh"], 36.0)
        self.assertEqual(avg_data["average_daily_kwh"], 12.0)  # 36 / 3 = 12.0

    def test_estimate_monthly_electricity_expenses(self):
        """Feature 7: Estimate monthly electricity expenses."""
        # Recharge at $0.20/kWh
        self.service.record_prepaid_purchase("2026-11-01", 50.0, 250.0)
        # Average consumption: 10 kWh/day
        self.service.record_daily_consumption("2026-11-01", units_consumed=10.0)

        est = self.service.estimate_monthly_electricity_expenses()
        self.assertEqual(est["average_daily_kwh"], 10.0)
        self.assertEqual(est["projected_monthly_kwh"], 300.0)  # 10 * 30
        self.assertEqual(est["estimated_grid_cost"], 60.0)     # 300 * 0.20

    def test_record_generator_fuel_and_summary(self):
        """Feature 8 & 9: Record and track generator fuel expenses separately."""
        # Buy 20 liters @ $1.50/L with 8 run hours
        g1 = self.service.record_generator_fuel("2026-11-05", liters_bought=20.0, cost_per_liter=1.50, run_hours=8.0)
        self.assertEqual(g1["total_cost"], 30.0)

        # Buy 10 liters @ $1.50/L with 4 run hours
        self.service.record_generator_fuel("2026-11-10", liters_bought=10.0, cost_per_liter=1.50, run_hours=4.0)

        summary = self.service.get_generator_summary()
        self.assertEqual(summary["total_entries"], 2)
        self.assertEqual(summary["total_liters"], 30.0)
        self.assertEqual(summary["total_spend"], 45.0)
        self.assertEqual(summary["total_run_hours"], 12.0)
        self.assertEqual(summary["liters_per_hour"], 2.5)  # 30 / 12 = 2.5 L/hr

    def test_monthly_energy_report(self):
        """Feature 10: Generate comprehensive monthly energy report."""
        month = "2026-11"
        # Grid: $100 spent, 500 kWh bought, 200 kWh consumed over 2 days
        self.service.record_prepaid_purchase("2026-11-01", 100.0, 500.0)
        self.service.record_daily_consumption("2026-11-01", units_consumed=100.0)
        self.service.record_daily_consumption("2026-11-02", units_consumed=100.0)

        # Generator: $50 fuel spent in November
        self.service.record_generator_fuel("2026-11-03", liters_bought=25.0, cost_per_liter=2.00, run_hours=10.0)

        report = self.service.generate_monthly_energy_report(month)
        self.assertEqual(report["month"], month)
        self.assertEqual(report["grid_spend"], 100.0)
        self.assertEqual(report["units_consumed_kwh"], 200.0)
        self.assertEqual(report["days_logged"], 2)
        self.assertEqual(report["avg_daily_kwh"], 100.0)
        self.assertEqual(report["generator_spend"], 50.0)
        self.assertEqual(report["total_energy_expense"], 150.0)  # 100 + 50
        self.assertAlmostEqual(report["grid_share_pct"], 66.7, places=1)
        self.assertAlmostEqual(report["generator_share_pct"], 33.3, places=1)


if __name__ == "__main__":
    unittest.main()
