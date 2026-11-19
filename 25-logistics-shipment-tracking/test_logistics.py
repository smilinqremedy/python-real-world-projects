"""
Automated unit tests for Logistics and Shipment Tracking System.
"""

import os
import tempfile
import unittest
from logistics_service import LogisticsService


class TestLogisticsTracking(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = LogisticsService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_customer_and_courier_registration(self):
        c = self.service.register_customer("C-01", "Acme Corp", "555-1234", "shipping@acme.com", "100 Industrial Pkwy")
        self.assertEqual(c["customer_code"], "C-01")

        with self.assertRaises(ValueError):
            self.service.register_customer("C-01", "Acme Duplicate", "555-0000", "", "Somewhere")

        courier = self.service.register_courier("CUR-01", "Speedy Delivery", "555-5678", "Van")
        self.assertEqual(courier["courier_code"], "CUR-01")

    def test_freight_calculation_and_shipment_creation(self):
        self.service.register_customer("C-10", "Tech Depot", "555-1111", "", "200 Tech St")

        # Standard: 5.00 + 4kg * 2.00 = 13.00
        charge_std = self.service.calculate_delivery_charge(4.0, "Standard")
        self.assertEqual(charge_std, 13.00)

        # Express: 10.00 + 4kg * 3.50 = 24.00
        charge_exp = self.service.calculate_delivery_charge(4.0, "Express")
        self.assertEqual(charge_exp, 24.00)

        # Create shipment
        ship = self.service.create_shipment(
            sender_code="C-10",
            receiver_name="Target Store",
            receiver_phone="555-2222",
            receiver_address="500 Retail Way",
            destination_city="Seattle",
            parcel_description="Computer Hardware",
            weight_kg=4.0,
            shipping_tier="Express",
            created_date_str="2026-11-19"
        )
        self.assertTrue(ship["tracking_number"].startswith("TRK-"))
        self.assertEqual(ship["delivery_fee"], 24.00)
        self.assertEqual(ship["status"], "Created")
        self.assertEqual(len(ship["milestones"]), 1)

    def test_courier_assignment_and_milestone_progression(self):
        self.service.register_customer("C-20", "Bookstore HQ", "555-3333", "", "12 Library Lane")
        self.service.register_courier("CUR-20", "Leo Transporter", "555-4444", "Motorcycle")

        ship = self.service.create_shipment(
            "C-20", "Reader Dave", "555-5555", "77 Elm St", "Boston", "Books", 2.0, "Standard"
        )
        trk = ship["tracking_number"]

        # Cannot mark as Delivered without courier assigned
        with self.assertRaises(ValueError):
            self.service.update_shipment_status(trk, "Delivered", "Boston Depot")

        # Assign courier
        assigned = self.service.assign_courier(trk, "CUR-20")
        self.assertEqual(assigned["status"], "Assigned")
        self.assertEqual(assigned["courier_code"], "CUR-20")

        # Update to In Transit
        transit = self.service.update_shipment_status(trk, "In Transit", "Midway Sorting Hub", "Package en route")
        self.assertEqual(transit["status"], "In Transit")

        # Update to Out for Delivery
        out_del = self.service.update_shipment_status(trk, "Out for Delivery", "Boston Local Hub", "Loaded on van")
        self.assertEqual(out_del["status"], "Out for Delivery")

        # Update to Delivered
        delivered = self.service.update_shipment_status(trk, "Delivered", "Customer Doorstep", "Signed by Dave")
        self.assertEqual(delivered["status"], "Delivered")
        self.assertIsNotNone(delivered["delivered_at"])

        # Check total milestones
        details = self.service.get_shipment_details(trk)
        # Created -> Assigned -> In Transit -> Out for Delivery -> Delivered = 5 milestones
        self.assertEqual(len(details["milestones"]), 5)

    def test_payment_and_report(self):
        self.service.register_customer("C-30", "Apparel Co", "555-6666", "", "99 Fashion Ave")
        ship = self.service.create_shipment(
            "C-30", "Boutique XYZ", "555-7777", "10 Market St", "Miami", "Apparel Box", 5.0, "Standard"
        )
        trk = ship["tracking_number"]

        # Record payment
        paid_ship = self.service.record_payment(trk)
        self.assertEqual(paid_ship["payment_status"], "Paid")

        # Report
        rep = self.service.generate_logistics_report()
        self.assertEqual(rep["total_shipments"], 1)
        self.assertEqual(rep["total_weight_handled_kg"], 5.0)
        self.assertEqual(rep["total_freight_collected"], paid_ship["delivery_fee"])


if __name__ == "__main__":
    unittest.main()
