"""
Automated unit tests for Internet Cafe Management System.
"""

import os
import tempfile
import unittest
from cafe_service import CafeService


class TestInternetCafe(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = CafeService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_computer_registration_and_status(self):
        c = self.service.register_computer("PC-01", "192.168.1.101", "Core i5, 16GB RAM", 3.00)
        self.assertEqual(c["computer_code"], "PC-01")
        self.assertEqual(c["status"], "Available")

        # Duplicate rejection
        with self.assertRaises(ValueError):
            self.service.register_computer("PC-01", "192.168.1.102", "Ryzen 5", 3.50)

    def test_simultaneous_session_prevention(self):
        self.service.register_computer("PC-02", "192.168.1.102", "Core i7", 4.00)

        # Start session 1
        s1 = self.service.start_session("PC-02", "Gamer One", "2026-11-18 14:00:00")
        self.assertEqual(s1["status"], "Active")

        # Verify PC is now 'In Use'
        comp = self.service.list_computers()[0]
        self.assertEqual(comp["status"], "In Use")

        # Attempt to start session 2 on same PC must be REJECTED!
        with self.assertRaises(ValueError) as ctx:
            self.service.start_session("PC-02", "Gamer Two", "2026-11-18 14:15:00")
        self.assertIn("unavailable", str(ctx.exception).lower())

    def test_session_duration_and_midnight_crossing(self):
        self.service.register_computer("PC-03", "192.168.1.103", "Core i9, RTX 4080", 6.00)

        # Session starts at 23:30:00 on Day 1 and ends at 01:30:00 on Day 2 (120 minutes = 2.0 hours)
        s = self.service.start_session("PC-03", "Night Owl", "2026-11-18 23:30:00")
        s_id = s["session_id"]

        ended = self.service.end_session(s_id, "2026-11-19 01:30:00")
        self.assertEqual(ended["duration_minutes"], 120)
        # 120 mins = 2 hours @ $6.00/hr = $12.00
        self.assertEqual(ended["total_bill"], 12.00)
        self.assertEqual(ended["status"], "Completed")

        # PC-03 should now be Available again
        comp = [c for c in self.service.list_computers() if c["computer_code"] == "PC-03"][0]
        self.assertEqual(comp["status"], "Available")

    def test_payment_and_daily_report(self):
        self.service.register_computer("PC-04", "192.168.1.104", "Core i5", 4.00)
        s = self.service.start_session("PC-04", "Sarah", "2026-11-19 10:00:00")
        s_id = s["session_id"]

        # 30 mins session = 0.5 hours @ $4.00/hr = $2.00
        self.service.end_session(s_id, "2026-11-19 10:30:00")

        # Underpayment fails
        with self.assertRaises(ValueError):
            self.service.record_payment(s_id, 1.00)

        # Correct payment
        p = self.service.record_payment(s_id, 5.00)
        self.assertEqual(p["payment_status"], "Paid")
        self.assertEqual(p["change_returned"], 3.00)

        # Daily report
        rep = self.service.generate_daily_revenue_report("2026-11-19")
        self.assertEqual(rep["completed_sessions"], 1)
        self.assertEqual(rep["total_usage_minutes"], 30)
        self.assertEqual(rep["total_revenue_collected"], 2.00)


if __name__ == "__main__":
    unittest.main()
