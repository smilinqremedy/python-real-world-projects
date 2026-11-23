"""
Unit tests for Supplier Purchase Order Management System.
"""
import unittest
import os
import tempfile
from po_service import POService, POWorkflowError


class TestPOService(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.service = POService(self.db_path)

        # Seed supplier & product
        self.service.register_supplier(
            "SUP-001", "Dangote Cement Plc", "Aliko", "sales@dangote.com", "+2348011223344", "Lagos"
        )
        self.service.add_product("CEM-50KG", "Portland Cement 50kg", 7500.0, initial_stock=10, reorder_level=20)
        self.service.add_product("IRON-12MM", "High-Yield Iron Rod 12mm", 12000.0, initial_stock=50, reorder_level=15)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_supplier_and_product_registration(self):
        suppliers = self.service.list_suppliers()
        self.assertEqual(len(suppliers), 1)
        self.assertEqual(suppliers[0]["supplier_code"], "SUP-001")

        products = self.service.list_products()
        self.assertEqual(len(products), 2)

        # Duplicate checks
        with self.assertRaises(ValueError):
            self.service.register_supplier("SUP-001", "Duplicate Sup", "John", "j@s.com", "080")
        with self.assertRaises(ValueError):
            self.service.add_product("CEM-50KG", "Another Cement", 5000.0)

    def test_po_creation_and_item_addition(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=100, unit_cost=7500.0)
        po = self.service.get_po_details(po_num)
        self.assertEqual(po["status"], "Draft")
        self.assertEqual(po["total_amount"], 750000.0)
        self.assertEqual(len(po["items"]), 1)

    def test_cannot_add_item_to_approved_po(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=20)
        self.service.approve_purchase_order(po_num)

        with self.assertRaises(POWorkflowError):
            self.service.add_po_item(po_num, "IRON-12MM", quantity=10)

    def test_cannot_approve_empty_po(self):
        po_num = self.service.create_purchase_order("SUP-001")
        with self.assertRaises(POWorkflowError):
            self.service.approve_purchase_order(po_num)

    def test_delivery_reception_updates_inventory_and_status(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=50, unit_cost=7500.0)
        self.service.approve_purchase_order(po_num)

        # Initial stock for CEM-50KG was 10.
        # Partial delivery of 20
        res1 = self.service.receive_delivery(po_num, "CEM-50KG", quantity_delivered=20, received_by="Audu")
        self.assertEqual(res1["po_status"], "Partially Delivered")
        self.assertEqual(res1["updated_warehouse_stock"], 30)

        # Second delivery of remaining 30 -> PO should become Completed
        res2 = self.service.receive_delivery(po_num, "CEM-50KG", quantity_delivered=30, received_by="Audu")
        self.assertEqual(res2["po_status"], "Completed")
        self.assertEqual(res2["updated_warehouse_stock"], 60)

        # Verify delivery history
        po = self.service.get_po_details(po_num)
        self.assertEqual(len(po["deliveries"]), 2)

    def test_overdelivery_rejected(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=50)
        self.service.approve_purchase_order(po_num)

        with self.assertRaises(POWorkflowError) as ctx:
            self.service.receive_delivery(po_num, "CEM-50KG", quantity_delivered=60, received_by="Audu")
        self.assertIn("Over-delivery rejected", str(ctx.exception))

    def test_delivery_against_cancelled_po_rejected(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=10)
        self.service.approve_purchase_order(po_num)
        self.service.cancel_purchase_order(po_num, reason="Supplier out of stock")

        with self.assertRaises(POWorkflowError):
            self.service.receive_delivery(po_num, "CEM-50KG", quantity_delivered=10, received_by="Audu")

    def test_supplier_balance_and_payments(self):
        po_num = self.service.create_purchase_order("SUP-001")
        self.service.add_po_item(po_num, "CEM-50KG", quantity=10, unit_cost=7000.0)  # total 70,000
        self.service.approve_purchase_order(po_num)

        statement1 = self.service.get_supplier_statement("SUP-001")
        self.assertEqual(statement1["total_orders_value"], 70000.0)
        self.assertEqual(statement1["outstanding_balance"], 70000.0)

        # Pay 30,000
        self.service.record_payment("SUP-001", amount=30000.0, payment_method="Bank Transfer", po_number=po_num)
        statement2 = self.service.get_supplier_statement("SUP-001")
        self.assertEqual(statement2["total_paid"], 30000.0)
        self.assertEqual(statement2["outstanding_balance"], 40000.0)

    def test_low_stock_detection(self):
        # CEM-50KG has stock 10, reorder level 20 -> should trigger
        # IRON-12MM has stock 50, reorder level 15 -> should not trigger
        low_stock = self.service.get_low_stock_products()
        self.assertEqual(len(low_stock), 1)
        self.assertEqual(low_stock[0]["sku"], "CEM-50KG")


if __name__ == "__main__":
    unittest.main()
