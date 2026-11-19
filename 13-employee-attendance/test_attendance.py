"""
Automated unit tests for Employee Attendance Management System.
"""

import os
import tempfile
import unittest
from attendance_service import AttendanceService


class TestAttendanceManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = AttendanceService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_employee_registration(self):
        emp = self.service.register_employee("EMP-01", "Sarah Connor", "Security", "Officer", "08:30")
        self.assertEqual(emp["emp_code"], "EMP-01")
        self.assertEqual(emp["shift_start_time"], "08:30")

        # Duplicate employee code
        with self.assertRaises(ValueError):
            self.service.register_employee("EMP-01", "Sarah Clone", "Security", "Officer", "09:00")

        # Invalid time format
        with self.assertRaises(ValueError):
            self.service.register_employee("EMP-02", "John", "IT", "Dev", "25:99")

    def test_check_in_ontime_and_late(self):
        self.service.register_employee("EMP-10", "Michael Scott", "Management", "Regional Manager", "09:00")

        # On-time check-in at 08:55
        rec1 = self.service.record_check_in("EMP-10", "08:55", "2026-11-01")
        self.assertFalse(rec1["is_late"])
        self.assertEqual(rec1["minutes_late"], 0)

        # Duplicate check-in on same day should fail
        with self.assertRaises(ValueError):
            self.service.record_check_in("EMP-10", "09:10", "2026-11-01")

        # Late check-in on next day at 09:25 (25 mins late)
        rec2 = self.service.record_check_in("EMP-10", "09:25", "2026-11-02")
        self.assertTrue(rec2["is_late"])
        self.assertEqual(rec2["minutes_late"], 25)

    def test_check_out(self):
        self.service.register_employee("EMP-20", "Dwight Schrute", "Sales", "Lead Sales", "08:00")
        self.service.record_check_in("EMP-20", "07:55", "2026-11-03")

        # Check-out
        out = self.service.record_check_out("EMP-20", "17:05", "2026-11-03")
        self.assertEqual(out["check_out_time"], "17:05:00")

        # Check-out with no check-in fails
        with self.assertRaises(ValueError):
            self.service.record_check_out("EMP-20", "17:00", "2026-11-04")

    def test_absence_and_history(self):
        self.service.register_employee("EMP-30", "Jim Halpert", "Sales", "Sales Rep", "09:00")
        self.service.record_absence("EMP-30", "2026-11-05", "Sick leave")

        history = self.service.get_employee_history("EMP-30")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "Absent")
        self.assertEqual(history[0]["notes"], "Sick leave")

    def test_attendance_report_and_rate(self):
        self.service.register_employee("EMP-40", "Pam Beesly", "Admin", "Receptionist", "09:00")
        self.service.register_employee("EMP-50", "Stanley Hudson", "Sales", "Sales Rep", "09:00")

        # Pam: 2 days present
        self.service.record_check_in("EMP-40", "08:50", "2026-11-01")
        self.service.record_check_in("EMP-40", "08:55", "2026-11-02")

        # Stanley: 1 day present, 1 day absent
        self.service.record_check_in("EMP-50", "09:15", "2026-11-01")  # late
        self.service.record_absence("EMP-50", "2026-11-02", "Personal")

        report = self.service.generate_attendance_report("2026-11-01", "2026-11-02")
        self.assertEqual(report["total_employees"], 2)
        self.assertEqual(report["total_present"], 3)
        self.assertEqual(report["total_absent"], 1)
        self.assertEqual(report["total_late_incidents"], 1)
        # Total days logged: 4, present: 3 => 75.0%
        self.assertEqual(report["overall_attendance_rate"], 75.0)


if __name__ == "__main__":
    unittest.main()
