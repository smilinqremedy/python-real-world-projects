"""
Automated unit tests for Laundry Service Management System.
"""

import os
import tempfile
import unittest
from laundry_service import LaundryService


class TestLaundryManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = LaundryService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_customer_registration(self):
        cust = self.service.register_customer("C-01", "Emma Watson", "555-1234", "emma@example.com")
        self.assertEqual(cust["customer_code"], "C-01")

        with self.assertRaises(ValueError):
            self.service.register_customer("C-01", "Emma Duplicate", "555-0000")

    def test_order_creation_and_calculation(self):
        self.service.register_customer("C-02", "Robert Downey", "555-4321")

        items = [
            {"item_type": "Shirt", "quantity": 3},    # 3 * 3.50 = 10.50
            {"item_type": "Suit", "quantity": 1},     # 1 * 12.00 = 12.00
            {"item_type": "Trousers", "quantity": 2}  # 2 * 4.00 = 8.00
        ]
        # Total charge = 10.50 + 12.00 + 8.00 = 30.50
        order = self.service.create_order("C-02", items, "2026-11-10")
        self.assertEqual(order["total_items"], 6)
        self.assertEqual(order["total_charge"], 30.50)
        self.assertEqual(order["status"], "Received")
        self.assertEqual(order["payment_status"], "Unpaid")

    def test_payment_and_collection_rules(self):
        self.service.register_customer("C-03", "Bruce Wayne", "555-9999")
        order = self.service.create_order("C-03", [{"item_type": "Suit", "quantity": 2}], "2026-11-10")
        ord_id = order["order_id"]
        self.assertEqual(order["total_charge"], 24.00)

        # Cannot collect when unpaid
        with self.assertRaises(ValueError):
            self.service.update_order_status(ord_id, "Collected")

        # Partial payment: $10.00
        res_partial = self.service.record_payment(ord_id, 10.00, "2026-11-10")
        self.assertEqual(res_partial["amount_paid"], 10.00)
        self.assertEqual(res_partial["payment_status"], "Partial")
        self.assertEqual(res_partial["outstanding_balance"], 14.00)

        # Still cannot collect when partially paid
        with self.assertRaises(ValueError):
            self.service.update_order_status(ord_id, "Collected")

        # Overpayment rejection: trying to pay $20 when balance is $14
        with self.assertRaises(ValueError):
            self.service.record_payment(ord_id, 20.00, "2026-11-10")

        # Full payment: pay remaining $14.00
        res_full = self.service.record_payment(ord_id, 14.00, "2026-11-10")
        self.assertEqual(res_full["payment_status"], "Paid")
        self.assertEqual(res_full["outstanding_balance"], 0.0)

        # Now can transition through Washing -> Ready -> Collected
        self.service.update_order_status(ord_id, "Washing")
        self.service.update_order_status(ord_id, "Ready")
        res_collected = self.service.update_order_status(ord_id, "Collected")
        self.assertEqual(res_collected["status"], "Collected")

    def test_pending_orders_and_daily_revenue(self):
        self.service.register_customer("C-04", "Clark Kent", "555-0011")
        ord1 = self.service.create_order("C-04", [{"item_type": "Shirt", "quantity": 2}], "2026-11-11")  # 7.00
        ord2 = self.service.create_order("C-04", [{"item_type": "Dress", "quantity": 1}], "2026-11-11")  # 8.00

        self.service.record_payment(ord1["order_id"], 7.00, "2026-11-11", "Card")

        # Pending orders should show both
        pending = self.service.get_pending_orders()
        self.assertGreaterEqual(len(pending), 2)

        # Daily revenue report
        rep = self.service.generate_daily_revenue_report("2026-11-11")
        self.assertEqual(rep["total_revenue"], 7.00)
        self.assertEqual(rep["orders_placed_today"], 2)


if __name__ == "__main__":
    unittest.main()
