"""
Unit tests for Customer Subscription & Renewal Management System.
"""
import unittest
import os
import tempfile
from datetime import date, timedelta
from database import init_db
from subscription_service import SubscriptionService, InvalidRenewalError


class TestSubscriptionService(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.service = SubscriptionService(self.db_path)

        # Seed initial plans
        self.starter_id = self.service.create_plan("STARTER-M", "Starter Monthly", "Monthly", 5000.0)
        self.pro_id = self.service.create_plan("PRO-Y", "Pro Annual", "Yearly", 60000.0)

        # Seed customer
        self.cust_id = self.service.register_customer(
            "CUST-001", "Amara Okonkwo", "amara@example.com", "+2348011223344", "Apex Logistics"
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_customer_registration_duplicate_prevention(self):
        with self.assertRaises(ValueError):
            self.service.register_customer("CUST-001", "Duplicate Amara", "amara2@example.com", "080")
        with self.assertRaises(ValueError):
            self.service.register_customer("CUST-002", "Other Amara", "amara@example.com", "080")

    def test_plan_creation_validation(self):
        with self.assertRaises(ValueError):
            self.service.create_plan("BAD-CYCLE", "Invalid Plan", "BiWeekly", 1000.0)
        with self.assertRaises(ValueError):
            self.service.create_plan("ZERO-PRICE", "Free Plan", "Monthly", 0)

    def test_create_subscription_and_expiry_calculation(self):
        start = date(2026, 1, 1)
        sub_ref = self.service.create_subscription(
            "CUST-001", "STARTER-M", start_date_str=start.strftime("%Y-%m-%d")
        )
        sub = self.service.get_subscription_details(sub_ref)
        self.assertEqual(sub["status"], "Active")
        # Monthly is +30 days
        self.assertEqual(sub["expiry_date"], (start + timedelta(days=30)).strftime("%Y-%m-%d"))
        self.assertEqual(len(sub["payments"]), 1)
        self.assertEqual(sub["payments"][0]["amount"], 5000.0)

    def test_valid_renewal_extension(self):
        start = date(2026, 1, 1)
        sub_ref = self.service.create_subscription(
            "CUST-001", "STARTER-M", start_date_str=start.strftime("%Y-%m-%d")
        )
        initial_sub = self.service.get_subscription_details(sub_ref)
        old_expiry = initial_sub["expiry_date"]

        renewal_result = self.service.renew_subscription(sub_ref, amount_paid=5000.0)
        self.assertEqual(renewal_result["status"], "Active")

        updated_sub = self.service.get_subscription_details(sub_ref)
        self.assertNotEqual(updated_sub["expiry_date"], old_expiry)
        self.assertEqual(len(updated_sub["renewals"]), 1)
        self.assertEqual(len(updated_sub["payments"]), 2)

    def test_invalid_renewal_on_cancelled_subscription(self):
        sub_ref = self.service.create_subscription("CUST-001", "STARTER-M")
        self.service.cancel_subscription(sub_ref, reason="Client switched provider")

        with self.assertRaises(InvalidRenewalError) as ctx:
            self.service.renew_subscription(sub_ref, amount_paid=5000.0)
        self.assertIn("The subscription is Cancelled", str(ctx.exception))

    def test_underpayment_renewal_rejected(self):
        sub_ref = self.service.create_subscription("CUST-001", "STARTER-M")
        with self.assertRaises(InvalidRenewalError) as ctx:
            self.service.renew_subscription(sub_ref, amount_paid=2000.0)
        self.assertIn("Underpayment rejected", str(ctx.exception))

    def test_check_and_update_expirations_grace_and_suspended(self):
        # Sub 1: Expired 3 days ago (Grace Period)
        sub1_ref = self.service.create_subscription(
            "CUST-001", "STARTER-M", start_date_str="2026-01-01"
        )
        # Sub 2: Expired 20 days ago (Suspended)
        cust2 = self.service.register_customer("CUST-002", "Bayo", "bayo@example.com", "080")
        sub2_ref = self.service.create_subscription(
            "CUST-002", "STARTER-M", start_date_str="2025-11-01"
        )

        ref_date = date(2026, 2, 3)  # sub1 expired Jan 31 -> 3 days overdue (Grace Period). sub2 expired Dec 1 -> >7 days overdue (Suspended).
        res = self.service.check_and_update_expirations(reference_date=ref_date)
        self.assertGreaterEqual(res["newly_suspended_count"], 1)
        self.assertGreaterEqual(res["newly_grace_period_count"], 1)

        sub1 = self.service.get_subscription_details(sub1_ref)
        sub2 = self.service.get_subscription_details(sub2_ref)
        self.assertEqual(sub1["status"], "Grace Period")
        self.assertEqual(sub2["status"], "Suspended")

    def test_get_expiring_soon(self):
        sub_ref = self.service.create_subscription(
            "CUST-001", "STARTER-M", start_date_str="2026-05-01"
        )
        # Expiry is 2026-05-31
        expiring = self.service.get_expiring_soon(days_threshold=7, reference_date=date(2026, 5, 25))
        self.assertEqual(len(expiring), 1)
        self.assertEqual(expiring[0]["subscription_ref"], sub_ref)

    def test_revenue_report_metrics(self):
        # 1 starter monthly: 5,000 / month
        self.service.create_subscription("CUST-001", "STARTER-M")
        # 1 pro yearly: 60,000 / year -> MRR 5,000 / month
        cust2 = self.service.register_customer("CUST-003", "Chidi", "chidi@example.com", "080333")
        self.service.create_subscription("CUST-003", "PRO-Y")

        report = self.service.generate_revenue_report()
        self.assertEqual(report["active_subscriptions"], 2)
        # Total MRR = 5,000 + 5,000 = 10,000
        self.assertEqual(report["mrr"], 10000.0)
        self.assertEqual(report["arr"], 120000.0)
        self.assertEqual(report["total_payments_collected"], 65000.0)


if __name__ == "__main__":
    unittest.main()
