"""
Automated unit tests for Water Delivery Management System.
"""

import os
import tempfile
import unittest
from delivery_service import DeliveryService


class TestWaterDelivery(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = DeliveryService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_customer_and_driver_registration(self):
        cust = self.service.register_customer("C-01", "Alice Springs", "555-1111", "12 Water St")
        self.assertEqual(cust["customer_code"], "C-01")

        # Missing address
        with self.assertRaises(ValueError):
            self.service.register_customer("C-02", "No Address", "555-2222", "")

        driver = self.service.register_driver("D-01", "Bob Driver", "555-3333", "TRK-99")
        self.assertEqual(driver["driver_code"], "D-01")

    def test_order_creation_pricing(self):
        self.service.register_customer("C-10", "Hotel Grand", "555-4444", "88 Ocean Ave")

        # Small order: 4x 20L Jug ($4.50 * 4 = $18.00) + $3.00 delivery fee = $21.00
        ord1 = self.service.create_order("C-10", "20L Jug", 4, order_date_str="2026-11-05")
        self.assertEqual(ord1["delivery_fee"], 3.00)
        self.assertEqual(ord1["total_charge"], 21.00)

        # Bulk order (>= 10): 10x 20L Jug ($4.50 * 10 = $45.00) with $0.00 delivery fee = $45.00
        ord2 = self.service.create_order("C-10", "20L Jug", 10, order_date_str="2026-11-05")
        self.assertEqual(ord2["delivery_fee"], 0.00)
        self.assertEqual(ord2["total_charge"], 45.00)

    def test_driver_assignment_and_dispatch(self):
        self.service.register_customer("C-20", "Gym Fit", "555-5555", "10 Iron Rd")
        self.service.register_driver("D-20", "Dan Wheeler", "555-6666", "VAN-12")

        order = self.service.create_order("C-20", "10L Dispenser", 2)
        ord_num = order["order_number"]

        # Cannot mark as Delivered without driver
        with self.assertRaises(ValueError):
            self.service.update_delivery_status(ord_num, "Delivered")

        # Assign driver
        assigned = self.service.assign_driver(ord_num, "D-20")
        self.assertEqual(assigned["status"], "Assigned")
        self.assertEqual(assigned["driver_code"], "D-20")

        # Out for delivery
        dispatched = self.service.update_delivery_status(ord_num, "Out for Delivery")
        self.assertEqual(dispatched["status"], "Out for Delivery")

        # Delivered
        delivered = self.service.update_delivery_status(ord_num, "Delivered")
        self.assertEqual(delivered["status"], "Delivered")

    def test_payment_and_daily_sales_report(self):
        self.service.register_customer("C-30", "Cafe Fresh", "555-7777", "4 Bean St")
        self.service.register_driver("D-30", "Sam Route", "555-8888", "WTR-01")

        ord1 = self.service.create_order("C-30", "5L Bottle Pack", 5, order_date_str="2026-11-12")
        self.service.assign_driver(ord1["order_number"], "D-30")
        self.service.update_delivery_status(ord1["order_number"], "Delivered")

        # Unpaid initially
        rep_unpaid = self.service.generate_daily_sales_report("2026-11-12")
        self.assertEqual(rep_unpaid["paid_orders_count"], 0)

        # Record payment
        paid = self.service.record_payment(ord1["order_number"], "Card")
        self.assertEqual(paid["payment_status"], "Paid")

        # Report after payment
        rep_paid = self.service.generate_daily_sales_report("2026-11-12")
        self.assertEqual(rep_paid["paid_orders_count"], 1)
        self.assertEqual(rep_paid["total_revenue"], paid["total_charge"])
        self.assertEqual(len(rep_paid["driver_deliveries"]), 1)


if __name__ == "__main__":
    unittest.main()
