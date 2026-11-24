"""
Attendance Reporting and CSV Export Engine.
Generates daily, weekly, and monthly aggregate reports with biometric vs manual breakdown.
"""
import csv
import io
from typing import List, Dict, Any, Optional
import database


class AttendanceReporter:
    def __init__(self, db_path: str = database.DEFAULT_DB_PATH):
        self.db_path = db_path

    def get_session_attendance(self, session_code: str) -> List[Dict[str, Any]]:
        """Retrieves all attendance records for a specific session."""
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    r.id as record_id,
                    s.session_code,
                    s.session_name,
                    p.employee_id,
                    p.full_name,
                    p.department,
                    r.timestamp,
                    r.date,
                    r.method,
                    r.confidence_score,
                    r.status,
                    r.verified_by,
                    r.notes
                FROM attendance_records r
                JOIN attendance_sessions s ON r.session_id = s.id
                JOIN participants p ON r.participant_id = p.id
                WHERE s.session_code = ?
                ORDER BY r.timestamp ASC
            """, (session_code,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def generate_report_by_period(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generates aggregate attendance report within date range (YYYY-MM-DD).
        Calculates total check-ins, breakdown by method (facial vs manual), and status.
        """
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    r.id,
                    r.date,
                    r.timestamp,
                    r.method,
                    r.status,
                    p.employee_id,
                    p.full_name,
                    p.department,
                    s.session_code
                FROM attendance_records r
                JOIN attendance_sessions s ON r.session_id = s.id
                JOIN participants p ON r.participant_id = p.id
                WHERE r.date >= ? AND r.date <= ?
                ORDER BY r.date ASC, r.timestamp ASC
            """, (start_date, end_date))
            records = [dict(r) for r in cursor.fetchall()]

            # Total participants
            cursor.execute("SELECT COUNT(*) as total FROM participants WHERE is_active = 1")
            total_active = cursor.fetchone()["total"]

        biometric_count = sum(1 for r in records if r["method"] == "facial_biometric")
        manual_count = sum(1 for r in records if r["method"] == "manual_alternative")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_active_participants": total_active,
            "total_check_ins": len(records),
            "biometric_check_ins": biometric_count,
            "manual_check_ins": manual_count,
            "records": records
        }

    def export_to_csv(self, records: List[Dict[str, Any]], output_filepath: Optional[str] = None) -> str:
        """Exports a list of attendance records into CSV format."""
        fields = [
            "record_id", "session_code", "employee_id", "full_name",
            "department", "date", "timestamp", "method", "status", "notes"
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

        csv_content = output.getvalue()

        if output_filepath:
            with open(output_filepath, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)

        return csv_content
