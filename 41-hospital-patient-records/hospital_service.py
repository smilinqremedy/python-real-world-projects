"""
Business logic and service operations for Hospital Patient Records Management System.
"""
from datetime import datetime, date
import re
import secrets
from database import get_connection, init_db
from security import (
    hash_password,
    verify_password,
    require_permission,
    sanitize_for_audit,
    AccessDeniedError,
)


class HospitalService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Audit Logging Helper ====================

    def _record_audit(self, conn, user: dict, action: str, resource_type: str, resource_id: str, details: str = ""):
        """Record an immutable, privacy-sanitized entry in the audit trail."""
        user_id = user.get("id") if user else None
        username = user.get("username", "System") if user else "System"
        clean_details = sanitize_for_audit(details)
        conn.execute(
            """
            INSERT INTO audit_logs (user_id, username, action, resource_type, resource_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, action, resource_type, str(resource_id), clean_details),
        )

    # ==================== User Management & Authentication ====================

    def register_user(self, admin_context: dict, user_id: str, username: str, password: str,
                      full_name: str, email: str, role: str, department: str = None) -> int:
        """Register a hospital staff user with RBAC role. Requires 'user:manage' permission."""
        if admin_context:
            require_permission(admin_context, "user:manage")

        user_id = user_id.strip().upper()
        username = username.strip().lower()
        full_name = full_name.strip()
        email = email.strip().lower()
        role = role.strip().lower()

        if not user_id or not username or not full_name or not email:
            raise ValueError("All staff fields (User ID, username, name, email) are required.")
        if role not in ("admin", "doctor", "nurse", "receptionist", "billing"):
            raise ValueError(f"Invalid role: {role}. Must be admin, doctor, nurse, receptionist, or billing.")

        # Email validation
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError(f"Invalid email address format: {email}")

        pwd_hash, salt = hash_password(password)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (user_id, username, password_hash, salt, full_name, email, role, department)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, pwd_hash, salt, full_name, email, role, department),
                )
                new_id = cursor.lastrowid
                self._record_audit(
                    conn, admin_context, "CREATE", "USER", user_id,
                    f"Created user account {username} with role {role}"
                )
                return new_id
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("User ID, username, or email is already in use.")
            raise
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticate user credentials and return user context dictionary."""
        username = username.strip().lower()
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)).fetchone()
            if not row:
                raise ValueError("Invalid username or password.")
            user_data = dict(row)
            if not verify_password(password, user_data["salt"], user_data["password_hash"]):
                raise ValueError("Invalid username or password.")

            user_context = {
                "id": user_data["id"],
                "user_id": user_data["user_id"],
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "role": user_data["role"],
                "department": user_data["department"],
                "email": user_data["email"],
            }
            with conn:
                self._record_audit(conn, user_context, "LOGIN", "AUTH", user_context["username"], "User logged in")
            return user_context
        finally:
            conn.close()

    def list_users(self, context_user: dict, role_filter: str = None) -> list[dict]:
        """List active users. Filterable by role."""
        require_permission(context_user, "user:manage")
        conn = self._get_connection()
        try:
            if role_filter:
                rows = conn.execute(
                    "SELECT id, user_id, username, full_name, email, role, department, is_active FROM users WHERE role = ?",
                    (role_filter.lower(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, user_id, username, full_name, email, role, department, is_active FROM users"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Patient Registration & Unique IDs ====================

    def _generate_unique_patient_id(self, conn) -> str:
        """
        Generate a guaranteed collision-free, human-readable patient ID.
        Format: PAT-YYYYMMDD-XXXX (e.g. PAT-20261120-0042)
        """
        today_str = datetime.now().strftime("%Y%m%d")
        for _ in range(100):
            seq = secrets.randbelow(9000) + 1000
            candidate_id = f"PAT-{today_str}-{seq}"
            exists = conn.execute(
                "SELECT 1 FROM patients WHERE patient_id = ?", (candidate_id,)
            ).fetchone()
            if not exists:
                return candidate_id
        raise RuntimeError("Failed to allocate a unique patient identification number.")

    @staticmethod
    def _validate_patient_data(first_name: str, last_name: str, dob: str, gender: str, blood_group: str, phone: str, email: str = None):
        """Strict validation of patient demographics."""
        if not first_name or len(first_name.strip()) < 2:
            raise ValueError("First name must be at least 2 characters long.")
        if not last_name or len(last_name.strip()) < 2:
            raise ValueError("Last name must be at least 2 characters long.")

        # Date of Birth validation
        try:
            dob_parsed = datetime.strptime(dob.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date of birth must follow 'YYYY-MM-DD' format.")

        if dob_parsed >= date.today():
            raise ValueError("Date of birth must be a valid date in the past.")

        if gender.upper() not in ("M", "F", "OTHER"):
            raise ValueError("Gender must be 'M', 'F', or 'Other'.")

        valid_bloods = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN")
        if blood_group.upper() not in valid_bloods:
            raise ValueError(f"Blood group must be one of {valid_bloods}.")

        # Phone format validation (allows international or standard numbers)
        clean_phone = re.sub(r"[\s\-\(\)]", "", phone.strip())
        if not re.match(r"^\+?[0-9]{7,15}$", clean_phone):
            raise ValueError("Phone number must contain between 7 and 15 digits.")

        if email and email.strip():
            if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email.strip()):
                raise ValueError("Invalid email address format.")

    def register_patient(self, context_user: dict, first_name: str, last_name: str,
                         date_of_birth: str, gender: str, blood_group: str, phone: str,
                         email: str = None, address: str = None, emergency_name: str = None,
                         emergency_phone: str = None, allergies: str = "None reported",
                         chronic_conditions: str = "None reported") -> str:
        """
        Register a new patient and allocate a unique identification number.
        Requires 'patient:create' permission.
        """
        require_permission(context_user, "patient:create")

        first_name = first_name.strip().title()
        last_name = last_name.strip().title()
        dob = date_of_birth.strip()
        gender = gender.strip().capitalize()
        blood_group = blood_group.strip().upper()
        phone = phone.strip()
        email = email.strip().lower() if email else None
        address = address.strip() if address else None
        emergency_name = emergency_name.strip() if emergency_name else None
        emergency_phone = emergency_phone.strip() if emergency_phone else None
        allergies = allergies.strip() if allergies else "None reported"
        chronic_conditions = chronic_conditions.strip() if chronic_conditions else "None reported"

        self._validate_patient_data(first_name, last_name, dob, gender, blood_group, phone, email)

        conn = self._get_connection()
        try:
            with conn:
                # Prevent duplicate patient registrations
                duplicate = conn.execute(
                    """
                    SELECT patient_id FROM patients
                    WHERE lower(first_name) = lower(?) AND lower(last_name) = lower(?)
                      AND date_of_birth = ? AND phone = ?
                    """,
                    (first_name, last_name, dob, phone),
                ).fetchone()
                if duplicate:
                    raise ValueError(
                        f"Duplicate patient record detected! Patient already registered with ID: {duplicate['patient_id']}."
                    )

                patient_id = self._generate_unique_patient_id(conn)
                creator_id = context_user.get("id")

                conn.execute(
                    """
                    INSERT INTO patients (
                        patient_id, first_name, last_name, date_of_birth, gender,
                        blood_group, phone, email, address, emergency_name, emergency_phone,
                        allergies, chronic_conditions, created_by, updated_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_id, first_name, last_name, dob, gender,
                        blood_group, phone, email, address, emergency_name, emergency_phone,
                        allergies, chronic_conditions, creator_id, creator_id
                    ),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "PATIENT", patient_id,
                    f"Registered new patient {first_name} {last_name}"
                )
                return patient_id
        finally:
            conn.close()

    def update_patient(self, context_user: dict, patient_id: str, **updates) -> bool:
        """Update patient demographic details with audit trail. Requires 'patient:update'."""
        require_permission(context_user, "patient:update")
        patient_id = patient_id.strip().upper()

        allowed_fields = {
            "first_name", "last_name", "date_of_birth", "gender", "blood_group",
            "phone", "email", "address", "emergency_name", "emergency_phone",
            "allergies", "chronic_conditions"
        }

        update_items = {}
        for k, v in updates.items():
            if k in allowed_fields and v is not None:
                update_items[k] = v

        if not update_items:
            raise ValueError("No valid patient fields provided for update.")

        conn = self._get_connection()
        try:
            with conn:
                existing = conn.execute(
                    "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
                ).fetchone()
                if not existing:
                    raise ValueError(f"Patient with ID '{patient_id}' not found.")

                set_clauses = [f"{field} = ?" for field in update_items.keys()]
                set_clauses.append("updated_by = ?")
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values = list(update_items.values()) + [context_user.get("id"), patient_id]

                conn.execute(
                    f"UPDATE patients SET {', '.join(set_clauses)} WHERE patient_id = ?",
                    values,
                )

                self._record_audit(
                    conn, context_user, "UPDATE", "PATIENT", patient_id,
                    f"Updated fields: {', '.join(update_items.keys())}"
                )
                return True
        finally:
            conn.close()

    def search_patients(self, context_user: dict, query: str = None, search_by: str = "all") -> list[dict]:
        """
        Search patient records by ID, name, phone, or date of birth.
        Requires 'patient:view_demographics'.
        """
        require_permission(context_user, "patient:view_demographics")
        conn = self._get_connection()
        try:
            if not query or not query.strip():
                rows = conn.execute(
                    """
                    SELECT id, patient_id, first_name, last_name, date_of_birth, gender,
                           blood_group, phone, email, address, created_at
                    FROM patients ORDER BY created_at DESC LIMIT 50
                    """
                ).fetchall()
            else:
                q = f"%{query.strip().lower()}%"
                if search_by == "id":
                    sql = "SELECT * FROM patients WHERE lower(patient_id) LIKE ? ORDER BY created_at DESC"
                    params = (q,)
                elif search_by == "name":
                    sql = "SELECT * FROM patients WHERE lower(first_name) LIKE ? OR lower(last_name) LIKE ? ORDER BY created_at DESC"
                    params = (q, q)
                elif search_by == "phone":
                    sql = "SELECT * FROM patients WHERE phone LIKE ? ORDER BY created_at DESC"
                    params = (q,)
                elif search_by == "dob":
                    sql = "SELECT * FROM patients WHERE date_of_birth LIKE ? ORDER BY created_at DESC"
                    params = (q,)
                else:  # all
                    sql = """
                    SELECT * FROM patients
                    WHERE lower(patient_id) LIKE ? OR lower(first_name) LIKE ?
                       OR lower(last_name) LIKE ? OR phone LIKE ? OR date_of_birth LIKE ?
                    ORDER BY created_at DESC
                    """
                    params = (q, q, q, q, q)

                rows = conn.execute(sql, params).fetchall()

            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_patient(self, context_user: dict, patient_id: str) -> dict:
        """
        Retrieve complete patient record. Clinical notes are only returned
        if user role possesses 'patient:view_clinical' permission.
        """
        require_permission(context_user, "patient:view_demographics")
        patient_id = patient_id.strip().upper()

        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
            if not row:
                raise ValueError(f"Patient with ID '{patient_id}' not found.")

            patient = dict(row)

            # Record audit of patient record access
            with conn:
                self._record_audit(
                    conn, context_user, "ACCESS", "PATIENT", patient_id,
                    "Viewed patient file"
                )

            # Include related historical collections
            appointments = conn.execute(
                """
                SELECT a.*, u.full_name as doctor_name
                FROM appointments a
                LEFT JOIN users u ON a.doctor_id = u.id
                WHERE a.patient_id = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """,
                (patient["id"],),
            ).fetchall()
            patient["appointments"] = [dict(a) for a in appointments]

            visits = conn.execute(
                """
                SELECT v.*, u.full_name as staff_name
                FROM visits v
                LEFT JOIN users u ON v.attending_staff_id = u.id
                WHERE v.patient_id = ?
                ORDER BY v.visit_date DESC
                """,
                (patient["id"],),
            ).fetchall()
            patient["visits"] = [dict(v) for v in visits]

            # Clinical details (only for clinical staff)
            has_clinical_access = True
            try:
                require_permission(context_user, "patient:view_clinical")
            except AccessDeniedError:
                has_clinical_access = False

            if has_clinical_access:
                vitals = conn.execute(
                    """
                    SELECT vs.*, u.full_name as recorded_by_name
                    FROM vital_signs vs
                    LEFT JOIN users u ON vs.recorded_by = u.id
                    WHERE vs.patient_id = ?
                    ORDER BY vs.recorded_at DESC
                    """,
                    (patient["id"],),
                ).fetchall()
                patient["vital_signs"] = [dict(vs) for vs in vitals]

                notes = conn.execute(
                    """
                    SELECT cn.*, u.full_name as author_name
                    FROM clinical_notes cn
                    LEFT JOIN users u ON cn.author_id = u.id
                    WHERE cn.patient_id = ?
                    ORDER BY cn.created_at DESC
                    """,
                    (patient["id"],),
                ).fetchall()
                patient["clinical_notes"] = [dict(n) for n in notes]
            else:
                patient["vital_signs"] = []
                patient["clinical_notes"] = []

            return patient
        finally:
            conn.close()

    # ==================== Appointment Scheduling ====================

    def register_appointment(self, context_user: dict, patient_id: str, doctor_user_id: str,
                             department: str, appointment_date: str, appointment_time: str,
                             reason: str, notes: str = None) -> str:
        """
        Schedule an appointment. Validates doctor assignment and checks for timeslot conflicts.
        Requires 'appointment:create' permission.
        """
        require_permission(context_user, "appointment:create")
        patient_id = patient_id.strip().upper()
        doctor_user_id = doctor_user_id.strip().upper()
        department = department.strip()
        appointment_date = appointment_date.strip()
        appointment_time = appointment_time.strip()
        reason = reason.strip()

        if not reason:
            raise ValueError("Reason for appointment is required.")

        # Date validation
        try:
            apt_date = datetime.strptime(appointment_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Appointment date must be 'YYYY-MM-DD'.")

        try:
            datetime.strptime(appointment_time, "%H:%M")
        except ValueError:
            raise ValueError("Appointment time must be 'HH:MM' (24-hour format).")

        conn = self._get_connection()
        try:
            with conn:
                # Validate patient
                patient = conn.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
                if not patient:
                    raise ValueError(f"Patient ID '{patient_id}' does not exist.")

                # Validate doctor
                doctor = conn.execute(
                    "SELECT id, role FROM users WHERE user_id = ? AND is_active = 1", (doctor_user_id,)
                ).fetchone()
                if not doctor:
                    raise ValueError(f"Staff user ID '{doctor_user_id}' not found.")
                if doctor["role"] not in ("doctor", "nurse", "admin"):
                    raise ValueError(f"User '{doctor_user_id}' is not an authorized healthcare practitioner.")

                # Check for double booking
                conflict = conn.execute(
                    """
                    SELECT appointment_ref FROM appointments
                    WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?
                      AND status NOT IN ('Cancelled', 'No-Show')
                    """,
                    (doctor["id"], appointment_date, appointment_time),
                ).fetchone()
                if conflict:
                    raise ValueError(
                        f"Doctor '{doctor_user_id}' already has an active appointment ({conflict['appointment_ref']}) at {appointment_time} on {appointment_date}."
                    )

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                appointment_ref = f"APT-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO appointments (
                        appointment_ref, patient_id, doctor_id, department,
                        appointment_date, appointment_time, reason, notes, scheduled_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        appointment_ref, patient["id"], doctor["id"], department,
                        appointment_date, appointment_time, reason, notes, context_user.get("id")
                    ),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "APPOINTMENT", appointment_ref,
                    f"Scheduled appointment for patient {patient_id} with doctor {doctor_user_id}"
                )
                return appointment_ref
        finally:
            conn.close()

    def update_appointment_status(self, context_user: dict, appointment_ref: str,
                                  new_status: str, notes: str = None) -> bool:
        """Update appointment status. Requires 'appointment:update'."""
        require_permission(context_user, "appointment:update")
        appointment_ref = appointment_ref.strip().upper()
        valid_statuses = ("Scheduled", "In-Progress", "Completed", "Cancelled", "No-Show")

        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        conn = self._get_connection()
        try:
            with conn:
                existing = conn.execute(
                    "SELECT id, status FROM appointments WHERE appointment_ref = ?", (appointment_ref,)
                ).fetchone()
                if not existing:
                    raise ValueError(f"Appointment '{appointment_ref}' not found.")

                conn.execute(
                    """
                    UPDATE appointments
                    SET status = ?, notes = coalesce(?, notes), updated_at = CURRENT_TIMESTAMP
                    WHERE appointment_ref = ?
                    """,
                    (new_status, notes, appointment_ref),
                )

                self._record_audit(
                    conn, context_user, "UPDATE", "APPOINTMENT", appointment_ref,
                    f"Changed status from {existing['status']} to {new_status}"
                )
                return True
        finally:
            conn.close()

    def get_appointment_history(self, context_user: dict, patient_id: str) -> list[dict]:
        """Track appointment history for a given patient. Requires 'appointment:view'."""
        require_permission(context_user, "appointment:view")
        patient_id = patient_id.strip().upper()

        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT a.appointment_ref, a.appointment_date, a.appointment_time,
                       a.department, a.reason, a.status, a.notes,
                       u.full_name as doctor_name, u.user_id as doctor_user_id
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN users u ON a.doctor_id = u.id
                WHERE p.patient_id = ?
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """,
                (patient_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Clinical Visits & Encounters ====================

    def record_visit(self, context_user: dict, patient_id: str, visit_type: str,
                     attending_staff_id: str, chief_complaint: str,
                     appointment_ref: str = None) -> str:
        """
        Record patient arrival / clinical encounter visit date.
        Requires 'visit:create' permission.
        """
        require_permission(context_user, "visit:create")
        patient_id = patient_id.strip().upper()
        attending_staff_id = attending_staff_id.strip().upper()
        chief_complaint = chief_complaint.strip()

        valid_types = ("Outpatient", "Inpatient", "Emergency", "Follow-up")
        if visit_type not in valid_types:
            raise ValueError(f"Visit type must be one of: {', '.join(valid_types)}")

        if not chief_complaint:
            raise ValueError("Chief complaint / reason for visit is required.")

        conn = self._get_connection()
        try:
            with conn:
                patient = conn.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
                if not patient:
                    raise ValueError(f"Patient '{patient_id}' not found.")

                staff = conn.execute(
                    "SELECT id FROM users WHERE user_id = ? AND is_active = 1", (attending_staff_id,)
                ).fetchone()
                if not staff:
                    raise ValueError(f"Staff member '{attending_staff_id}' not found.")

                apt_id = None
                if appointment_ref:
                    apt = conn.execute(
                        "SELECT id FROM appointments WHERE appointment_ref = ?", (appointment_ref.strip().upper(),)
                    ).fetchone()
                    if apt:
                        apt_id = apt["id"]

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                visit_ref = f"VST-{today_str}-{seq}"
                visit_date = datetime.now().strftime("%Y-%m-%d")

                conn.execute(
                    """
                    INSERT INTO visits (
                        visit_ref, patient_id, appointment_id, visit_date,
                        visit_type, attending_staff_id, chief_complaint, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
                    """,
                    (visit_ref, patient["id"], apt_id, visit_date, visit_type, staff["id"], chief_complaint),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "VISIT", visit_ref,
                    f"Recorded {visit_type} visit for patient {patient_id}"
                )
                return visit_ref
        finally:
            conn.close()

    # ==================== Vital Signs & Clinical Observations ====================

    def record_vital_signs(self, context_user: dict, visit_ref: str,
                           systolic_bp: int, diastolic_bp: int, heart_rate: int,
                           temperature_c: float, respiratory_rate: int,
                           spo2_percent: float, weight_kg: float, height_cm: float,
                           notes: str = None) -> int:
        """
        Record patient vital signs and automatically compute BMI.
        Requires 'vitals:create' permission (Doctor or Nurse).
        """
        require_permission(context_user, "vitals:create")
        visit_ref = visit_ref.strip().upper()

        # Physiological boundary checks
        if systolic_bp < 50 or systolic_bp > 300:
            raise ValueError("Systolic BP must be between 50 and 300 mmHg.")
        if diastolic_bp < 30 or diastolic_bp > 200:
            raise ValueError("Diastolic BP must be between 30 and 200 mmHg.")
        if systolic_bp <= diastolic_bp:
            raise ValueError("Systolic BP must be higher than diastolic BP.")
        if heart_rate < 30 or heart_rate > 250:
            raise ValueError("Heart rate must be between 30 and 250 bpm.")
        if temperature_c < 30.0 or temperature_c > 45.0:
            raise ValueError("Body temperature must be between 30.0°C and 45.0°C.")
        if respiratory_rate < 6 or respiratory_rate > 60:
            raise ValueError("Respiratory rate must be between 6 and 60 breaths/min.")
        if spo2_percent < 50.0 or spo2_percent > 100.0:
            raise ValueError("SpO2 oxygen saturation must be between 50.0% and 100.0%.")
        if weight_kg < 1.0 or weight_kg > 500.0:
            raise ValueError("Weight must be between 1.0 and 500.0 kg.")
        if height_cm < 30.0 or height_cm > 260.0:
            raise ValueError("Height must be between 30.0 and 260.0 cm.")

        # Compute Body Mass Index (BMI = kg / m^2)
        height_m = height_cm / 100.0
        bmi = round(weight_kg / (height_m * height_m), 2)

        conn = self._get_connection()
        try:
            with conn:
                visit = conn.execute(
                    "SELECT id, patient_id FROM visits WHERE visit_ref = ?", (visit_ref,)
                ).fetchone()
                if not visit:
                    raise ValueError(f"Visit record '{visit_ref}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO vital_signs (
                        visit_id, patient_id, recorded_by, systolic_bp, diastolic_bp,
                        heart_rate, temperature_c, respiratory_rate, spo2_percent,
                        weight_kg, height_cm, bmi, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        visit["id"], visit["patient_id"], context_user.get("id"),
                        systolic_bp, diastolic_bp, heart_rate, temperature_c,
                        respiratory_rate, spo2_percent, weight_kg, height_cm, bmi, notes
                    ),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "VITALS", visit_ref,
                    f"Recorded vital signs for visit {visit_ref}: BP {systolic_bp}/{diastolic_bp}, HR {heart_rate}, Temp {temperature_c}C, BMI {bmi}"
                )
                return cursor.lastrowid
        finally:
            conn.close()

    # ==================== Authorized Clinical Notes ====================

    def record_clinical_note(self, context_user: dict, visit_ref: str, note_type: str,
                             subjective_observations: str, objective_observations: str,
                             clinical_assessment: str, care_plan: str) -> int:
        """
        Store authorized clinical notes recorded by an authorized medical professional.
        Requires 'clinical_notes:create' permission (Doctor).
        IMPORTANT: This system strictly avoids automated diagnosis or automated prescription.
        All entries must be direct human clinical documentation.
        """
        require_permission(context_user, "clinical_notes:create")
        visit_ref = visit_ref.strip().upper()

        valid_note_types = ("Consultation", "Progress Note", "Nursing Note", "Discharge Summary")
        if note_type not in valid_note_types:
            raise ValueError(f"Note type must be one of: {', '.join(valid_note_types)}")

        if not subjective_observations or not objective_observations or not clinical_assessment or not care_plan:
            raise ValueError("All SOAP components (Subjective, Objective, Assessment, Plan) are required.")

        conn = self._get_connection()
        try:
            with conn:
                visit = conn.execute(
                    "SELECT id, patient_id FROM visits WHERE visit_ref = ?", (visit_ref,)
                ).fetchone()
                if not visit:
                    raise ValueError(f"Visit record '{visit_ref}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO clinical_notes (
                        visit_id, patient_id, author_id, note_type,
                        subjective_observations, objective_observations,
                        clinical_assessment, care_plan
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        visit["id"], visit["patient_id"], context_user.get("id"), note_type,
                        subjective_observations.strip(), objective_observations.strip(),
                        clinical_assessment.strip(), care_plan.strip()
                    ),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "CLINICAL_NOTE", visit_ref,
                    f"Recorded {note_type} for visit {visit_ref} by {context_user.get('username')}"
                )
                return cursor.lastrowid
        finally:
            conn.close()

    # ==================== Billing Records ====================

    def create_billing_invoice(self, context_user: dict, patient_id: str,
                               description: str, amount: float, visit_ref: str = None) -> str:
        """Create a hospital billing invoice. Requires 'billing:create'."""
        require_permission(context_user, "billing:create")
        patient_id = patient_id.strip().upper()
        if amount <= 0:
            raise ValueError("Invoice amount must be greater than zero.")

        conn = self._get_connection()
        try:
            with conn:
                patient = conn.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
                if not patient:
                    raise ValueError(f"Patient '{patient_id}' not found.")

                visit_id = None
                if visit_ref:
                    v = conn.execute("SELECT id FROM visits WHERE visit_ref = ?", (visit_ref.strip().upper(),)).fetchone()
                    if v:
                        visit_id = v["id"]

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                invoice_ref = f"INV-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO billing_invoices (invoice_ref, patient_id, visit_id, description, amount, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (invoice_ref, patient["id"], visit_id, description.strip(), amount, context_user.get("id")),
                )

                self._record_audit(
                    conn, context_user, "CREATE", "INVOICE", invoice_ref,
                    f"Created invoice for patient {patient_id} amount {amount}"
                )
                return invoice_ref
        finally:
            conn.close()

    def record_payment(self, context_user: dict, invoice_ref: str, payment_amount: float) -> dict:
        """Record a payment towards an invoice. Requires 'billing:create'."""
        require_permission(context_user, "billing:create")
        invoice_ref = invoice_ref.strip().upper()
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive.")

        conn = self._get_connection()
        try:
            with conn:
                inv = conn.execute(
                    "SELECT * FROM billing_invoices WHERE invoice_ref = ?", (invoice_ref,)
                ).fetchone()
                if not inv:
                    raise ValueError(f"Invoice '{invoice_ref}' not found.")

                new_paid = inv["amount_paid"] + payment_amount
                if new_paid > inv["amount"]:
                    raise ValueError(f"Payment exceeds remaining invoice balance. Total: {inv['amount']}, Current paid: {inv['amount_paid']}.")

                status = "Paid" if new_paid >= inv["amount"] else "Partial"
                paid_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status == "Paid" else None

                conn.execute(
                    """
                    UPDATE billing_invoices
                    SET amount_paid = ?, status = ?, paid_at = coalesce(?, paid_at)
                    WHERE invoice_ref = ?
                    """,
                    (new_paid, status, paid_at, invoice_ref),
                )

                self._record_audit(
                    conn, context_user, "UPDATE", "INVOICE", invoice_ref,
                    f"Recorded payment {payment_amount} for {invoice_ref}; status: {status}"
                )
                return {"invoice_ref": invoice_ref, "amount_paid": new_paid, "status": status}
        finally:
            conn.close()

    # ==================== Administrative Reports ====================

    def generate_administrative_reports(self, context_user: dict) -> dict:
        """
        Generate administrative analytics and operational summaries.
        Requires 'reports:view' permission.
        """
        require_permission(context_user, "reports:view")
        conn = self._get_connection()
        try:
            total_patients = conn.execute("SELECT count(*) FROM patients").fetchone()[0]

            # Patient registrations by month
            registrations_by_month = conn.execute(
                """
                SELECT strftime('%Y-%m', created_at) as month, count(*) as count
                FROM patients
                GROUP BY month ORDER BY month DESC LIMIT 6
                """
            ).fetchall()

            # Appointments by status
            appointments_by_status = conn.execute(
                "SELECT status, count(*) as count FROM appointments GROUP BY status"
            ).fetchall()

            # Appointments by department
            appointments_by_dept = conn.execute(
                "SELECT department, count(*) as count FROM appointments GROUP BY department ORDER BY count DESC"
            ).fetchall()

            # Doctor consultation workload
            doctor_workload = conn.execute(
                """
                SELECT u.full_name as doctor_name, u.department, count(a.id) as total_appointments
                FROM users u
                JOIN appointments a ON u.id = a.doctor_id
                GROUP BY u.id ORDER BY total_appointments DESC
                """
            ).fetchall()

            # Total visits by type
            visits_by_type = conn.execute(
                "SELECT visit_type, count(*) as count FROM visits GROUP BY visit_type"
            ).fetchall()

            # Billing summary
            billing_summary = conn.execute(
                """
                SELECT count(*) as total_invoices,
                       coalesce(sum(amount), 0.0) as total_billed,
                       coalesce(sum(amount_paid), 0.0) as total_collected,
                       coalesce(sum(amount - amount_paid), 0.0) as outstanding_balance
                FROM billing_invoices
                """
            ).fetchone()

            return {
                "total_patients": total_patients,
                "registrations_by_month": [dict(r) for r in registrations_by_month],
                "appointments_by_status": [dict(r) for r in appointments_by_status],
                "appointments_by_department": [dict(r) for r in appointments_by_dept],
                "doctor_workload": [dict(r) for r in doctor_workload],
                "visits_by_type": [dict(r) for r in visits_by_type],
                "billing_summary": dict(billing_summary),
            }
        finally:
            conn.close()

    def get_audit_trail(self, context_user: dict, limit: int = 50) -> list[dict]:
        """View sanitized system audit trail. Requires 'audit:view' (Admin only)."""
        require_permission(context_user, "audit:view")
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT id, username, action, resource_type, resource_id, details, timestamp
                FROM audit_logs
                ORDER BY timestamp DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
