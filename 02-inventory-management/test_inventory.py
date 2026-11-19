"""
Unit Tests for Small Business Inventory Management System
Validates product creation, updates, purchases, sales deduction, insufficient stock prevention,
valuation calculations, and sales analytics.
"""

import os
import unittest
import tempfile
from inventory_manager import (
    load_data,
    save_data,
    add_product,
    update_product_details,
    record_purchase,
    record_sale,
    get_low_stock_products,
    calculate_inventory_value,
    calculate_sales_metrics,
    generate_next_id,
    find_product_by_id
)


class TestInventoryManager(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for isolated test persistence
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.test_path = self.temp_file.name

        self.sample_data = {
            "products": [
                {
                    "id": 1,
                    "name": "Mechanical Keyboard",
                    "quantity": 10,
                    "cost_price": 40.0,
                    "selling_price": 75.0,
                    "low_stock_threshold": 3
                },
                {
                    "id": 2,
                    "name": "Wireless Mouse",
                    "quantity": 2,
                    "cost_price": 12.0,
                    "selling_price": 25.0,
                    "low_stock_threshold": 5
                }
            ],
            "sales": [],
            "purchases": []
        }

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_save_and_load_persistence(self):
        """Test that data can be saved and retrieved reliably."""
        self.assertTrue(save_data(self.sample_data, self.test_path))
        loaded = load_data(self.test_path)
        self.assertEqual(len(loaded["products"]), 2)
        self.assertEqual(loaded["products"][0]["name"], "Mechanical Keyboard")

    def test_corrupt_file_recovery(self):
        """Corrupt JSON files should be handled without throwing uncaught exceptions."""
        with open(self.test_path, "w") as f:
            f.write("corrupted content {[[")
        loaded = load_data(self.test_path)
        self.assertEqual(loaded, {"products": [], "sales": [], "purchases": []})

    def test_add_product_unique_id(self):
        """Test adding products assigns unique sequential IDs."""
        p3 = add_product(self.sample_data, "Gaming Headset", 15, 30.0, 59.99, 4, self.test_path)
        self.assertEqual(p3["id"], 3)
        self.assertEqual(len(self.sample_data["products"]), 3)
        self.assertEqual(p3["selling_price"], 59.99)

    def test_update_product_details(self):
        """Test updating price, threshold, and product name."""
        success, msg = update_product_details(
            self.sample_data,
            product_id=1,
            new_name="RGB Mechanical Keyboard",
            new_cost=45.0,
            new_selling=85.0,
            new_threshold=4,
            file_path=self.test_path
        )
        self.assertTrue(success)
        prod = find_product_by_id(self.sample_data["products"], 1)
        self.assertEqual(prod["name"], "RGB Mechanical Keyboard")
        self.assertEqual(prod["cost_price"], 45.0)
        self.assertEqual(prod["selling_price"], 85.0)
        self.assertEqual(prod["low_stock_threshold"], 4)

    def test_record_purchase_restock(self):
        """Test restocking increases product quantity and logs a purchase record."""
        success, entry = record_purchase(self.sample_data, product_id=2, quantity=10, unit_cost=11.5, file_path=self.test_path)
        self.assertTrue(success)
        prod = find_product_by_id(self.sample_data["products"], 2)
        self.assertEqual(prod["quantity"], 12)  # 2 + 10
        self.assertEqual(prod["cost_price"], 11.5)
        self.assertEqual(len(self.sample_data["purchases"]), 1)
        self.assertEqual(self.sample_data["purchases"][0]["total_cost"], 115.0)

    def test_record_sale_reduces_stock_and_calculates_profit(self):
        """Test sale reduces stock automatically and computes revenue and gross profit."""
        # Initial stock of product 1 is 10. Cost: 40, Selling: 75
        success, sale = record_sale(self.sample_data, product_id=1, quantity=3, file_path=self.test_path)
        self.assertTrue(success)
        prod = find_product_by_id(self.sample_data["products"], 1)
        self.assertEqual(prod["quantity"], 7)  # 10 - 3
        self.assertEqual(sale["total_revenue"], 225.0)  # 3 * 75
        self.assertEqual(sale["cogs"], 120.0)           # 3 * 40
        self.assertEqual(sale["profit"], 105.0)         # 225 - 120
        self.assertEqual(len(self.sample_data["sales"]), 1)

    def test_prevent_sale_when_stock_insufficient(self):
        """Test that attempting to sell more than available stock is rejected."""
        # Product 2 has quantity = 2
        success, err = record_sale(self.sample_data, product_id=2, quantity=5, file_path=self.test_path)
        self.assertFalse(success)
        self.assertIn("Insufficient stock", err)
        # Quantity should remain untouched
        prod = find_product_by_id(self.sample_data["products"], 2)
        self.assertEqual(prod["quantity"], 2)

    def test_low_stock_detection(self):
        """Test identifying products with quantity <= threshold."""
        # Product 1: qty 10, threshold 3 -> Not low
        # Product 2: qty 2, threshold 5 -> LOW STOCK
        low_items = get_low_stock_products(self.sample_data["products"])
        self.assertEqual(len(low_items), 1)
        self.assertEqual(low_items[0]["id"], 2)

    def test_calculate_inventory_value(self):
        """Test total inventory valuation metrics."""
        # Product 1: 10 * 40 = 400 cost, 10 * 75 = 750 retail
        # Product 2: 2 * 12 = 24 cost, 2 * 25 = 50 retail
        # Total cost: 424.0, Total retail: 800.0, Profit: 376.0
        metrics = calculate_inventory_value(self.sample_data["products"])
        self.assertEqual(metrics["total_items"], 2)
        self.assertEqual(metrics["total_units"], 12)
        self.assertEqual(metrics["total_cost_value"], 424.0)
        self.assertEqual(metrics["total_retail_value"], 800.0)
        self.assertEqual(metrics["potential_profit"], 376.0)

    def test_sales_summary_metrics(self):
        """Test aggregated sales summary calculations."""
        sales = [
            {"quantity": 2, "total_revenue": 50.0, "cogs": 24.0, "profit": 26.0},
            {"quantity": 1, "total_revenue": 75.0, "cogs": 40.0, "profit": 35.0}
        ]
        metrics = calculate_sales_metrics(sales)
        self.assertEqual(metrics["transactions"], 2)
        self.assertEqual(metrics["units_sold"], 3)
        self.assertEqual(metrics["total_revenue"], 125.0)
        self.assertEqual(metrics["total_cogs"], 64.0)
        self.assertEqual(metrics["total_profit"], 61.0)


if __name__ == "__main__":
    unittest.main()
