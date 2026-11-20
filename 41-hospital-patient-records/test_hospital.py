"""
Unit tests for Hospital Patient Records Management System.
"""
import unittest
import os
from datetime import datetime, timedelta
from hospital_service import HospitalService
from security import AccessDeniedError, mask_phone, mask_email, sanitize_for_audit

TEST_DB = "test_hospital.db"


class TestHospitalPatientRecords(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.service = HospitalService(TEST_DB)

        # Bootstrap admin user
        self.service.register_user(
            None, "ADM-01", "superadmin", "AdminSecret123!", "Hospital Administrator",
            "admin@hospital.org", "admin", "Admin"
        )
        self.admin = self.service.authenticate_user("superadmin", "AdminSecret123!")

        # Create doctor, nurse, receptionist, and billing staff
        self.service.register_user(
            self.admin, "DOC-01", "dr.smith", "DoctorSecret123!", "Dr. John Smith",
            "smith@hospital.org", "doctor", "Cardiology"
        )
        self.doctor = self.service.authenticate_user("dr.smith", "DoctorSecret123!")

        self.service.register_user(
            self.admin, "NUR-01", "nurse.mary", "NurseSecret123!", "Nurse Mary Johnson",
            "mary@hospital.org", "nurse", "General"
        )
        self.nurse = self.service.authenticate_user("nurse.mary", "NurseSecret123!")

        self.service.register_user(
            self.admin, "REC-01", "rec.jane", "RecepSecret123!", "Jane Doe",
            "jane@hospital.org", "receptionist", "Front Desk"
        )
        self.receptionist = self.service.authenticate_user("rec.jane", "RecepSecret123!")

        self.service.register_user(
            self.admin, "BIL-01", "bill.bob", "BillingSecret123!", "Bob Miller",
            "bob@hospital.org", "billing", "Finance"
        )
        self.billing = self.service.authenticate_user("bill.bob", "BillingSecret123!")

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    # ==================== Authentication & Security Tests ====================

    def test_authentication_success_and_failure(self):
        # Valid login
        user = self.service.authenticate_user("dr.smith", "DoctorSecret123!")
        self.assertEqual(user["username"], "dr.smith")
        self.assertEqual(user["role"], "doctor")

        # Wrong password
        with self.assertRaises(ValueError):
            self.service.authenticate_user("dr.smith", "WrongPassword!")

        # Nonexistent user
        with self.assertRaises(ValueError):
            self.service.authenticate_user("ghost_user", "AnyPassword123!")

    def test_rbac_user_management(self):
        # Receptionist attempting to create user must be denied
        with self.assertRaises(AccessDeniedError):
            self.service.register_user(
                self.receptionist, "USR-99", "newuser", "Password123!", "Test User",
                "test@hospital.org", "doctor", "General"
            )

    # ==================== Patient Registration & Validation ====================

    def test_patient_registration_success_and_id_generation(self):
        pid = self.service.register_patient(
            self.receptionist, "David", "Okonkwo", "1990-05-15", "M", "O+",
            "+2348012345678", "david@example.com", "12 Broad Street, Lagos",
            "Mary Okonkwo", "+2348087654321", "None", "None"
        )
        self.assertTrue(pid.startswith("PAT-"))

        # Fetch and verify
        patient = self.service.get_patient(self.receptionist, pid)
        self.assertEqual(patient["first_name"], "David")
        self.assertEqual(patient["last_name"], "Okonkwo")
        self.assertEqual(patient["blood_group"], "O+")

    def test_patient_registration_validation_errors(self):
        # Future date of birth
        future_dob = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        with self.assertRaises(ValueError):
            self.service.register_patient(
                self.receptionist, "Baby", "Future", future_dob, "F", "A+",
                "+2348011112222"
            )

        # Invalid phone format
        with self.assertRaises(ValueError):
            self.service.register_patient(
                self.receptionist, "Sam", "Fisher", "1988-01-01", "M", "B+",
                "not-a-phone"
            )

        # Invalid blood group
        with self.assertRaises(ValueError):
            self.service.register_patient(
                self.receptionist, "Sam", "Fisher", "1988-01-01", "M", "Z+",
                "+2348011112222"
            )

        # Short name
        with self.assertRaises(ValueError):
            self.service.register_patient(
                self.receptionist, "S", "Fisher", "1988-01-01", "M", "A+",
                "+2348011112222"
            )

    def test_prevent_duplicate_patient_registration(self):
        self.service.register_patient(
            self.receptionist, "Kemi", "Adebayo", "1995-10-20", "F", "AB+",
            "+2348099887766"
        )
        # Attempt identical registration
        with self.assertRaises(ValueError) as ctx:
            self.service.register_patient(
                self.receptionist, "Kemi", "Adebayo", "1995-10-20", "F", "AB+",
                "+2348099887766"
            )
        self.assertIn("Duplicate patient record detected", str(ctx.exception))

    def test_patient_search(self):
        p1 = self.service.register_patient(
            self.receptionist, "Nnamdi", "Azikiwe", "1980-11-16", "M", "A+",
            "+2348011110001"
        )
        p2 = self.service.register_patient(
            self.receptionist, "Funmilayo", "Kuti", "1982-10-25", "F", "O-",
            "+2348022220002"
        )

        # Search by name
        res_name = self.service.search_patients(self.receptionist, "Funmilayo")
        self.assertEqual(len(res_name), 1)
        self.assertEqual(res_name[0]["first_name"], "Funmilayo")

        # Search by ID
        res_id = self.service.search_patients(self.receptionist, p1)
        self.assertEqual(len(res_id), 1)
        self.assertEqual(res_id[0]["last_name"], "Azikiwe")

    # ==================== Appointment Scheduling & History ====================

    def test_appointment_scheduling_and_conflict_prevention(self):
        pid = self.service.register_patient(
            self.receptionist, "Tari", "Briggs", "1991-03-12", "F", "B-",
            "+2348033334444"
        )

        apt_ref = self.service.register_appointment(
            self.receptionist, pid, "DOC-01", "Cardiology",
            "2026-12-01", "10:00", "Annual heart screening"
        )
        self.assertTrue(apt_ref.startswith("APT-"))

        # Conflicting appointment for same doctor at same time
        with self.assertRaises(ValueError) as ctx:
            self.service.register_appointment(
                self.receptionist, pid, "DOC-01", "Cardiology",
                "2026-12-01", "10:00", "Second booking attempt"
            )
        self.assertIn("already has an active appointment", str(ctx.exception))

        # Status transition
        self.service.update_appointment_status(self.receptionist, apt_ref, "In-Progress")
        history = self.service.get_appointment_history(self.receptionist, pid)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["status"], "In-Progress")

    # ==================== Clinical Notes & Vital Signs ====================

    def test_vital_signs_and_bmi_calculation(self):
        pid = self.service.register_patient(
            self.receptionist, "Musa", "YarAdua", "1975-08-01", "M", "O+",
            "+2348055556666"
        )
        vst_ref = self.service.record_visit(
            self.receptionist, pid, "Outpatient", "DOC-01", "Routine checkup"
        )

        # Nurse records vitals
        self.service.record_vital_signs(
            self.nurse, vst_ref,
            systolic_bp=120, diastolic_bp=80, heart_rate=72,
            temperature_c=36.7, respiratory_rate=16, spo2_percent=99.0,
            weight_kg=70.0, height_cm=175.0, notes="All vitals normal"
        )

        patient = self.service.get_patient(self.doctor, pid)
        self.assertEqual(len(patient["vital_signs"]), 1)
        # BMI = 70 / (1.75^2) = 22.86
        self.assertAlmostEqual(patient["vital_signs"][0]["bmi"], 22.86, places=2)

    def test_clinical_notes_authorization_and_safeguards(self):
        pid = self.service.register_patient(
            self.receptionist, "Grace", "Alele", "1983-02-14", "F", "A+",
            "+2348077778888"
        )
        vst_ref = self.service.record_visit(
            self.receptionist, pid, "Outpatient", "DOC-01", "Persistent headache"
        )

        # Receptionist CANNOT create clinical notes
        with self.assertRaises(AccessDeniedError):
            self.service.record_clinical_note(
                self.receptionist, vst_ref, "Consultation",
                "Headache", "Normal reflexes", "Tension headache", "Rest and hydration"
            )

        # Doctor CAN record clinical notes
        note_id = self.service.record_clinical_note(
            self.doctor, vst_ref, "Consultation",
            "Episodic frontal headache exacerbated by fatigue",
            "Pupils equal and reactive, cranial nerves intact",
            "Tension-type cephalalgia",
            "Adequate sleep hygiene, stress mitigation, fluid intake review"
        )
        self.assertGreater(note_id, 0)

        # Receptionist looking at chart should not receive clinical notes
        rec_view = self.service.get_patient(self.receptionist, pid)
        self.assertEqual(len(rec_view["clinical_notes"]), 0)

        # Doctor looking at chart receives clinical notes
        doc_view = self.service.get_patient(self.doctor, pid)
        self.assertEqual(len(doc_view["clinical_notes"]), 1)

    # ==================== Billing & Administrative Reports ====================

    def test_billing_invoice_and_payment(self):
        pid = self.service.register_patient(
            self.receptionist, "Ali", "Modu", "1989-06-18", "M", "AB-",
            "+2348044445555"
        )
        inv_ref = self.service.create_billing_invoice(
            self.billing, pid, "Comprehensive Clinical Consultation", 15000.0
        )
        self.assertTrue(inv_ref.startswith("INV-"))

        # Make partial payment
        res1 = self.service.record_payment(self.billing, inv_ref, 5000.0)
        self.assertEqual(res1["status"], "Partial")
        self.assertEqual(res1["amount_paid"], 5000.0)

        # Complete payment
        res2 = self.service.record_payment(self.billing, inv_ref, 10000.0)
        self.assertEqual(res2["status"], "Paid")
        self.assertEqual(res2["amount_paid"], 15000.0)

    def test_administrative_reports_and_audit_trail(self):
        reports = self.service.generate_administrative_reports(self.admin)
        self.assertIn("total_patients", reports)
        self.assertIn("appointments_by_department", reports)
        self.assertIn("billing_summary", reports)

        audit_trail = self.service.get_audit_trail(self.admin)
        self.assertGreater(len(audit_trail), 0)

    def test_privacy_and_log_sanitization(self):
        masked_phone = mask_phone("+2348031234567")
        self.assertTrue(masked_phone.endswith("4567"))
        self.assertNotIn("123", masked_phone)

        masked_mail = mask_email("doctor.chidi@hospital.org")
        self.assertTrue(masked_mail.endswith("@hospital.org"))
        self.assertNotIn("chidi", masked_mail)

        clean = sanitize_for_audit("User updated password='SuperSecretPassword123' and phone 08031234567")
        self.assertNotIn("SuperSecretPassword123", clean)
        self.assertNotIn("08031234567", clean)


if __name__ == "__main__":
    unittest.main()
