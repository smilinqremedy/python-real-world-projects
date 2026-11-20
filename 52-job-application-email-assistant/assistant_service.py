"""
Service coordinator for Job Application Email Assistant.
"""
from datetime import datetime
import os
from database import get_connection, init_db
from email_generator import EmailGenerator
from email_sender import EmailSender


class EmailAssistantService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self.sender = EmailSender()
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Company & Vacancy Operations ====================

    def add_company(self, name: str, recruitment_email: str, industry: str = None, website: str = None, notes: str = None) -> int:
        name = name.strip()
        recruitment_email = recruitment_email.strip().lower()
        if not name or not recruitment_email:
            raise ValueError("Company name and recruitment email are required.")

        self.sender.validate_email(recruitment_email)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO companies (name, recruitment_email, industry, website, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, recruitment_email, industry, website, notes),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def list_companies(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM companies ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_vacancy(self, company_id: int, title: str, job_url: str = None, salary_range: str = None) -> int:
        title = title.strip()
        if not title:
            raise ValueError("Job title is required.")

        conn = self._get_connection()
        try:
            with conn:
                comp = conn.execute("SELECT id FROM companies WHERE id = ?", (company_id,)).fetchone()
                if not comp:
                    raise ValueError(f"Company ID {company_id} does not exist.")

                cursor = conn.execute(
                    """
                    INSERT INTO vacancies (company_id, title, job_url, salary_range, status)
                    VALUES (?, ?, ?, ?, 'Saved')
                    """,
                    (company_id, title, job_url, salary_range),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def list_vacancies(self, status: str = None) -> list[dict]:
        conn = self._get_connection()
        try:
            sql = """
            SELECT v.*, c.name as company_name, c.recruitment_email
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

    # ==================== Templates ====================

    def list_templates(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM email_templates ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_template(self, template_id: int) -> dict:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM email_templates WHERE id = ?", (template_id,)).fetchone()
            if not row:
                raise ValueError(f"Template with ID {template_id} not found.")
            return dict(row)
        finally:
            conn.close()

    # ==================== Preview & Confirmation Workflow ====================

    def preview_application(self, vacancy_id: int, template_id: int, candidate_profile: dict, cv_path: str = None) -> dict:
        """
        Generate complete preview of the application email before sending.
        Does NOT transmit anything over the network.
        """
        conn = self._get_connection()
        try:
            vac = conn.execute(
                """
                SELECT v.*, c.name as company_name, c.recruitment_email
                FROM vacancies v
                JOIN companies c ON v.company_id = c.id
                WHERE v.id = ?
                """,
                (vacancy_id,),
            ).fetchone()
            if not vac:
                raise ValueError(f"Vacancy ID {vacancy_id} not found.")

            tpl = self.get_template(template_id)

            ctx = candidate_profile.copy()
            ctx["company"] = vac["company_name"]
            ctx["job_title"] = vac["title"]
            ctx["recipient_email"] = vac["recruitment_email"]

            rendered = EmailGenerator.generate_application_email(tpl["subject_template"], tpl["body_template"], ctx)

            # Validate CV attachment if provided
            cv_filename = None
            if cv_path:
                if not os.path.exists(cv_path):
                    raise FileNotFoundError(f"CV document not found at: {cv_path}")
                cv_filename = os.path.basename(cv_path)

            return {
                "vacancy_id": vacancy_id,
                "company_name": vac["company_name"],
                "recipient_email": vac["recruitment_email"],
                "job_title": vac["title"],
                "template_name": tpl["name"],
                "subject": rendered["subject"],
                "body": rendered["body"],
                "cv_path": cv_path,
                "cv_filename": cv_filename,
                "preview_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        finally:
            conn.close()

    def send_confirmed_application(self, preview_data: dict, user_confirmed: bool, dry_run: bool = False) -> dict:
        """
        MANDATORY SAFETY GATE: Requires explicit user confirmation before sending.
        Records sent application in database and updates vacancy status.
        """
        if not user_confirmed:
            raise PermissionError("Action blocked: User confirmation is strictly required before sending emails.")

        recipient = preview_data["recipient_email"]
        subject = preview_data["subject"]
        body = preview_data["body"]
        cv_path = preview_data.get("cv_path")

        # Dispatch via EmailSender
        dispatch_res = self.sender.send(recipient, subject, body, cv_path, dry_run=dry_run)

        # Record into sent_applications
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO sent_applications (
                        vacancy_id, company_name, recipient_email, job_title,
                        subject, body, cv_filename, cv_path, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Sent', ?)
                    """,
                    (
                        preview_data.get("vacancy_id"), preview_data["company_name"],
                        recipient, preview_data["job_title"], subject, body,
                        preview_data.get("cv_filename"), cv_path,
                        f"Dispatched in mode: {dispatch_res.get('mode', 'Sent')}"
                    ),
                )
                app_id = cursor.lastrowid

                # Update vacancy status
                if preview_data.get("vacancy_id"):
                    conn.execute("UPDATE vacancies SET status = 'Applied' WHERE id = ?", (preview_data["vacancy_id"],))

                dispatch_res["application_id"] = app_id
                return dispatch_res
        finally:
            conn.close()

    def update_application_status(self, application_id: int, new_status: str, notes: str = None) -> bool:
        valid_statuses = ("Sent", "Follow-up Needed", "Interviewing", "Rejected", "Offer")
        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE sent_applications SET status = ?, notes = coalesce(?, notes) WHERE id = ?",
                    (new_status, notes, application_id),
                )
                return True
        finally:
            conn.close()

    def get_applications_report(self) -> dict:
        conn = self._get_connection()
        try:
            total_sent = conn.execute("SELECT count(*) FROM sent_applications").fetchone()[0]

            by_status = conn.execute(
                "SELECT status, count(*) as count FROM sent_applications GROUP BY status"
            ).fetchall()

            recent = conn.execute(
                "SELECT * FROM sent_applications ORDER BY sent_at DESC LIMIT 10"
            ).fetchall()

            return {
                "total_applications": total_sent,
                "by_status": [dict(s) for s in by_status],
                "recent_applications": [dict(r) for r in recent],
            }
        finally:
            conn.close()
