"""
Automated unit tests for Donation and Charity Management System.
"""

import os
import tempfile
import unittest
from charity_service import CharityService


class TestCharityManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = CharityService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_donor_and_campaign_creation(self):
        d = self.service.register_donor("D-01", "Bill Gates", "bill@gatesfoundation.org", "555-1111", "Foundation")
        self.assertEqual(d["donor_code"], "D-01")
        self.assertEqual(d["donor_type"], "Foundation")

        # Duplicate donor code
        with self.assertRaises(ValueError):
            self.service.register_donor("D-01", "Duplicate Bill", "bill2@gates.org", "555-2222")

        c = self.service.create_campaign("CMP-EDU", "Scholarships 2026", "Fund university education", 50000.0, "2026-01-01", "2026-12-31")
        self.assertEqual(c["campaign_code"], "CMP-EDU")
        self.assertEqual(c["target_amount"], 50000.0)

    def test_donation_recording_and_balances(self):
        self.service.register_donor("D-10", "MacKenzie Scott", "mackenzie@giving.org", "555-3333")
        self.service.create_campaign("CMP-FOOD", "Food Bank Relief", "Emergency meal packs", 20000.0, "2026-01-01", "2026-12-31")

        don = self.service.record_donation("D-10", "CMP-FOOD", 5000.0, "Bank Transfer", "2026-11-01")
        self.assertTrue(don["receipt_reference"].startswith("DON-"))
        self.assertEqual(don["amount"], 5000.0)

        # Check balance
        bal = self.service.get_campaign_balance("CMP-FOOD")
        self.assertEqual(bal["total_raised"], 5000.0)
        self.assertEqual(bal["total_disbursed"], 0.0)
        self.assertEqual(bal["available_balance"], 5000.0)
        self.assertEqual(bal["progress_percentage"], 25.0)

    def test_disbursement_rules_and_overdraft_prevention(self):
        self.service.register_donor("D-20", "Philanthropist X", "x@donor.org", "555-4444")
        self.service.create_campaign("CMP-WATER", "Clean Water Wells", "Digging village wells", 10000.0, "2026-01-01", "2026-12-31")

        self.service.record_donation("D-20", "CMP-WATER", 3000.0)

        # Attempting to disburse $4,000 when only $3,000 is available must be rejected
        with self.assertRaises(ValueError) as ctx:
            self.service.record_disbursement("CMP-WATER", "Water Drill Co", "Well equipment", 4000.0)
        self.assertIn("exceeds available campaign balance", str(ctx.exception))

        # Valid disbursement of $1,800
        disb = self.service.record_disbursement("CMP-WATER", "Water Drill Co", "Phase 1 Well", 1800.0, "2026-11-05")
        self.assertTrue(disb["disbursement_reference"].startswith("DIS-"))
        self.assertEqual(disb["remaining_balance"], 1200.0)

        # Verify updated balance
        bal = self.service.get_campaign_balance("CMP-WATER")
        self.assertEqual(bal["total_raised"], 3000.0)
        self.assertEqual(bal["total_disbursed"], 1800.0)
        self.assertEqual(bal["available_balance"], 1200.0)

    def test_financial_report(self):
        self.service.register_donor("D-30", "Alice", "alice@donor.com", "555-5555")
        self.service.register_donor("D-31", "Bob", "bob@donor.com", "555-6666")
        self.service.create_campaign("CMP-MED", "Medical Clinic", "Free medicines", 15000.0, "2026-01-01", "2026-12-31")

        self.service.record_donation("D-30", "CMP-MED", 4000.0)
        self.service.record_donation("D-31", "CMP-MED", 1000.0)
        self.service.record_disbursement("CMP-MED", "City Pharmacy", "Antibiotics supply", 2000.0)

        rep = self.service.generate_financial_report()
        self.assertEqual(rep["total_donations_count"], 2)
        self.assertEqual(rep["total_funds_raised"], 5000.0)
        self.assertEqual(rep["total_funds_distributed"], 2000.0)
        self.assertEqual(rep["net_treasury_balance"], 3000.0)
        self.assertEqual(len(rep["top_donors"]), 2)
        # Alice is top donor with $4000
        self.assertEqual(rep["top_donors"][0]["donor_name"], "Alice")


if __name__ == "__main__":
    unittest.main()
