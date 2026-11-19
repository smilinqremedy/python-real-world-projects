"""
Business logic and attendance operations for Employee Attendance Management System.
"""

from datetime import datetime, date, time
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class AttendanceService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_employee(self, emp_code: str, name: str, department: str,
                          position: str, shift_start_time: str = "09:00") -> Dict[str, Any]:
        code = emp_code.strip().upper()
        name = name.strip()
        dept = department.strip()
        pos = position.strip()
        shift = shift_start_time.strip()

        if not code or not name or not dept or not pos:
            raise ValueError("Employee code, name, department, and position cannot be empty.")

        try:
            datetime.strptime(shift, "%H:%M")
        except ValueError:
            raise ValueError("Shift start time must be in HH:MM format (24-hour clock).")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO employees (emp_code, name, department, position, shift_start_time)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (code, name, dept, pos, shift)
                )
                return {
                    "id": cursor.lastrowid,
                    "emp_code": code,
                    "name": name,
                    "department": dept,
                    "position": pos,
                    "shift_start_time": shift,
                    "is_active": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Employee with code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def record_check_in(self, emp_code: str, check_in_str: Optional[str] = None,
                        att_date_str: Optional[str] = None, notes: str = "") -> Dict[str, Any]:
        code = emp_code.strip().upper()
        today_date = att_date_str.strip() if att_date_str else str(date.today())
        try:
            datetime.strptime(today_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Attendance date must be in YYYY-MM-DD format.")

        now_str = check_in_str.strip() if check_in_str else datetime.now().strftime("%H:%M:%S")
        try:
            if len(now_str.split(":")) == 2:
                check_in_time_obj = datetime.strptime(now_str, "%H:%M").time()
                formatted_check_in = check_in_time_obj.strftime("%H:%M:00")
            else:
                check_in_time_obj = datetime.strptime(now_str, "%H:%M:%S").time()
                formatted_check_in = check_in_time_obj.strftime("%H:%M:%S")
        except ValueError:
            raise ValueError("Check-in time must be in HH:MM or HH:MM:SS format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, shift_start_time, is_active FROM employees WHERE emp_code = ?", (code,))
                emp = cursor.fetchone()
                if not emp:
                    raise ValueError(f"Employee with code '{code}' not found.")
                if not emp["is_active"]:
                    raise ValueError(f"Employee '{code}' is inactive.")

                # Calculate lateness
                shift_obj = datetime.strptime(emp["shift_start_time"], "%H:%M").time()
                is_late = 0
                minutes_late = 0
                if check_in_time_obj > shift_obj:
                    is_late = 1
                    shift_dt = datetime.combine(date.today(), shift_obj)
                    check_in_dt = datetime.combine(date.today(), check_in_time_obj)
                    minutes_late = int((check_in_dt - shift_dt).total_seconds() // 60)

                cursor.execute(
                    """
                    INSERT INTO attendance (employee_id, attendance_date, check_in_time, is_late, minutes_late, status, notes)
                    VALUES (?, ?, ?, ?, ?, 'Present', ?)
                    """,
                    (emp["id"], today_date, formatted_check_in, is_late, minutes_late, notes.strip())
                )
                att_id = cursor.lastrowid
                return {
                    "id": att_id,
                    "emp_code": code,
                    "name": emp["name"],
                    "attendance_date": today_date,
                    "check_in_time": formatted_check_in,
                    "is_late": bool(is_late),
                    "minutes_late": minutes_late,
                    "status": "Present",
                    "notes": notes.strip()
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Attendance for employee '{code}' on {today_date} has already been recorded.")
            raise
        finally:
            conn.close()

    def record_check_out(self, emp_code: str, check_out_str: Optional[str] = None,
                         att_date_str: Optional[str] = None) -> Dict[str, Any]:
        code = emp_code.strip().upper()
        target_date = att_date_str.strip() if att_date_str else str(date.today())
        now_str = check_out_str.strip() if check_out_str else datetime.now().strftime("%H:%M:%S")

        try:
            if len(now_str.split(":")) == 2:
                check_out_time_obj = datetime.strptime(now_str, "%H:%M").time()
                formatted_check_out = check_out_time_obj.strftime("%H:%M:00")
            else:
                check_out_time_obj = datetime.strptime(now_str, "%H:%M:%S").time()
                formatted_check_out = check_out_time_obj.strftime("%H:%M:%S")
        except ValueError:
            raise ValueError("Check-out time must be in HH:MM or HH:MM:SS format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT a.id, a.check_in_time, e.name
                    FROM attendance a
                    JOIN employees e ON a.employee_id = e.id
                    WHERE e.emp_code = ? AND a.attendance_date = ?
                    """,
                    (code, target_date)
                )
                record = cursor.fetchone()
                if not record:
                    raise ValueError(f"No check-in record found for employee '{code}' on {target_date}.")

                cursor.execute(
                    "UPDATE attendance SET check_out_time = ? WHERE id = ?",
                    (formatted_check_out, record["id"])
                )
                return {
                    "emp_code": code,
                    "name": record["name"],
                    "attendance_date": target_date,
                    "check_in_time": record["check_in_time"],
                    "check_out_time": formatted_check_out
                }
        finally:
            conn.close()

    def record_absence(self, emp_code: str, att_date_str: str, reason: str = "") -> Dict[str, Any]:
        code = emp_code.strip().upper()
        try:
            datetime.strptime(att_date_str.strip(), "%Y-%m-%d")
            t_date = att_date_str.strip()
        except ValueError:
            raise ValueError("Attendance date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM employees WHERE emp_code = ?", (code,))
                emp = cursor.fetchone()
                if not emp:
                    raise ValueError(f"Employee with code '{code}' not found.")

                cursor.execute(
                    """
                    INSERT INTO attendance (employee_id, attendance_date, status, notes)
                    VALUES (?, ?, 'Absent', ?)
                    """,
                    (emp["id"], t_date, reason.strip())
                )
                return {
                    "emp_code": code,
                    "name": emp["name"],
                    "attendance_date": t_date,
                    "status": "Absent",
                    "reason": reason.strip()
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Attendance for employee '{code}' on {t_date} has already been recorded.")
            raise
        finally:
            conn.close()

    def get_late_arrivals(self, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT a.id, e.emp_code, e.name, e.department, e.shift_start_time,
                       a.attendance_date, a.check_in_time, a.minutes_late
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                WHERE a.is_late = 1
            """
            params = []
            if target_date:
                query += " AND a.attendance_date = ?"
                params.append(target_date.strip())
            query += " ORDER BY a.attendance_date DESC, a.minutes_late DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_employee_history(self, emp_code: str) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.id, a.attendance_date, a.check_in_time, a.check_out_time,
                       a.is_late, a.minutes_late, a.status, a.notes,
                       e.emp_code, e.name, e.department
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                WHERE e.emp_code = ?
                ORDER BY a.attendance_date DESC
                """,
                (emp_code.strip().upper(),)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def list_employees(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees ORDER BY emp_code ASC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_attendance_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        try:
            d_start = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
            d_end = datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format.")

        if d_start > d_end:
            raise ValueError("Start date cannot be after end date.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, emp_code, name, department FROM employees WHERE is_active = 1 ORDER BY emp_code ASC")
            employees = cursor.fetchall()

            emp_summaries = []
            total_present = 0
            total_absent = 0
            total_late = 0

            for emp in employees:
                cursor.execute(
                    """
                    SELECT status, is_late
                    FROM attendance
                    WHERE employee_id = ? AND attendance_date BETWEEN ? AND ?
                    """,
                    (emp["id"], str(d_start), str(d_end))
                )
                records = cursor.fetchall()
                present_count = sum(1 for r in records if r["status"] == "Present")
                absent_count = sum(1 for r in records if r["status"] == "Absent")
                late_count = sum(1 for r in records if r["is_late"] == 1)

                total_logged = len(records)
                percentage = (present_count / total_logged * 100) if total_logged > 0 else 0.0

                total_present += present_count
                total_absent += absent_count
                total_late += late_count

                emp_summaries.append({
                    "emp_code": emp["emp_code"],
                    "name": emp["name"],
                    "department": emp["department"],
                    "logged_days": total_logged,
                    "present_days": present_count,
                    "absent_days": absent_count,
                    "late_days": late_count,
                    "attendance_rate": round(percentage, 1)
                })

            total_days_logged = total_present + total_absent
            overall_rate = (total_present / total_days_logged * 100) if total_days_logged > 0 else 0.0

            return {
                "start_date": str(d_start),
                "end_date": str(d_end),
                "total_employees": len(employees),
                "total_present": total_present,
                "total_absent": total_absent,
                "total_late_incidents": total_late,
                "overall_attendance_rate": round(overall_rate, 1),
                "employee_summaries": emp_summaries
            }
        finally:
            conn.close()
