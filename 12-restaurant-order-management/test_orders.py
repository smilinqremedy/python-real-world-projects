"""
Automated unit tests for Restaurant Order Management System.
"""

import os
import tempfile
import unittest
from order_service import OrderService


class TestRestaurantOrderManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = OrderService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_menu_seeding_and_creation(self):
        menu = self.service.get_menu()
        self.assertGreaterEqual(len(menu), 8)

        item = self.service.add_menu_item("M-CUSTOM", "Spicy Chicken Wings", "Appetizer", 9.99)
        self.assertEqual(item["item_code"], "M-CUSTOM")

        # Duplicate code
        with self.assertRaises(ValueError):
            self.service.add_menu_item("M-CUSTOM", "Another Dish", "Appetizer", 10.0)

    def test_order_creation_and_item_addition(self):
        order = self.service.create_order("John Doe", "Table 5")
        self.assertTrue(order["order_number"].startswith("ORD-"))

        # Add 2 Cheeseburgers ($12.50 each = $25.00)
        updated = self.service.add_meal_to_order(order["order_number"], "M-101", 2)
        self.assertEqual(updated["subtotal"], 25.00)
        # Tax is 5% = $1.25 -> Total $26.25
        self.assertEqual(updated["tax_amount"], 1.25)
        self.assertEqual(updated["total_bill"], 26.25)
        self.assertEqual(len(updated["items"]), 1)

    def test_quantity_change_and_removal(self):
        order = self.service.create_order("Jane", "Table 2")
        ord_num = order["order_number"]

        self.service.add_meal_to_order(ord_num, "M-101", 2)
        self.service.add_meal_to_order(ord_num, "M-107", 1)  # Tea $4.00

        # Change quantity of Tea to 3
        updated = self.service.change_item_quantity(ord_num, "M-107", 3)
        # Subtotal: 2 * 12.50 + 3 * 4.00 = 25.00 + 12.00 = 37.00
        self.assertEqual(updated["subtotal"], 37.00)

        # Remove Tea
        updated = self.service.remove_item_from_order(ord_num, "M-107")
        self.assertEqual(len(updated["items"]), 1)
        self.assertEqual(updated["subtotal"], 25.00)

    def test_discount_application(self):
        order = self.service.create_order("VIP Customer", "Booth 1")
        ord_num = order["order_number"]
        self.service.add_meal_to_order(ord_num, "M-102", 2)  # Pizza 14.00 * 2 = 28.00

        # 10% discount: discount = 2.80, net = 25.20, tax = 5% of 25.20 = 1.26, total = 26.46
        updated = self.service.apply_discount(ord_num, 10.0)
        self.assertEqual(updated["discount_amount"], 2.80)
        self.assertEqual(updated["tax_amount"], 1.26)
        self.assertEqual(updated["total_bill"], 26.46)

        # Invalid discount
        with self.assertRaises(ValueError):
            self.service.apply_discount(ord_num, 150.0)

    def test_payment_and_sales_report(self):
        order = self.service.create_order("Mark", "Table 9")
        ord_num = order["order_number"]
        self.service.add_meal_to_order(ord_num, "M-101", 1)  # 12.50 -> tax 0.63 -> total 13.13

        # Underpayment fails
        with self.assertRaises(ValueError):
            self.service.record_payment(ord_num, 10.00)

        # Correct payment
        receipt = self.service.record_payment(ord_num, 20.00)
        self.assertEqual(receipt["payment_status"], "Paid")
        self.assertEqual(receipt["order_status"], "Completed")
        self.assertEqual(receipt["change"], 6.88)

        # Cannot modify paid order
        with self.assertRaises(ValueError):
            self.service.add_meal_to_order(ord_num, "M-107", 1)

        # Report
        report = self.service.generate_daily_sales_report(receipt["order_date"])
        self.assertEqual(report["total_completed_orders"], 1)
        self.assertEqual(report["total_revenue"], 13.12)
        self.assertEqual(len(report["top_items"]), 1)


if __name__ == "__main__":
    unittest.main()
