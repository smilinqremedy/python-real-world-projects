"""
Business logic and applicant tracking service for Job Recruitment and Applicant Tracking System.
"""
from datetime import datetime
import hashlib
import hmac
import os
import re
import secrets
from database import get_connection, init_db
from cv_storage import CVStorageManager

VALID_APPLICATION_STATUSES = (
    "Submitted",
    "Under Review",
    "Shortlisted",
    "Interview Scheduled",
    "Accepted",
    "Rejected",
)


class AccessControlError(PermissionError):
    """Raised when an operation violates role authorization."""
    pass


class RecruitmentService:
    def __init__(self, db_path=None, upload_dir=None):
        self.db_path = db_path
        self.storage = CVStorageManager(upload_dir)
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Authentication & Passwords ====================

    @staticmethod
    def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if not salt:
            salt = os.urandom(16).hex()
        pwd_bytes = password.encode("utf-8")
        salt_bytes = bytes.fromhex(salt)
        derived = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 10_000)
        return derived.hex(), salt

    @staticmethod
    def _verify_password(password: str, salt: str, expected_hash: str) -> bool:
        if not password or not salt or not expected_hash:
            return False
        pwd_bytes = password.encode("utf-8")
        salt_bytes = bytes.fromhex(salt)
        computed = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 10_000).hex()
        return hmac.compare_digest(computed, expected_hash)

    def register_user(self, admin_context: dict, user_id: str, username: str,
                      password: str, full_name: str, email: str, role: str) -> int:
        """Register a recruiter, hiring manager, or administrator account."""
        if admin_context and admin_context.get("role") != "admin":
            raise AccessControlError("Only administrators can register new staff accounts.")

        user_id = user_id.strip().upper()
        username = username.strip().lower()
        full_name = full_name.strip()
        email = email.strip().lower()
        role = role.strip().lower()

        if role not in ("admin", "recruiter", "hiring_manager"):
            raise ValueError("Role must be 'admin', 'recruiter', or 'hiring_manager'.")

        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("Invalid email format.")

        pwd_hash, salt = self._hash_password(password)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (user_id, username, password_hash, salt, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, username, pwd_hash, salt, full_name, email, role),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("User ID, username, or email is already registered.")
            raise
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticate user and return user session context."""
        username = username.strip().lower()
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not row:
                raise ValueError("Invalid username or password.")
            u = dict(row)
            if not self._verify_password(password, u["salt"], u["password_hash"]):
                raise ValueError("Invalid username or password.")
            return {
                "id": u["id"],
                "user_id": u["user_id"],
                "username": u["username"],
                "full_name": u["full_name"],
                "email": u["email"],
                "role": u["role"],
            }
        finally:
            conn.close()

    # ==================== Company Management ====================

    def register_company(self, user_context: dict, company_code: str, name: str,
                         industry: str, contact_person: str, email: str,
                         phone: str, location: str, website: str = None) -> int:
        """Register a client employer company. Requires recruiter or admin role."""
        if user_context.get("role") not in ("admin", "recruiter"):
            raise AccessControlError("Only recruiters and administrators can register companies.")

        company_code = company_code.strip().upper()
        name = name.strip()
        industry = industry.strip()
        contact_person = contact_person.strip()
        email = email.strip().lower()
        phone = phone.strip()
        location = location.strip()

        if not company_code or not name or not industry:
            raise ValueError("Company code, name, and industry are required.")

        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError("Invalid contact email format.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO companies (company_code, name, industry, contact_person, email, phone, location, website)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (company_code, name, industry, contact_person, email, phone, location, website),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Company code '{company_code}' is already registered.")
            raise
        finally:
            conn.close()

    def list_companies(self) -> list[dict]:
        """List all registered companies."""
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM companies ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Job Vacancies ====================

    def create_vacancy(self, user_context: dict, vacancy_code: str, company_code: str,
                       title: str, department: str, employment_type: str,
                       location: str, min_years_experience: float, required_skills: str,
                       job_description: str, requirements: str,
                       salary_min: float = 0.0, salary_max: float = 0.0,
                       closing_date: str = None) -> int:
        """Create a job vacancy with role, skills, and experience criteria."""
        if user_context.get("role") not in ("admin", "recruiter"):
            raise AccessControlError("Only recruiters or administrators can create job vacancies.")

        vacancy_code = vacancy_code.strip().upper()
        title = title.strip()
        department = department.strip()
        employment_type = employment_type.strip()
        location = location.strip()
        required_skills = required_skills.strip()
        job_description = job_description.strip()
        requirements = requirements.strip()

        valid_emp_types = ("Full-time", "Part-time", "Contract", "Remote", "Hybrid")
        if employment_type not in valid_emp_types:
            raise ValueError(f"Employment type must be one of: {', '.join(valid_emp_types)}")

        if min_years_experience < 0:
            raise ValueError("Minimum years of experience cannot be negative.")
        if salary_max < salary_min:
            raise ValueError("Maximum salary cannot be less than minimum salary.")

        conn = self._get_connection()
        try:
            with conn:
                company = conn.execute(
                    "SELECT id FROM companies WHERE company_code = ?", (company_code.strip().upper(),)
                ).fetchone()
                if not company:
                    raise ValueError(f"Company with code '{company_code}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO vacancies (
                        vacancy_code, company_id, title, department, employment_type,
                        location, salary_min, salary_max, min_years_experience,
                        required_skills, job_description, requirements, status,
                        created_by, closing_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?)
                    """,
                    (
                        vacancy_code, company["id"], title, department, employment_type,
                        location, salary_min, salary_max, min_years_experience,
                        required_skills, job_description, requirements,
                        user_context.get("id"), closing_date
                    ),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Vacancy code '{vacancy_code}' already exists.")
            raise
        finally:
            conn.close()

    def list_vacancies(self, status: str = None) -> list[dict]:
        """List vacancies with company details, optionally filtered by status."""
        conn = self._get_connection()
        try:
            sql = """
            SELECT v.*, c.name as company_name, c.company_code
            FROM vacancies v
            JOIN companies c ON v.company_id = c.id
            """
            params = []
            if status:
                sql += " WHERE v.status = ?"
                params.append(status)
            sql += " ORDER BY v.created_at DESC"

            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Candidate Registration ====================

    def register_candidate(self, full_name: str, email: str, phone: str,
                           location: str, current_title: str, years_experience: float,
                           skills: str, education_level: str = None,
                           linkedin_portfolio: str = None) -> str:
        """Register a job applicant profile."""
        full_name = full_name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        location = location.strip()
        current_title = current_title.strip() if current_title else "Job Seeker"
        skills = skills.strip()

        if not full_name or not email or not phone:
            raise ValueError("Full name, email, and phone number are required.")

        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError(f"Invalid email address: {email}")

        if years_experience < 0:
            raise ValueError("Years of experience cannot be negative.")

        today_year = datetime.now().year
        seq = secrets.randbelow(9000) + 1000
        candidate_code = f"CND-{today_year}-{seq}"

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO candidates (
                        candidate_code, full_name, email, phone, location,
                        current_title, years_experience, skills, education_level,
                        linkedin_portfolio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate_code, full_name, email, phone, location,
                        current_title, years_experience, skills, education_level,
                        linkedin_portfolio
                    ),
                )
                return candidate_code
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Candidate with email '{email}' is already registered.")
            raise
        finally:
            conn.close()

    def get_candidate(self, candidate_code: str) -> dict:
        """Retrieve candidate profile by code."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM candidates WHERE candidate_code = ?", (candidate_code.strip().upper(),)
            ).fetchone()
            if not row:
                raise ValueError(f"Candidate '{candidate_code}' not found.")
            return dict(row)
        finally:
            conn.close()

    # ==================== Candidate Search (Skills & Experience) ====================

    def search_candidates(self, skill_query: str = None, min_years_exp: float = None,
                          location: str = None) -> list[dict]:
        """
        Search candidates by skills, years of experience, and location.
        Adheres to ethical recruitment principles: matching is strictly based on
        objective technical skills, verified experience, and qualifications.
        """
        conn = self._get_connection()
        try:
            clauses = []
            params = []

            if min_years_exp is not None and min_years_exp > 0:
                clauses.append("years_experience >= ?")
                params.append(min_years_exp)

            if location and location.strip():
                clauses.append("lower(location) LIKE ?")
                params.append(f"%{location.strip().lower()}%")

            where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(f"SELECT * FROM candidates {where_str} ORDER BY years_experience DESC", params).fetchall()

            results = [dict(r) for r in rows]

            # In-memory keyword filtering for multiple skills
            if skill_query and skill_query.strip():
                tokens = [t.strip().lower() for t in re.split(r"[,/|; ]+", skill_query) if t.strip()]
                filtered = []
                for cand in results:
                    cand_skills = cand.get("skills", "").lower()
                    # Check if any or all skill tokens match
                    matched_count = sum(1 for token in tokens if token in cand_skills)
                    if matched_count > 0:
                        cand["matched_skills_count"] = matched_count
                        filtered.append(cand)
                filtered.sort(key=lambda x: (x.get("matched_skills_count", 0), x.get("years_experience", 0)), reverse=True)
                return filtered

            return results
        finally:
            conn.close()

    # ==================== Job Applications & CV Uploads ====================

    def apply_to_vacancy(self, candidate_code: str, vacancy_code: str, cover_letter: str = None) -> str:
        """
        Accept and record a job application.
        Prevents duplicate applications for the same vacancy.
        Allocates a unique application reference number.
        Initial status is 'Submitted'.
        """
        candidate_code = candidate_code.strip().upper()
        vacancy_code = vacancy_code.strip().upper()

        conn = self._get_connection()
        try:
            with conn:
                cand = conn.execute("SELECT id FROM candidates WHERE candidate_code = ?", (candidate_code,)).fetchone()
                if not cand:
                    raise ValueError(f"Candidate code '{candidate_code}' does not exist.")

                vac = conn.execute("SELECT id, status FROM vacancies WHERE vacancy_code = ?", (vacancy_code,)).fetchone()
                if not vac:
                    raise ValueError(f"Vacancy code '{vacancy_code}' does not exist.")

                if vac["status"] != "Open":
                    raise ValueError(f"Vacancy '{vacancy_code}' is currently {vac['status']} and not accepting applications.")

                # Check for duplicate application
                existing = conn.execute(
                    "SELECT application_ref FROM applications WHERE vacancy_id = ? AND candidate_id = ?",
                    (vac["id"], cand["id"]),
                ).fetchone()
                if existing:
                    raise ValueError(
                        f"Duplicate application! Candidate {candidate_code} has already applied to vacancy {vacancy_code} (Ref: {existing['application_ref']})."
                    )

                today_year = datetime.now().year
                seq = secrets.randbelow(9000) + 1000
                application_ref = f"APP-{today_year}-{seq}"

                cursor = conn.execute(
                    """
                    INSERT INTO applications (application_ref, vacancy_id, candidate_id, status, cover_letter)
                    VALUES (?, ?, ?, 'Submitted', ?)
                    """,
                    (application_ref, vac["id"], cand["id"], cover_letter),
                )
                app_id = cursor.lastrowid

                # Initial status transition log
                conn.execute(
                    """
                    INSERT INTO application_history (application_id, old_status, new_status, notes)
                    VALUES (?, NULL, 'Submitted', 'Application submitted by candidate')
                    """,
                    (app_id,),
                )

                return application_ref
        finally:
            conn.close()

    def upload_candidate_cv(self, application_ref: str, filename: str, content_bytes: bytes) -> dict:
        """
        Upload candidate CV document into local storage and link to application.
        Validates allowed file types (pdf, docx, doc, txt) and max size (5 MB).
        """
        application_ref = application_ref.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                app = conn.execute(
                    """
                    SELECT a.id, a.candidate_id, c.candidate_code
                    FROM applications a
                    JOIN candidates c ON a.candidate_id = c.id
                    WHERE a.application_ref = ?
                    """,
                    (application_ref,),
                ).fetchone()
                if not app:
                    raise ValueError(f"Application '{application_ref}' not found.")

                cand_code = app["candidate_code"]
                stored_meta = self.storage.save_cv_bytes(cand_code, filename, content_bytes)

                file_ref = f"CV-{secrets.token_hex(4).upper()}"
                cursor = conn.execute(
                    """
                    INSERT INTO cv_documents (
                        file_ref, candidate_id, original_filename, stored_filename,
                        file_path, file_type, file_size_bytes, checksum_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_ref, app["candidate_id"], stored_meta["original_filename"],
                        stored_meta["stored_filename"], stored_meta["file_path"],
                        stored_meta["file_type"], stored_meta["file_size_bytes"],
                        stored_meta["checksum_sha256"]
                    ),
                )
                cv_id = cursor.lastrowid

                # Link to application
                conn.execute(
                    "UPDATE applications SET cv_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (cv_id, app["id"]),
                )

                stored_meta["cv_id"] = cv_id
                stored_meta["file_ref"] = file_ref
                return stored_meta
        finally:
            conn.close()

    # ==================== Application Status Tracking & History ====================

    def update_application_status(self, user_context: dict, application_ref: str,
                                  new_status: str, notes: str = None) -> bool:
        """
        Transition application through statuses:
        'Submitted', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Accepted', 'Rejected'.
        Maintains full status history with actor and notes.
        """
        if user_context.get("role") not in ("admin", "recruiter", "hiring_manager"):
            raise AccessControlError("Authorized recruiter, hiring manager, or administrator role required.")

        application_ref = application_ref.strip().upper()
        if new_status not in VALID_APPLICATION_STATUSES:
            raise ValueError(f"Invalid status: '{new_status}'. Must be one of: {', '.join(VALID_APPLICATION_STATUSES)}")

        conn = self._get_connection()
        try:
            with conn:
                app = conn.execute(
                    "SELECT id, status FROM applications WHERE application_ref = ?", (application_ref,)
                ).fetchone()
                if not app:
                    raise ValueError(f"Application '{application_ref}' not found.")

                old_status = app["status"]
                conn.execute(
                    "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_status, app["id"]),
                )

                conn.execute(
                    """
                    INSERT INTO application_history (application_id, old_status, new_status, changed_by_user_id, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (app["id"], old_status, new_status, user_context.get("id"), notes),
                )
                return True
        finally:
            conn.close()

    def get_application_history(self, application_ref: str) -> list[dict]:
        """Retrieve complete status transition timeline for an application."""
        application_ref = application_ref.strip().upper()
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT h.old_status, h.new_status, h.notes, h.timestamp,
                       u.full_name as actor_name, u.role as actor_role
                FROM application_history h
                JOIN applications a ON h.application_id = a.id
                LEFT JOIN users u ON h.changed_by_user_id = u.id
                WHERE a.application_ref = ?
                ORDER BY h.timestamp ASC
                """,
                (application_ref,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_application_details(self, application_ref: str) -> dict:
        """Retrieve full details of an application including candidate, vacancy, and CV."""
        application_ref = application_ref.strip().upper()
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT a.*, c.candidate_code, c.full_name as candidate_name, c.email as candidate_email,
                       c.phone as candidate_phone, c.years_experience, c.skills, c.current_title,
                       v.vacancy_code, v.title as job_title, v.department, comp.name as company_name,
                       cv.original_filename, cv.file_path, cv.file_type, cv.file_size_bytes
                FROM applications a
                JOIN candidates c ON a.candidate_id = c.id
                JOIN vacancies v ON a.vacancy_id = v.id
                JOIN companies comp ON v.company_id = comp.id
                LEFT JOIN cv_documents cv ON a.cv_id = cv.id
                WHERE a.application_ref = ?
                """,
                (application_ref,),
            ).fetchone()
            if not row:
                raise ValueError(f"Application '{application_ref}' not found.")

            app_data = dict(row)

            # Get history
            history_rows = conn.execute(
                """
                SELECT h.old_status, h.new_status, h.notes, h.timestamp,
                       u.full_name as actor_name, u.role as actor_role
                FROM application_history h
                JOIN applications a ON h.application_id = a.id
                LEFT JOIN users u ON h.changed_by_user_id = u.id
                WHERE a.application_ref = ?
                ORDER BY h.timestamp ASC
                """,
                (application_ref,),
            ).fetchall()
            app_data["history"] = [dict(h) for h in history_rows]

            # Get scheduled interviews
            interviews = conn.execute(
                "SELECT * FROM interviews WHERE application_id = ? ORDER BY scheduled_datetime ASC",
                (app_data["id"],),
            ).fetchall()
            app_data["interviews"] = [dict(i) for i in interviews]
            return app_data
        finally:
            conn.close()

    # ==================== Interview Scheduling & Feedback ====================

    def schedule_interview(self, user_context: dict, application_ref: str, round_name: str,
                           scheduled_datetime: str, interviewer_name: str,
                           meeting_link_or_location: str) -> str:
        """
        Schedule an interview round for a candidate.
        Automatically advances application status to 'Interview Scheduled'.
        """
        if user_context.get("role") not in ("admin", "recruiter"):
            raise AccessControlError("Only recruiters or administrators can schedule interviews.")

        application_ref = application_ref.strip().upper()
        valid_rounds = ("Phone Screen", "Technical Interview", "Behavioral Interview", "Panel Interview", "Final Round")
        if round_name not in valid_rounds:
            raise ValueError(f"Round must be one of: {', '.join(valid_rounds)}")

        conn = self._get_connection()
        try:
            with conn:
                app = conn.execute("SELECT id, status FROM applications WHERE application_ref = ?", (application_ref,)).fetchone()
                if not app:
                    raise ValueError(f"Application '{application_ref}' not found.")

                today_year = datetime.now().year
                seq = secrets.randbelow(9000) + 1000
                interview_ref = f"INT-{today_year}-{seq}"

                conn.execute(
                    """
                    INSERT INTO interviews (
                        interview_ref, application_id, round_name, scheduled_datetime,
                        interviewer_name, interviewer_user_id, meeting_link_or_location, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Scheduled')
                    """,
                    (
                        interview_ref, app["id"], round_name, scheduled_datetime.strip(),
                        interviewer_name.strip(), user_context.get("id"), meeting_link_or_location.strip()
                    ),
                )

                # Transition application status to Interview Scheduled
                old_status = app["status"]
                conn.execute(
                    "UPDATE applications SET status = 'Interview Scheduled', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (app["id"],),
                )
                conn.execute(
                    """
                    INSERT INTO application_history (application_id, old_status, new_status, changed_by_user_id, notes)
                    VALUES (?, ?, 'Interview Scheduled', ?, ?)
                    """,
                    (app["id"], old_status, user_context.get("id"), f"Scheduled {round_name} on {scheduled_datetime}"),
                )

                return interview_ref
        finally:
            conn.close()

    def record_interview_feedback(self, user_context: dict, interview_ref: str,
                                  rating_overall: int, technical_score: int,
                                  communication_score: int, problem_solving_score: int,
                                  strengths: str, areas_for_improvement: str,
                                  recommendation: str, notes: str = None) -> int:
        """
        Record structured evaluation feedback for a completed interview.
        Validates scores (1-5) and recommendations.
        """
        interview_ref = interview_ref.strip().upper()
        for score, name in [
            (rating_overall, "Overall rating"), (technical_score, "Technical score"),
            (communication_score, "Communication score"), (problem_solving_score, "Problem solving score")
        ]:
            if score < 1 or score > 5:
                raise ValueError(f"{name} must be an integer between 1 and 5.")

        valid_recs = ("Strong Hire", "Hire", "Hold", "Reject")
        if recommendation not in valid_recs:
            raise ValueError(f"Recommendation must be one of: {', '.join(valid_recs)}")

        conn = self._get_connection()
        try:
            with conn:
                interview = conn.execute("SELECT id FROM interviews WHERE interview_ref = ?", (interview_ref,)).fetchone()
                if not interview:
                    raise ValueError(f"Interview '{interview_ref}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO interview_feedback (
                        interview_id, interviewer_user_id, interviewer_name,
                        rating_overall, technical_score, communication_score,
                        problem_solving_score, strengths, areas_for_improvement,
                        recommendation, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interview["id"], user_context.get("id"), user_context.get("full_name", "Interviewer"),
                        rating_overall, technical_score, communication_score, problem_solving_score,
                        strengths.strip(), areas_for_improvement.strip(), recommendation, notes
                    ),
                )

                # Mark interview completed
                conn.execute("UPDATE interviews SET status = 'Completed' WHERE id = ?", (interview["id"],))
                return cursor.lastrowid
        finally:
            conn.close()

    # ==================== Recruitment Reporting ====================

    def generate_recruitment_reports(self) -> dict:
        """
        Generate comprehensive recruitment pipeline analytics and company statistics.
        """
        conn = self._get_connection()
        try:
            total_companies = conn.execute("SELECT count(*) FROM companies").fetchone()[0]
            total_vacancies = conn.execute("SELECT count(*) FROM vacancies").fetchone()[0]
            total_candidates = conn.execute("SELECT count(*) FROM candidates").fetchone()[0]
            total_applications = conn.execute("SELECT count(*) FROM applications").fetchone()[0]

            # Application Funnel Status Breakdown
            status_counts = conn.execute(
                """
                SELECT status, count(*) as count
                FROM applications
                GROUP BY status
                """
            ).fetchall()
            status_dict = {row["status"]: row["count"] for row in status_counts}

            # Funnel order
            funnel = [
                {"stage": "Submitted", "count": status_dict.get("Submitted", 0)},
                {"stage": "Under Review", "count": status_dict.get("Under Review", 0)},
                {"stage": "Shortlisted", "count": status_dict.get("Shortlisted", 0)},
                {"stage": "Interview Scheduled", "count": status_dict.get("Interview Scheduled", 0)},
                {"stage": "Accepted", "count": status_dict.get("Accepted", 0)},
                {"stage": "Rejected", "count": status_dict.get("Rejected", 0)},
            ]

            # Vacancy specific pipeline breakdown
            vacancy_breakdowns = conn.execute(
                """
                SELECT v.vacancy_code, v.title, c.name as company_name, v.status as vacancy_status,
                       count(a.id) as total_applicants,
                       sum(CASE WHEN a.status = 'Accepted' THEN 1 ELSE 0 END) as accepted_count,
                       sum(CASE WHEN a.status = 'Interview Scheduled' THEN 1 ELSE 0 END) as interview_count
                FROM vacancies v
                JOIN companies c ON v.company_id = c.id
                LEFT JOIN applications a ON v.id = a.vacancy_id
                GROUP BY v.id
                ORDER BY total_applicants DESC
                """
            ).fetchall()

            # Interview Feedback averages
            feedback_stats = conn.execute(
                """
                SELECT count(*) as total_evaluations,
                       coalesce(avg(rating_overall), 0.0) as avg_rating,
                       coalesce(avg(technical_score), 0.0) as avg_technical,
                       coalesce(avg(communication_score), 0.0) as avg_communication
                FROM interview_feedback
                """
            ).fetchone()

            return {
                "total_companies": total_companies,
                "total_vacancies": total_vacancies,
                "total_candidates": total_candidates,
                "total_applications": total_applications,
                "pipeline_funnel": funnel,
                "vacancy_breakdowns": [dict(v) for v in vacancy_breakdowns],
                "feedback_stats": dict(feedback_stats),
            }
        finally:
            conn.close()
