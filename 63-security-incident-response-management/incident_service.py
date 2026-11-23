"""
Service layer for Security Incident Response Management.
Manages incident lifecycle, role-based access control (RBAC),
investigator assignment, evidence documentation, and audit logging.
"""
from datetime import datetime
import secrets
from typing import Optional, Dict, List, Any
from database import get_connection, init_db


class RBACPermissionError(Exception):
    """Raised when an operation is disallowed by user role permissions."""
    pass


class IncidentWorkflowError(Exception):
    """Raised when an invalid status transition is attempted."""
    pass


class IncidentResponseService:
    LIFECYCLE_ORDER = [
        "Reported",
        "Investigating",
        "Contained",
        "Eradicated",
        "Recovered",
        "Closed"
    ]

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== User & RBAC Management ====================

    def create_user(self, username: str, full_name: str, role: str, email: str) -> int:
        username = username.strip().lower()
        full_name = full_name.strip()
        role = role.strip().capitalize()
        email = email.strip().lower()

        if role not in ("Analyst", "Lead", "Admin"):
            raise ValueError("Role must be one of: 'Analyst', 'Lead', 'Admin'.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO users (username, full_name, role, email) VALUES (?, ?, ?, ?)",
                    (username, full_name, role, email)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise ValueError(f"Username '{username}' or email already exists.")
            raise
        finally:
            conn.close()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_users(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM users ORDER BY full_name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Incident Operations ====================

    def create_incident(self, title: str, description: str, severity: str,
                        category: str, created_by_id: int) -> str:
        title = title.strip()
        description = description.strip()
        severity = severity.strip().capitalize()

        valid_sevs = ("Low", "Medium", "High", "Critical")
        if severity not in valid_sevs:
            raise ValueError(f"Severity must be one of: {', '.join(valid_sevs)}")

        valid_cats = ("Phishing", "Malware", "Data Breach", "Unauthorized Access", "DDoS", "Insider Threat", "System Compromise")
        if category not in valid_cats:
            raise ValueError(f"Category must be one of: {', '.join(valid_cats)}")

        conn = self._get_connection()
        try:
            with conn:
                user = conn.execute("SELECT id FROM users WHERE id = ?", (created_by_id,)).fetchone()
                if not user:
                    raise ValueError(f"User ID {created_by_id} does not exist.")

                year_tag = datetime.now().strftime("%Y")
                seq = secrets.randbelow(9000) + 1000
                inc_ref = f"INC-{year_tag}-{seq}"

                cursor = conn.execute(
                    """
                    INSERT INTO incidents (incident_ref, title, description, severity, category, status, created_by_id)
                    VALUES (?, ?, ?, ?, ?, 'Reported', ?)
                    """,
                    (inc_ref, title, description, severity, category, created_by_id)
                )
                inc_id = cursor.lastrowid

                # Initial audit trail
                conn.execute(
                    """
                    INSERT INTO audit_logs (incident_id, user_id, action, previous_state, new_state)
                    VALUES (?, ?, 'INCIDENT_CREATED', NULL, 'Reported')
                    """,
                    (inc_id, created_by_id)
                )
                return inc_ref
        finally:
            conn.close()

    def assign_lead_investigator(self, incident_ref: str, lead_user_id: int, acting_user_id: int) -> bool:
        """Assign or reassign lead analyst. Requires Lead or Admin acting user."""
        conn = self._get_connection()
        try:
            with conn:
                actor = conn.execute("SELECT role FROM users WHERE id = ?", (acting_user_id,)).fetchone()
                if not actor or actor["role"] not in ("Lead", "Admin"):
                    raise RBACPermissionError("Only a 'Lead' or 'Admin' can assign lead investigators.")

                target_lead = conn.execute("SELECT full_name FROM users WHERE id = ?", (lead_user_id,)).fetchone()
                if not target_lead:
                    raise ValueError(f"Lead user ID {lead_user_id} not found.")

                inc = conn.execute("SELECT id, lead_analyst_id FROM incidents WHERE incident_ref = ?", (incident_ref,)).fetchone()
                if not inc:
                    raise ValueError(f"Incident '{incident_ref}' not found.")

                prev_lead = inc["lead_analyst_id"]
                conn.execute(
                    "UPDATE incidents SET lead_analyst_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (lead_user_id, inc["id"])
                )

                conn.execute(
                    """
                    INSERT INTO audit_logs (incident_id, user_id, action, previous_state, new_state)
                    VALUES (?, ?, 'ASSIGN_LEAD', ?, ?)
                    """,
                    (inc["id"], acting_user_id, str(prev_lead), str(lead_user_id))
                )
                return True
        finally:
            conn.close()

    def transition_status(self, incident_ref: str, new_status: str, acting_user_id: int,
                          resolution_note: Optional[str] = None) -> bool:
        """
        Transition incident lifecycle status.
        Enforces lifecycle order and RBAC rules (closure requires Lead or Admin).
        """
        new_status = new_status.strip().capitalize()
        if new_status not in self.LIFECYCLE_ORDER:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(self.LIFECYCLE_ORDER)}")

        conn = self._get_connection()
        try:
            with conn:
                actor = conn.execute("SELECT id, role FROM users WHERE id = ?", (acting_user_id,)).fetchone()
                if not actor:
                    raise ValueError("Acting user not found.")

                inc = conn.execute("SELECT * FROM incidents WHERE incident_ref = ?", (incident_ref,)).fetchone()
                if not inc:
                    raise ValueError(f"Incident '{incident_ref}' not found.")

                current_status = inc["status"]
                curr_idx = self.LIFECYCLE_ORDER.index(current_status)
                new_idx = self.LIFECYCLE_ORDER.index(new_status)

                if current_status == "Closed":
                    raise IncidentWorkflowError("Incident is already Closed and cannot transition further.")

                if new_idx <= curr_idx and new_status != current_status:
                    raise IncidentWorkflowError(f"Cannot revert status backwards from '{current_status}' to '{new_status}'.")

                # Skipping stages validation: cannot jump from Reported straight to Closed without Contained
                if new_status == "Closed" and current_status not in ("Recovered", "Eradicated"):
                    raise IncidentWorkflowError(
                        f"Cannot close incident directly from '{current_status}'. Incident must be Contained/Eradicated/Recovered first."
                    )

                # Closing requires Lead or Admin
                if new_status == "Closed" and actor["role"] not in ("Lead", "Admin"):
                    raise RBACPermissionError("Only a 'Lead' or 'Admin' is authorized to Close an incident.")

                closed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "Closed" else None

                conn.execute(
                    """
                    UPDATE incidents
                    SET status = ?, updated_at = CURRENT_TIMESTAMP, closed_at = coalesce(?, closed_at)
                    WHERE id = ?
                    """,
                    (new_status, closed_at, inc["id"])
                )

                if resolution_note:
                    conn.execute(
                        "INSERT INTO incident_notes (incident_id, user_id, note_text) VALUES (?, ?, ?)",
                        (inc["id"], acting_user_id, f"[{new_status.upper()}] {resolution_note}")
                    )

                conn.execute(
                    """
                    INSERT INTO audit_logs (incident_id, user_id, action, previous_state, new_state)
                    VALUES (?, ?, 'STATUS_TRANSITION', ?, ?)
                    """,
                    (inc["id"], acting_user_id, current_status, new_status)
                )
                return True
        finally:
            conn.close()

    def add_note(self, incident_ref: str, user_id: int, note_text: str) -> int:
        note_text = note_text.strip()
        if not note_text:
            raise ValueError("Note text cannot be empty.")

        conn = self._get_connection()
        try:
            with conn:
                inc = conn.execute("SELECT id FROM incidents WHERE incident_ref = ?", (incident_ref,)).fetchone()
                if not inc:
                    raise ValueError(f"Incident '{incident_ref}' not found.")

                cursor = conn.execute(
                    "INSERT INTO incident_notes (incident_id, user_id, note_text) VALUES (?, ?, ?)",
                    (inc["id"], user_id, note_text)
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def add_evidence(self, incident_ref: str, user_id: int, evidence_type: str,
                     reference_locator: str, description: str, sha256: Optional[str] = None) -> int:
        valid_types = ('Log', 'File Hash', 'Network PCAP', 'Memory Dump', 'Disk Image', 'Screenshot', 'Email Artifact')
        if evidence_type not in valid_types:
            raise ValueError(f"Evidence type must be one of: {', '.join(valid_types)}")

        conn = self._get_connection()
        try:
            with conn:
                inc = conn.execute("SELECT id FROM incidents WHERE incident_ref = ?", (incident_ref,)).fetchone()
                if not inc:
                    raise ValueError(f"Incident '{incident_ref}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO evidence_records (incident_id, evidence_type, reference_locator, description, sha256, added_by_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (inc["id"], evidence_type, reference_locator.strip(), description.strip(), sha256.strip() if sha256 else None, user_id)
                )
                rec_id = cursor.lastrowid

                conn.execute(
                    """
                    INSERT INTO audit_logs (incident_id, user_id, action, previous_state, new_state)
                    VALUES (?, ?, 'EVIDENCE_ATTACHED', NULL, ?)
                    """,
                    (inc["id"], user_id, f"{evidence_type}: {reference_locator}")
                )
                return rec_id
        finally:
            conn.close()

    def get_incident_details(self, incident_ref: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            inc = conn.execute(
                """
                SELECT i.*,
                       u_lead.full_name as lead_analyst_name, u_lead.email as lead_analyst_email,
                       u_creator.full_name as creator_name
                FROM incidents i
                LEFT JOIN users u_lead ON i.lead_analyst_id = u_lead.id
                JOIN users u_creator ON i.created_by_id = u_creator.id
                WHERE i.incident_ref = ?
                """,
                (incident_ref,)
            ).fetchone()
            if not inc:
                raise ValueError(f"Incident '{incident_ref}' not found.")

            data = dict(inc)

            notes = conn.execute(
                """
                SELECT n.*, u.full_name as author_name, u.role as author_role
                FROM incident_notes n
                JOIN users u ON n.user_id = u.id
                WHERE n.incident_id = ?
                ORDER BY n.created_at ASC
                """,
                (data["id"],)
            ).fetchall()
            data["notes"] = [dict(n) for n in notes]

            evidence = conn.execute(
                """
                SELECT e.*, u.full_name as added_by_name
                FROM evidence_records e
                JOIN users u ON e.added_by_id = u.id
                WHERE e.incident_id = ?
                ORDER BY e.created_at ASC
                """,
                (data["id"],)
            ).fetchall()
            data["evidence"] = [dict(e) for e in evidence]

            audit = conn.execute(
                """
                SELECT a.*, u.full_name as actor_name, u.role as actor_role
                FROM audit_logs a
                JOIN users u ON a.user_id = u.id
                WHERE a.incident_id = ?
                ORDER BY a.timestamp ASC
                """,
                (data["id"],)
            ).fetchall()
            data["timeline"] = [dict(a) for a in audit]

            return data
        finally:
            conn.close()

    def get_incident_metrics(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT count(*) FROM incidents").fetchone()[0]
            status_counts = conn.execute("SELECT status, count(*) as count FROM incidents GROUP BY status").fetchall()
            sev_counts = conn.execute("SELECT severity, count(*) as count FROM incidents GROUP BY severity").fetchall()
            cat_counts = conn.execute("SELECT category, count(*) as count FROM incidents GROUP BY category").fetchall()

            return {
                "total_incidents": total,
                "by_status": {r["status"]: r["count"] for r in status_counts},
                "by_severity": {r["severity"]: r["count"] for r in sev_counts},
                "by_category": {r["category"]: r["count"] for r in cat_counts},
            }
        finally:
            conn.close()
