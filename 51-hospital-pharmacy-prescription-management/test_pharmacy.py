"""
Unit tests for Hospital Pharmacy Prescription Management System.
"""
import unittest
import os
from pharmacy_service import PharmacyService, PrescriptionError, InsufficientStockError

TEST_DB = "test_pharmacy.db"


class TestPharmacyService(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = PharmacyService(TEST_DB)

        # Standard seed data
        self.service.register_doctor("DOC-01", "Dr. Alan Turing", "Neurology", "MDCN-001", "+2348011112222")
        self.service.register_patient("PAT-01", "Ada Lovelace", "1990-12-10", "F", "+2348022223333", "ada@example.com", "Penicillin")
        self.service.add_medicine("MED-01", "Paracetamol", "Tablet", "500mg", stock_quantity=100, unit_price=20.0, reorder_level=20)
        self.service.add_medicine("MED-02", "Ibuprofen", "Tablet", "400mg", stock_quantity=10, unit_price=50.0, reorder_level=5)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ==================== Patient & Doctor Validation ====================

    def test_patient_registration_validation(self):
        # Future DOB
        with self.assertRaises(ValueError):
            self.service.register_patient("PAT-02", "Future Person", "2099-01-01", "M", "+2348033334444")

        # Invalid Email
        with self.assertRaises(ValueError):
            self.service.register_patient("PAT-03", "Bad Mail", "1995-05-05", "M", "+2348033334444", email="invalid-email")

        # Duplicate Patient ID
        with self.assertRaises(ValueError):
            self.service.register_patient("PAT-01", "Duplicate ID", "1990-12-10", "F", "+2348022223333")

    def test_medicine_stock_management(self):
        # Update stock
        new_qty = self.service.update_stock("MED-01", 50)
        self.assertEqual(new_qty, 150)

        # Reduce below zero must fail
        with self.assertRaises(ValueError):
            self.service.update_stock("MED-01", -200)

    # ==================== Prescription Workflow ====================

    def test_prescription_creation_and_multiple_items(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Tension Headache")
        self.assertTrue(rx_ref.startswith("RX-"))

        item1 = self.service.add_prescription_item(rx_ref, "MED-01", 20, "2 tablets twice daily", 5)
        item2 = self.service.add_prescription_item(rx_ref, "MED-02", 5, "1 tablet after meals", 5)
        self.assertGreater(item1, 0)
        self.assertGreater(item2, 0)

        rx = self.service.get_prescription(rx_ref)
        self.assertEqual(len(rx["items"]), 2)
        self.assertEqual(rx["status"], "Pending")

    def test_check_availability(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Joint Pain")
        # MED-02 only has 10 in stock; prescribe 15 to trigger shortage
        self.service.add_prescription_item(rx_ref, "MED-02", 15, "1 tablet daily", 15)

        avail = self.service.check_prescription_availability(rx_ref)
        self.assertFalse(avail["can_dispense"])
        item_status = avail["items"][0]
        self.assertFalse(item_status["is_available"])
        self.assertEqual(item_status["deficit"], 5)

    def test_prevent_dispensing_insufficient_stock(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Severe Fever")
        # MED-02 only has 10 units in stock
        self.service.add_prescription_item(rx_ref, "MED-02", 25, "1 tablet 3 times daily", 8)

        # Must raise InsufficientStockError and leave stock untouched
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.dispense_prescription(rx_ref, "Pharm. Smith")
        self.assertIn("Insufficient stock", str(ctx.exception))

        # Check stock unchanged
        med = self.service.get_medicine("MED-02")
        self.assertEqual(med["stock_quantity"], 10)

    def test_successful_dispensing_and_stock_reduction(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Mild Sprain")
        self.service.add_prescription_item(rx_ref, "MED-01", 10, "1 tab twice daily", 5)
        self.service.add_prescription_item(rx_ref, "MED-02", 4, "1 tab daily", 4)

        result = self.service.dispense_prescription(rx_ref, "Pharm. Ngozi")
        self.assertTrue(result["dispense_ref"].startswith("DSP-"))
        # Cost: (10 * 20.0) + (4 * 50.0) = 200 + 200 = 400.0
        self.assertEqual(result["total_amount"], 400.0)

        # Verify stock decremented: MED-01 (100 -> 90), MED-02 (10 -> 6)
        med1 = self.service.get_medicine("MED-01")
        med2 = self.service.get_medicine("MED-02")
        self.assertEqual(med1["stock_quantity"], 90)
        self.assertEqual(med2["stock_quantity"], 6)

        # Verify prescription status updated
        rx = self.service.get_prescription(rx_ref)
        self.assertEqual(rx["status"], "Dispensed")

    def test_prevent_re_dispensing_and_cancelled_dispensing(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Cough")
        self.service.add_prescription_item(rx_ref, "MED-01", 5, "1 tab daily", 5)
        self.service.dispense_prescription(rx_ref, "Pharm. Ngozi")

        # Second dispense attempt must fail
        with self.assertRaises(PrescriptionError):
            self.service.dispense_prescription(rx_ref, "Pharm. Ngozi")

        # Cancelled prescription cannot be dispensed
        rx2 = self.service.create_prescription("PAT-01", "DOC-01", "Earache")
        self.service.add_prescription_item(rx2, "MED-01", 5, "1 tab daily", 5)
        self.service.cancel_prescription(rx2, "Patient moved away")

        with self.assertRaises(PrescriptionError):
            self.service.dispense_prescription(rx2, "Pharm. Ngozi")

    def test_prescription_history_and_daily_reports(self):
        rx_ref = self.service.create_prescription("PAT-01", "DOC-01", "Dental Pain")
        self.service.add_prescription_item(rx_ref, "MED-01", 8, "1 tab PRN", 4)
        self.service.dispense_prescription(rx_ref, "Pharm. Ngozi")

        # History
        history = self.service.get_patient_prescription_history("PAT-01")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["diagnosis"], "Dental Pain")

        # Report
        report = self.service.generate_daily_dispensing_report()
        self.assertGreaterEqual(report["total_dispenses"], 1)
        self.assertGreaterEqual(report["total_revenue"], 160.0)


if __name__ == "__main__":
    unittest.main()
