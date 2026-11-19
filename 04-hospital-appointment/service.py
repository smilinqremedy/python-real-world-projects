"""
Service Layer for Hospital Appointment Management System
Encapsulates business logic, conflict prevention, availability calculations, and validation.
"""

from datetime import datetime
import sqlite3
from database import get_db_connection, STANDARD_TIME_SLOTS, DEFAULT_DB_FILE
from exceptions import (
    ValidationError,
    NotFoundError,
    DoctorUnavailableError,
    PatientConflictError,
    InvalidStatusTransitionError
)


class ClinicService:
    def __init__(self, db_path=DEFAULT_DB_FILE):
        self.db_path = db_path

    # ==========================================
    # 1. PATIENT MANAGEMENT
    # ==========================================

    def generate_patient_id(self):
        """
        Generates a unique patient ID formatted as PAT-YYYY-NNN.
        """
        year = datetime.now().year
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT patient_id FROM patients WHERE patient_id LIKE ?;", (f"PAT-{year}-%",))
            rows = cursor.fetchall()
            existing_nums = []
            for row in rows:
                try:
                    num_part = int(row["patient_id"].split("-")[-1])
                    existing_nums.append(num_part)
                except ValueError:
                    pass
            next_num = max(existing_nums, default=0) + 1
            return f"PAT-{year}-{next_num:03d}"

    def register_patient(self, full_name, date_of_birth, gender, phone_number, email=None):
        """
        Registers a new patient with a unique patient ID.
        """
        name = full_name.strip()
        if not name:
            raise ValidationError("Patient full name cannot be blank.")

        try:
            datetime.strptime(date_of_birth, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date of birth format. Must be YYYY-MM-DD.")

        if not phone_number.strip():
            raise ValidationError("Phone number cannot be blank.")

        patient_id = self.generate_patient_id()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO patients (patient_id, full_name, date_of_birth, gender, phone_number, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (patient_id, name, date_of_birth, gender.strip(), phone_number.strip(), email.strip() if email else None, now_str))
            conn.commit()

        return self.get_patient_by_id(patient_id)

    def get_patient_by_id(self, patient_id):
        """
        Retrieves patient by patient_id.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE patient_id = ?;", (patient_id.strip().upper(),))
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Patient with ID '{patient_id}' not found.")
            return dict(row)

    def list_patients(self):
        """
        Retrieves all registered patients.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients ORDER BY patient_id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 2. DOCTOR MANAGEMENT
    # ==========================================

    def register_doctor(self, full_name, specialty, phone_number=None, email=None):
        """
        Registers a new doctor and their specialty.
        """
        name = full_name.strip()
        spec = specialty.strip()
        if not name:
            raise ValidationError("Doctor name cannot be blank.")
        if not spec:
            raise ValidationError("Specialty cannot be blank.")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO doctors (full_name, specialty, phone_number, email)
            VALUES (?, ?, ?, ?);
            """, (name, spec, phone_number.strip() if phone_number else None, email.strip() if email else None))
            conn.commit()
            doc_id = cursor.lastrowid

        return self.get_doctor_by_id(doc_id)

    def get_doctor_by_id(self, doctor_id):
        """
        Retrieves doctor by ID.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE doctor_id = ?;", (doctor_id,))
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Doctor ID {doctor_id} not found.")
            return dict(row)

    def list_doctors(self):
        """
        Retrieves all active doctors.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE is_active = 1 ORDER BY specialty, full_name;")
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 3. AVAILABILITY & SCHEDULING ALGORITHM
    # ==========================================

    def check_doctor_availability(self, doctor_id, appointment_date):
        """
        Checks doctor availability for a given date.
        Returns:
            dict containing:
            - doctor: doctor details
            - date: appointment date
            - booked_slots: list of booked time slots
            - available_slots: list of remaining free time slots
        """
        doctor = self.get_doctor_by_id(doctor_id)

        try:
            datetime.strptime(appointment_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format. Must be YYYY-MM-DD.")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT time_slot FROM appointments
            WHERE doctor_id = ? AND appointment_date = ? AND status = 'scheduled'
            ORDER BY time_slot ASC;
            """, (doctor_id, appointment_date))
            booked_slots = [r["time_slot"] for r in cursor.fetchall()]

        available_slots = [slot for slot in STANDARD_TIME_SLOTS if slot not in booked_slots]

        return {
            "doctor": doctor,
            "date": appointment_date,
            "booked_slots": booked_slots,
            "available_slots": available_slots
        }

    def schedule_appointment(self, patient_id, doctor_id, appointment_date, time_slot, reason="General Consultation"):
        """
        Schedules a new appointment with strict conflict prevention.
        Guarantees that no two patients can book the same doctor at the same time.
        """
        # Validate patient and doctor exist
        patient = self.get_patient_by_id(patient_id)
        doctor = self.get_doctor_by_id(doctor_id)

        # Validate date format
        try:
            parsed_date = datetime.strptime(appointment_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid appointment date format. Use YYYY-MM-DD.")

        # Validate time slot
        if time_slot not in STANDARD_TIME_SLOTS:
            raise ValidationError(f"Invalid time slot '{time_slot}'. Standard slots: {STANDARD_TIME_SLOTS}")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Rule 1: Check if doctor is already booked for this slot
            cursor.execute("""
            SELECT appointment_id FROM appointments
            WHERE doctor_id = ? AND appointment_date = ? AND time_slot = ? AND status = 'scheduled';
            """, (doctor_id, appointment_date, time_slot))
            if cursor.fetchone():
                raise DoctorUnavailableError(
                    f"Conflict detected: {doctor['full_name']} is already booked on {appointment_date} at {time_slot}."
                )

            # Rule 2: Check if patient already has an active appointment at this slot
            cursor.execute("""
            SELECT appointment_id FROM appointments
            WHERE patient_id = ? AND appointment_date = ? AND time_slot = ? AND status = 'scheduled';
            """, (patient["patient_id"], appointment_date, time_slot))
            if cursor.fetchone():
                raise PatientConflictError(
                    f"Patient {patient['full_name']} already has another appointment scheduled on {appointment_date} at {time_slot}."
                )

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, time_slot, reason, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'scheduled', ?, ?);
                """, (patient["patient_id"], doctor_id, appointment_date, time_slot, reason.strip(), now_str, now_str))
                conn.commit()
                appointment_id = cursor.lastrowid
            except sqlite3.IntegrityError as err:
                raise DoctorUnavailableError(f"Database constraint violation: time slot is no longer available ({err}).")

        return self.get_appointment_by_id(appointment_id)

    # ==========================================
    # 4. RESCHEDULE & CANCEL
    # ==========================================

    def reschedule_appointment(self, appointment_id, new_date, new_time_slot):
        """
        Reschedules an existing scheduled appointment to a new date and time slot.
        Frees old slot and verifies availability of new slot.
        """
        app = self.get_appointment_by_id(appointment_id)

        if app["status"] != "scheduled":
            raise InvalidStatusTransitionError(
                f"Cannot reschedule an appointment with status '{app['status']}'. Only 'scheduled' appointments can be rescheduled."
            )

        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format. Must be YYYY-MM-DD.")

        if new_time_slot not in STANDARD_TIME_SLOTS:
            raise ValidationError(f"Invalid time slot '{new_time_slot}'.")

        # If date and slot are identical, no change needed
        if app["appointment_date"] == new_date and app["time_slot"] == new_time_slot:
            return app

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if doctor is free at the new slot (excluding current appointment id)
            cursor.execute("""
            SELECT appointment_id FROM appointments
            WHERE doctor_id = ? AND appointment_date = ? AND time_slot = ? AND status = 'scheduled' AND appointment_id != ?;
            """, (app["doctor_id"], new_date, new_time_slot, appointment_id))
            if cursor.fetchone():
                raise DoctorUnavailableError(
                    f"Cannot reschedule: Doctor {app['doctor_name']} is already booked on {new_date} at {new_time_slot}."
                )

            # Check if patient is free at the new slot
            cursor.execute("""
            SELECT appointment_id FROM appointments
            WHERE patient_id = ? AND appointment_date = ? AND time_slot = ? AND status = 'scheduled' AND appointment_id != ?;
            """, (app["patient_id"], new_date, new_time_slot, appointment_id))
            if cursor.fetchone():
                raise PatientConflictError(
                    f"Cannot reschedule: Patient {app['patient_name']} already has another appointment on {new_date} at {new_time_slot}."
                )

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
            UPDATE appointments
            SET appointment_date = ?, time_slot = ?, updated_at = ?
            WHERE appointment_id = ?;
            """, (new_date, new_time_slot, now_str, appointment_id))
            conn.commit()

        return self.get_appointment_by_id(appointment_id)

    def cancel_appointment(self, appointment_id):
        """
        Cancels an appointment, updating its status to 'cancelled' and freeing up the time slot.
        """
        app = self.get_appointment_by_id(appointment_id)

        if app["status"] == "cancelled":
            raise InvalidStatusTransitionError("Appointment is already cancelled.")
        if app["status"] == "completed":
            raise InvalidStatusTransitionError("Cannot cancel an appointment that has already been completed.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE appointments
            SET status = 'cancelled', updated_at = ?
            WHERE appointment_id = ?;
            """, (now_str, appointment_id))
            conn.commit()

        return self.get_appointment_by_id(appointment_id)

    def complete_appointment(self, appointment_id):
        """
        Marks an appointment as completed.
        """
        app = self.get_appointment_by_id(appointment_id)
        if app["status"] != "scheduled":
            raise InvalidStatusTransitionError(f"Cannot complete an appointment with status '{app['status']}'.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE appointments
            SET status = 'completed', updated_at = ?
            WHERE appointment_id = ?;
            """, (now_str, appointment_id))
            conn.commit()

        return self.get_appointment_by_id(appointment_id)

    # ==========================================
    # 5. QUERIES & REPORTS
    # ==========================================

    def get_appointment_by_id(self, appointment_id):
        """
        Fetches an appointment with patient and doctor details joined.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                a.appointment_id,
                a.patient_id,
                p.full_name AS patient_name,
                p.phone_number AS patient_phone,
                a.doctor_id,
                d.full_name AS doctor_name,
                d.specialty AS doctor_specialty,
                a.appointment_date,
                a.time_slot,
                a.reason,
                a.status,
                a.created_at,
                a.updated_at
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_id = ?;
            """, (appointment_id,))
            row = cursor.fetchone()
            if not row:
                raise NotFoundError(f"Appointment ID {appointment_id} not found.")
            return dict(row)

    def get_appointments_by_date(self, target_date):
        """
        Retrieves all appointments scheduled on a given date.
        """
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Invalid date format. Must be YYYY-MM-DD.")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                a.appointment_id,
                a.patient_id,
                p.full_name AS patient_name,
                a.doctor_id,
                d.full_name AS doctor_name,
                d.specialty AS doctor_specialty,
                a.appointment_date,
                a.time_slot,
                a.reason,
                a.status
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.appointment_date = ?
            ORDER BY a.time_slot ASC, d.full_name ASC;
            """, (target_date,))
            return [dict(r) for r in cursor.fetchall()]

    def get_patient_appointment_history(self, patient_id):
        """
        Searches and returns the full appointment history for a patient.
        """
        # Ensure patient exists
        patient = self.get_patient_by_id(patient_id)

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                a.appointment_id,
                a.patient_id,
                a.doctor_id,
                d.full_name AS doctor_name,
                d.specialty AS doctor_specialty,
                a.appointment_date,
                a.time_slot,
                a.reason,
                a.status,
                a.created_at
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id = ?
            ORDER BY a.appointment_date DESC, a.time_slot DESC;
            """, (patient["patient_id"],))
            return {
                "patient": patient,
                "history": [dict(r) for r in cursor.fetchall()]
            }
