"""
Automated Unit and Integration Tests for Hospital Appointment Management System
Validates database schema, patient/doctor registration, scheduling, conflict prevention,
rescheduling, cancellations, availability calculation, and history searches.
"""

import os
import unittest
import tempfile
from database import initialize_database, STANDARD_TIME_SLOTS
from service import ClinicService
from exceptions import (
    ValidationError,
    NotFoundError,
    DoctorUnavailableError,
    PatientConflictError,
    InvalidStatusTransitionError
)


class TestHospitalManagementSystem(unittest.TestCase):

    def setUp(self):
        # Create a temporary file database for isolated testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        initialize_database(self.db_path)
        self.service = ClinicService(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_initial_seeds(self):
        """Verify doctors and initial fictional patients are seeded correctly."""
        doctors = self.service.list_doctors()
        patients = self.service.list_patients()
        self.assertGreaterEqual(len(doctors), 5)
        self.assertGreaterEqual(len(patients), 3)

    def test_register_patient(self):
        """Test registering a patient assigns a unique formatted ID."""
        patient = self.service.register_patient(
            full_name="Alice Cooper",
            date_of_birth="1992-06-15",
            gender="Female",
            phone_number="+1-555-9999",
            email="alice@test.com"
        )
        self.assertTrue(patient["patient_id"].startswith("PAT-"))
        self.assertEqual(patient["full_name"], "Alice Cooper")

    def test_register_doctor(self):
        """Test registering a new doctor with specialty."""
        doc = self.service.register_doctor(
            full_name="Dr. Gregory House",
            specialty="Diagnostics",
            phone_number="+1-555-4321"
        )
        self.assertEqual(doc["full_name"], "Dr. Gregory House")
        self.assertEqual(doc["specialty"], "Diagnostics")

    def test_check_doctor_availability(self):
        """Test checking doctor availability returns correct standard slots minus booked slots."""
        doc_id = 1
        date_str = "2026-11-25"
        avail = self.service.check_doctor_availability(doc_id, date_str)
        self.assertEqual(len(avail["booked_slots"]), 0)
        self.assertEqual(len(avail["available_slots"]), len(STANDARD_TIME_SLOTS))

        # Book one slot
        self.service.schedule_appointment("PAT-2026-001", doc_id, date_str, "10:00")
        avail_after = self.service.check_doctor_availability(doc_id, date_str)
        self.assertIn("10:00", avail_after["booked_slots"])
        self.assertNotIn("10:00", avail_after["available_slots"])
        self.assertEqual(len(avail_after["available_slots"]), len(STANDARD_TIME_SLOTS) - 1)

    def test_prevent_overlapping_appointments_same_doctor(self):
        """Feature 5: Prevent two patients from booking the same doctor at the same time."""
        doc_id = 1
        date_str = "2026-11-26"
        time_slot = "09:30"

        # First booking succeeds
        app1 = self.service.schedule_appointment("PAT-2026-001", doc_id, date_str, time_slot)
        self.assertEqual(app1["status"], "scheduled")

        # Second booking for different patient with SAME doctor & time slot MUST fail
        with self.assertRaises(DoctorUnavailableError):
            self.service.schedule_appointment("PAT-2026-002", doc_id, date_str, time_slot)

    def test_prevent_patient_double_booking(self):
        """Prevent the same patient from having two appointments at the same time."""
        date_str = "2026-11-26"
        time_slot = "11:00"

        # Book with Doctor 1
        self.service.schedule_appointment("PAT-2026-001", 1, date_str, time_slot)

        # Attempt to book same patient with Doctor 2 at identical time slot
        with self.assertRaises(PatientConflictError):
            self.service.schedule_appointment("PAT-2026-001", 2, date_str, time_slot)

    def test_reschedule_appointment(self):
        """Test rescheduling moves the appointment and frees up the original slot."""
        doc_id = 2
        date1 = "2026-11-27"
        slot1 = "10:00"
        date2 = "2026-11-28"
        slot2 = "14:00"

        app = self.service.schedule_appointment("PAT-2026-001", doc_id, date1, slot1)

        # Reschedule to date2, slot2
        rescheduled = self.service.reschedule_appointment(app["appointment_id"], date2, slot2)
        self.assertEqual(rescheduled["appointment_date"], date2)
        self.assertEqual(rescheduled["time_slot"], slot2)

        # Original slot (date1, slot1) should now be free again
        avail_old = self.service.check_doctor_availability(doc_id, date1)
        self.assertIn(slot1, avail_old["available_slots"])

        # Another patient can now book date1, slot1
        app2 = self.service.schedule_appointment("PAT-2026-002", doc_id, date1, slot1)
        self.assertEqual(app2["status"], "scheduled")

    def test_cancel_appointment(self):
        """Test cancelling updates status to cancelled and frees up the slot."""
        doc_id = 3
        date_str = "2026-11-29"
        slot = "15:00"

        app = self.service.schedule_appointment("PAT-2026-001", doc_id, date_str, slot)
        cancelled = self.service.cancel_appointment(app["appointment_id"])
        self.assertEqual(cancelled["status"], "cancelled")

        # Slot should now be free
        avail = self.service.check_doctor_availability(doc_id, date_str)
        self.assertIn(slot, avail["available_slots"])

        # Cannot cancel again
        with self.assertRaises(InvalidStatusTransitionError):
            self.service.cancel_appointment(app["appointment_id"])

    def test_complete_appointment(self):
        """Test marking appointment as completed."""
        app = self.service.schedule_appointment("PAT-2026-001", 1, "2026-11-30", "13:00")
        completed = self.service.complete_appointment(app["appointment_id"])
        self.assertEqual(completed["status"], "completed")

    def test_display_appointments_by_date(self):
        """Test retrieving appointments by date."""
        target_date = "2026-12-01"
        self.service.schedule_appointment("PAT-2026-001", 1, target_date, "09:00")
        self.service.schedule_appointment("PAT-2026-002", 2, target_date, "10:00")

        results = self.service.get_appointments_by_date(target_date)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["time_slot"], "09:00")
        self.assertEqual(results[1]["time_slot"], "10:00")

    def test_search_patient_appointment_history(self):
        """Test searching appointment history for a patient."""
        pat_id = "PAT-2026-003"
        self.service.schedule_appointment(pat_id, 1, "2026-12-05", "09:00", "Annual checkup")
        self.service.schedule_appointment(pat_id, 2, "2026-12-10", "11:30", "Consultation")

        history_data = self.service.get_patient_appointment_history(pat_id)
        self.assertEqual(history_data["patient"]["patient_id"], pat_id)
        self.assertEqual(len(history_data["history"]), 2)


if __name__ == "__main__":
    unittest.main()
