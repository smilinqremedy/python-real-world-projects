"""
Automated unit tests for Microfinance Loan Management System.
"""

import os
import tempfile
import unittest
from loan_service import LoanService


class TestMicrofinanceLoans(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = LoanService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_borrower_registration_and_loan_creation(self):
        b = self.service.register_borrower("B-01", "Amara Okafor", "555-0101", "amara@example.com", 800.0)
        self.assertEqual(b["borrower_code"], "B-01")

        # Loan for $1,200 at 10% annual interest over 12 months
        # Interest = 1200 * 0.10 * (12/12) = 120.00
        # Total payable = 1320.00, monthly installment = 110.00
        loan = self.service.create_loan_application("B-01", 1200.0, 10.0, 12, "2026-01-01")
        self.assertEqual(loan["total_interest"], 120.0)
        self.assertEqual(loan["total_payable"], 1320.0)
        self.assertEqual(loan["monthly_installment"], 110.0)
        self.assertEqual(loan["status"], "Applied")

        # Nonexistent borrower rejection
        with self.assertRaises(ValueError):
            self.service.create_loan_application("NONEXISTENT", 500.0, 5.0, 6)

    def test_approval_and_schedule(self):
        self.service.register_borrower("B-02", "David Kim", "555-0202")
        loan = self.service.create_loan_application("B-02", 600.0, 12.0, 6, "2026-01-01")
        ref = loan["loan_reference"]

        # Approve loan
        approved = self.service.decide_loan_application(ref, "Approved", "2026-01-01")
        self.assertEqual(approved["status"], "Active")
        self.assertEqual(approved["due_date"], "2026-07-01")

        # Repayment schedule
        sched = self.service.calculate_repayment_schedule(ref)
        self.assertEqual(len(sched), 6)
        self.assertEqual(sched[-1]["remaining_balance_after"], 0.0)

    def test_repayment_and_excess_handling(self):
        self.service.register_borrower("B-03", "Elena Rostova", "555-0303")
        loan = self.service.create_loan_application("B-03", 1000.0, 0.0, 5, "2026-01-01")  # Total payable 1000.0
        ref = loan["loan_reference"]
        self.service.decide_loan_application(ref, "Approved", "2026-01-01")

        # 1. Partial payment: $400
        p1 = self.service.record_repayment(ref, 400.0, "2026-02-01")
        self.assertEqual(p1["amount_repaid"], 400.0)
        self.assertEqual(p1["outstanding_balance"], 600.0)
        self.assertEqual(p1["status"], "Active")

        # 2. Overpayment test: Balance is 600.0, payer pays $750.0
        # Requirement: "Do not allow repayments exceeding the outstanding balance without explicitly recording the excess as a separate transaction."
        p2 = self.service.record_repayment(ref, 750.0, "2026-03-01")
        self.assertEqual(p2["amount_repaid"], 1000.0)
        self.assertEqual(p2["outstanding_balance"], 0.0)
        self.assertEqual(p2["status"], "Repaid")
        self.assertEqual(p2["excess_logged"], 150.0)
        self.assertIsNotNone(p2["excess_reference"])
        self.assertEqual(len(p2["excess_records"]), 1)
        self.assertEqual(p2["excess_records"][0]["excess_amount"], 150.0)

    def test_overdue_detection_and_report(self):
        self.service.register_borrower("B-04", "Farouk Al-Mansoor", "555-0404")
        loan = self.service.create_loan_application("B-04", 500.0, 10.0, 3, "2026-01-01")
        ref = loan["loan_reference"]
        self.service.decide_loan_application(ref, "Approved", "2026-01-01")  # Due 2026-04-01

        # Check overdue as of 2026-05-01
        overdue = self.service.get_overdue_loans("2026-05-01")
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["loan_reference"], ref)
        self.assertEqual(overdue[0]["days_overdue"], 30)

        # Performance report
        rep = self.service.generate_loan_performance_report()
        self.assertEqual(rep["disbursed_loans_count"], 1)
        self.assertEqual(rep["total_principal_disbursed"], 500.0)


if __name__ == "__main__":
    unittest.main()
