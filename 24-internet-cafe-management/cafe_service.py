"""
Business logic and session tracking for Internet Cafe Management System.
"""

from datetime import datetime, date
import math
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class CafeService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_computer(self, code: str, ip_address: str, specs: str, hourly_rate: float) -> Dict[str, Any]:
        c_code = code.strip().upper()
        ip = ip_address.strip()
        specs = specs.strip()

        if not c_code or not ip or not specs:
            raise ValueError("Computer code, IP address, and hardware specs cannot be empty.")
        if hourly_rate <= 0:
            raise ValueError("Hourly rate must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO computers (computer_code, ip_address, specs, hourly_rate, status)
                    VALUES (?, ?, ?, ?, 'Available')
                    """,
                    (c_code, ip, specs, round(hourly_rate, 2))
                )
                return {
                    "id": cursor.lastrowid,
                    "computer_code": c_code,
                    "ip_address": ip,
                    "specs": specs,
                    "hourly_rate": round(hourly_rate, 2),
                    "status": "Available"
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Computer with code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def start_session(self, computer_code: str, customer_name: str,
                      start_time_str: Optional[str] = None) -> Dict[str, Any]:
        c_code = computer_code.strip().upper()
        c_name = customer_name.strip()
        if not c_name:
            raise ValueError("Customer name cannot be empty.")

        s_time_str = start_time_str.strip() if start_time_str else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            datetime.strptime(s_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Start time must be in 'YYYY-MM-DD HH:MM:SS' format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, hourly_rate, status FROM computers WHERE computer_code = ?", (c_code,))
                comp = cursor.fetchone()
                if not comp:
                    raise ValueError(f"Computer '{c_code}' not found.")

                # Rule: A computer cannot be assigned to two active sessions simultaneously
                if comp["status"] != "Available":
                    raise ValueError(f"Computer '{c_code}' is currently unavailable (Status: {comp['status']}). Cannot start a new session.")

                session_id = f"SES-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO sessions (session_id, computer_id, customer_name, start_time, hourly_rate_applied, status)
                    VALUES (?, ?, ?, ?, ?, 'Active')
                    """,
                    (session_id, comp["id"], c_name, s_time_str, float(comp["hourly_rate"]))
                )
                cursor.execute("UPDATE computers SET status = 'In Use' WHERE id = ?", (comp["id"],))
        finally:
            conn.close()

        return self.get_session(session_id)

    def end_session(self, session_id: str, end_time_str: Optional[str] = None) -> Dict[str, Any]:
        s_id = session_id.strip().upper()
        e_time_str = end_time_str.strip() if end_time_str else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            end_dt = datetime.strptime(e_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("End time must be in 'YYYY-MM-DD HH:MM:SS' format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, computer_id, start_time, hourly_rate_applied, status FROM sessions WHERE session_id = ?", (s_id,))
                sess = cursor.fetchone()
                if not sess:
                    raise ValueError(f"Session '{s_id}' not found.")
                if sess["status"] != "Active":
                    raise ValueError(f"Cannot end session '{s_id}' because status is already '{sess['status']}'.")

                start_dt = datetime.strptime(sess["start_time"], "%Y-%m-%d %H:%M:%S")
                if end_dt < start_dt:
                    raise ValueError("End time cannot be earlier than session start time.")

                # Accurate duration calculation (handles midnight transitions cleanly)
                total_seconds = int((end_dt - start_dt).total_seconds())
                duration_minutes = max(1, math.ceil(total_seconds / 60))

                # Billing calculation (pro-rata billing based on hourly rate, minimum 15 mins)
                billable_minutes = max(15, duration_minutes)
                hourly_rate = float(sess["hourly_rate_applied"])
                total_bill = round((billable_minutes / 60.0) * hourly_rate, 2)

                cursor.execute(
                    """
                    UPDATE sessions
                    SET end_time = ?, duration_minutes = ?, total_bill = ?, status = 'Completed'
                    WHERE id = ?
                    """,
                    (e_time_str, duration_minutes, total_bill, sess["id"])
                )
                # Release computer
                cursor.execute("UPDATE computers SET status = 'Available' WHERE id = ?", (sess["computer_id"],))
        finally:
            conn.close()

        return self.get_session(s_id)

    def record_payment(self, session_id: str, amount: float) -> Dict[str, Any]:
        s_id = session_id.strip().upper()
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, total_bill, payment_status, status FROM sessions WHERE session_id = ?", (s_id,))
                sess = cursor.fetchone()
                if not sess:
                    raise ValueError(f"Session '{s_id}' not found.")
                if sess["payment_status"] == "Paid":
                    raise ValueError(f"Session '{s_id}' has already been paid in full.")
                if sess["status"] == "Active":
                    raise ValueError("Session is still active. Please end the session first to compute the final bill.")

                total_bill = float(sess["total_bill"])
                if round(amount, 2) < total_bill:
                    raise ValueError(f"Insufficient payment. Total bill is ${total_bill:.2f}, but received ${amount:.2f}.")

                change = round(amount - total_bill, 2)
                cursor.execute(
                    """
                    UPDATE sessions
                    SET payment_status = 'Paid', amount_paid = ?
                    WHERE id = ?
                    """,
                    (round(amount, 2), sess["id"])
                )
        finally:
            conn.close()

        res = self.get_session(s_id)
        res["change_returned"] = change
        return res

    def get_session(self, session_id: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.*, c.computer_code, c.ip_address, c.specs
                FROM sessions s
                JOIN computers c ON s.computer_id = c.id
                WHERE s.session_id = ?
                """,
                (session_id.strip().upper(),)
            )
            sess = cursor.fetchone()
            if not sess:
                raise ValueError(f"Session '{session_id}' not found.")
            return dict(sess)
        finally:
            conn.close()

    def list_computers(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM computers ORDER BY computer_code ASC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def list_sessions(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT s.*, c.computer_code
                FROM sessions s
                JOIN computers c ON s.computer_id = c.id
            """
            params = []
            if status_filter:
                query += " WHERE s.status = ?"
                params.append(status_filter.capitalize())
            query += " ORDER BY s.id DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_daily_revenue_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        rep_date = target_date.strip() if target_date else str(date.today())
        try:
            datetime.strptime(rep_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Report date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as completed_sessions,
                       COALESCE(SUM(duration_minutes), 0) as total_minutes,
                       COALESCE(SUM(total_bill), 0) as total_billed,
                       COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN total_bill ELSE 0 END), 0) as total_collected
                FROM sessions
                WHERE DATE(start_time) = ? AND status = 'Completed'
                """,
                (rep_date,)
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                SELECT c.computer_code, COUNT(s.id) as sessions_count, SUM(s.duration_minutes) as terminal_minutes, SUM(s.total_bill) as revenue
                FROM sessions s
                JOIN computers c ON s.computer_id = c.id
                WHERE DATE(s.start_time) = ? AND s.status = 'Completed'
                GROUP BY c.id
                ORDER BY revenue DESC
                """,
                (rep_date,)
            )
            by_comp = [dict(r) for r in cursor.fetchall()]

            total_hours = round(float(stats["total_minutes"]) / 60.0, 1)
            return {
                "report_date": rep_date,
                "completed_sessions": stats["completed_sessions"],
                "total_usage_minutes": stats["total_minutes"],
                "total_usage_hours": total_hours,
                "total_billed": round(float(stats["total_billed"]), 2),
                "total_revenue_collected": round(float(stats["total_collected"]), 2),
                "terminal_breakdown": by_comp
            }
        finally:
            conn.close()
