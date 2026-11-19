"""
Automated unit tests for School Fee Payment Management System.
"""

import os
import tempfile
import unittest
from fee_service import FeeService


class TestSchoolFees(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = FeeService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_class_definition_and_student_enrollment(self):
        c = self.service.define_class("SS-1A", "Senior Secondary 1A", "2026/2027", 500.0)
        self.assertEqual(c["class_code"], "SS-1A")
        self.assertEqual(c["term_fee"], 500.0)

        # Duplicate class code
        with self.assertRaises(ValueError):
            self.service.define_class("SS-1A", "Duplicate SS1A", "2026/2027", 400.0)

        # Student registration
        s = self.service.register_student("STU-101", "Chidi Anagonye", "SS-1A", "Eleanor", "555-1111")
        self.assertEqual(s["student_reg_no"], "STU-101")

        # Nonexistent class
        with self.assertRaises(ValueError):
            self.service.register_student("STU-102", "Jason Mendoza", "NONEXISTENT", "Tahani", "555-2222")

    def test_payment_and_installment_reconciliation(self):
        self.service.define_class("JS-1", "Junior Secondary 1", "2026/2027", 600.0)
        self.service.register_student("STU-201", "Janet Smith", "JS-1", "Michael", "555-3333")

        # Negative / zero payment rejected
        with self.assertRaises(ValueError):
            self.service.record_fee_payment("STU-201", -50.0, "Term 1")
        with self.assertRaises(ValueError):
            self.service.record_fee_payment("STU-201", 0.0, "Term 1")

        # Installment 1: $250 out of $600
        p1 = self.service.record_fee_payment("STU-201", 250.0, "Term 1", "2026-09-10")
        self.assertEqual(p1["total_paid"], 250.0)
        self.assertEqual(p1["outstanding_balance"], 350.0)
        self.assertEqual(p1["payment_status"], "Partial")
        self.assertTrue(p1["latest_receipt_reference"].startswith("FEE-"))

        # Installment 2: $350 remaining
        p2 = self.service.record_fee_payment("STU-201", 350.0, "Term 1", "2026-10-15")
        self.assertEqual(p2["total_paid"], 600.0)
        self.assertEqual(p2["outstanding_balance"], 0.0)
        self.assertEqual(p2["payment_status"], "Paid")

    def test_unpaid_defaulters_and_history(self):
        self.service.define_class("GR-5", "Grade 5", "2026/2027", 400.0)
        self.service.register_student("STU-301", "Alice Student", "GR-5", "Parent A", "555-4444")
        self.service.register_student("STU-302", "Bob Student", "GR-5", "Parent B", "555-5555")

        # Bob pays partial $150, Alice pays nothing
        self.service.record_fee_payment("STU-302", 150.0, "Term 1")

        unpaid = self.service.get_unpaid_students("Term 1", "GR-5")
        self.assertEqual(len(unpaid), 2)
        # Alice owes 400, Bob owes 250
        self.assertEqual(unpaid[0]["student_reg_no"], "STU-301")
        self.assertEqual(unpaid[0]["outstanding_balance"], 400.0)
        self.assertEqual(unpaid[1]["student_reg_no"], "STU-302")
        self.assertEqual(unpaid[1]["outstanding_balance"], 250.0)

        # History lookup
        hist = self.service.get_student_payment_history("STU-302")
        self.assertEqual(len(hist["payments"]), 1)
        self.assertEqual(hist["lifetime_paid"], 150.0)

    def test_financial_report(self):
        self.service.define_class("PRI-1", "Primary 1", "2026/2027", 300.0)
        self.service.register_student("STU-401", "Student One", "PRI-1", "Parent 1", "555-6666")
        self.service.register_student("STU-402", "Student Two", "PRI-1", "Parent 2", "555-7777")

        self.service.record_fee_payment("STU-401", 300.0, "Term 1")  # fully paid
        self.service.record_fee_payment("STU-402", 100.0, "Term 1")  # partial

        rep = self.service.generate_financial_report("Term 1")
        self.assertEqual(rep["total_enrolled_students"], 2)
        self.assertEqual(rep["total_expected_revenue"], 600.0)
        self.assertEqual(rep["total_collected_revenue"], 400.0)
        self.assertEqual(rep["total_outstanding_debt"], 200.0)
        # 400 / 600 * 100 = 66.7%
        self.assertEqual(rep["overall_collection_rate"], 66.7)


if __name__ == "__main__":
    unittest.main()
