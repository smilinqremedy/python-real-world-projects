"""
Business logic and financial reconciliation for School Fee Payment Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class FeeService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def define_class(self, code: str, name: str, academic_session: str, term_fee: float) -> Dict[str, Any]:
        c_code = code.strip().upper()
        name = name.strip()
        sess = academic_session.strip()

        if not c_code or not name or not sess:
            raise ValueError("Class code, name, and academic session cannot be empty.")
        if term_fee <= 0:
            raise ValueError("Term fee must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO classes (class_code, name, academic_session, term_fee)
                    VALUES (?, ?, ?, ?)
                    """,
                    (c_code, name, sess, round(term_fee, 2))
                )
                return {
                    "id": cursor.lastrowid,
                    "class_code": c_code,
                    "name": name,
                    "academic_session": sess,
                    "term_fee": round(term_fee, 2)
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Class with code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def register_student(self, reg_no: str, name: str, class_code: str,
                         parent_name: str, parent_phone: str) -> Dict[str, Any]:
        s_reg = reg_no.strip().upper()
        name = name.strip()
        p_name = parent_name.strip()
        p_phone = parent_phone.strip()

        if not s_reg or not name or not p_name or not p_phone:
            raise ValueError("Student registration number, name, parent name, and parent phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM classes WHERE class_code = ?", (class_code.strip().upper(),))
                cls_row = cursor.fetchone()
                if not cls_row:
                    raise ValueError(f"Class '{class_code}' does not exist.")

                cursor.execute(
                    """
                    INSERT INTO students (student_reg_no, name, class_id, parent_name, parent_phone, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (s_reg, name, cls_row["id"], p_name, p_phone)
                )
                return {
                    "id": cursor.lastrowid,
                    "student_reg_no": s_reg,
                    "name": name,
                    "class_code": class_code.strip().upper(),
                    "parent_name": p_name,
                    "parent_phone": p_phone
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Student with registration number '{s_reg}' already exists.")
            raise
        finally:
            conn.close()

    def record_fee_payment(self, student_reg_no: str, amount: float, academic_term: str = "Term 1",
                           payment_date_str: Optional[str] = None, payment_method: str = "Bank Transfer",
                           notes: str = "") -> Dict[str, Any]:
        s_reg = student_reg_no.strip().upper()
        term = academic_term.strip()

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero. Negative or zero payments are not allowed.")
        if not term:
            raise ValueError("Academic term cannot be empty.")

        p_date = payment_date_str.strip() if payment_date_str else str(date.today())
        try:
            datetime.strptime(p_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Payment date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT s.id, s.name, c.term_fee, c.name as class_name
                    FROM students s
                    JOIN classes c ON s.class_id = c.id
                    WHERE s.student_reg_no = ? AND s.is_active = 1
                    """,
                    (s_reg,)
                )
                student = cursor.fetchone()
                if not student:
                    raise ValueError(f"Active student '{s_reg}' not found.")

                receipt_ref = f"FEE-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO payments (receipt_reference, student_id, amount, payment_date, payment_method, academic_term, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (receipt_ref, student["id"], round(amount, 2), p_date, payment_method.strip(), term, notes.strip())
                )
        finally:
            conn.close()

        balance_info = self.get_student_balance(s_reg, term)
        balance_info["latest_receipt_reference"] = receipt_ref
        balance_info["amount_paid_now"] = round(amount, 2)
        balance_info["payment_date"] = p_date
        return balance_info

    def get_student_balance(self, student_reg_no: str, academic_term: str = "Term 1") -> Dict[str, Any]:
        s_reg = student_reg_no.strip().upper()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.student_reg_no, s.name, s.parent_name, s.parent_phone,
                       c.class_code, c.name as class_name, c.term_fee, c.academic_session
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.student_reg_no = ?
                """,
                (s_reg,)
            )
            student = cursor.fetchone()
            if not student:
                raise ValueError(f"Student '{s_reg}' not found.")

            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE student_id = ? AND academic_term = ?
                """,
                (student["id"], academic_term.strip())
            )
            total_paid = float(cursor.fetchone()[0])
            term_fee = float(student["term_fee"])
            balance = max(0.0, round(term_fee - total_paid, 2))

            if total_paid >= term_fee:
                status = "Paid"
            elif total_paid > 0:
                status = "Partial"
            else:
                status = "Unpaid"

            res = dict(student)
            res["academic_term"] = academic_term.strip()
            res["total_paid"] = round(total_paid, 2)
            res["outstanding_balance"] = balance
            res["payment_status"] = status
            return res
        finally:
            conn.close()

    def get_student_payment_history(self, student_reg_no: str) -> Dict[str, Any]:
        s_reg = student_reg_no.strip().upper()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.student_reg_no, s.name, c.class_code, c.name as class_name, c.term_fee
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.student_reg_no = ?
                """,
                (s_reg,)
            )
            student = cursor.fetchone()
            if not student:
                raise ValueError(f"Student '{s_reg}' not found.")

            cursor.execute(
                """
                SELECT receipt_reference, amount, payment_date, payment_method, academic_term, notes
                FROM payments
                WHERE student_id = ?
                ORDER BY payment_date ASC, id ASC
                """,
                (student["id"],)
            )
            records = [dict(r) for r in cursor.fetchall()]

            res = dict(student)
            res["payments"] = records
            res["lifetime_paid"] = round(sum(r["amount"] for r in records), 2)
            return res
        finally:
            conn.close()

    def get_unpaid_students(self, academic_term: str = "Term 1", class_code: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT s.student_reg_no
                FROM students s
                JOIN classes c ON s.class_id = c.id
                WHERE s.is_active = 1
            """
            params = []
            if class_code:
                query += " AND c.class_code = ?"
                params.append(class_code.strip().upper())
            cursor.execute(query, params)
            reg_numbers = [r["student_reg_no"] for r in cursor.fetchall()]
        finally:
            conn.close()

        unpaid_list = []
        for reg in reg_numbers:
            bal = self.get_student_balance(reg, academic_term)
            if bal["payment_status"] in ["Unpaid", "Partial"]:
                unpaid_list.append(bal)

        unpaid_list.sort(key=lambda x: x["outstanding_balance"], reverse=True)
        return unpaid_list

    def list_classes(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.*, COUNT(s.id) as enrolled_students
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id AND s.is_active = 1
                GROUP BY c.id
                ORDER BY c.class_code ASC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_financial_report(self, academic_term: str = "Term 1") -> Dict[str, Any]:
        classes = self.list_classes()
        class_summaries = []

        total_students = 0
        total_expected_revenue = 0.0
        total_collected_revenue = 0.0

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            for cls in classes:
                enrolled = cls["enrolled_students"]
                term_fee = cls["term_fee"]
                class_expected = enrolled * term_fee

                cursor.execute(
                    """
                    SELECT COALESCE(SUM(p.amount), 0)
                    FROM payments p
                    JOIN students s ON p.student_id = s.id
                    WHERE s.class_id = ? AND p.academic_term = ?
                    """,
                    (cls["id"], academic_term.strip())
                )
                class_collected = float(cursor.fetchone()[0])
                class_outstanding = max(0.0, round(class_expected - class_collected, 2))
                coll_rate = (class_collected / class_expected * 100) if class_expected > 0 else 0.0

                total_students += enrolled
                total_expected_revenue += class_expected
                total_collected_revenue += class_collected

                class_summaries.append({
                    "class_code": cls["class_code"],
                    "class_name": cls["name"],
                    "term_fee": term_fee,
                    "enrolled_students": enrolled,
                    "expected_revenue": round(class_expected, 2),
                    "collected_revenue": round(class_collected, 2),
                    "outstanding_debt": class_outstanding,
                    "collection_rate_percent": round(coll_rate, 1)
                })
        finally:
            conn.close()

        total_outstanding = max(0.0, round(total_expected_revenue - total_collected_revenue, 2))
        overall_rate = (total_collected_revenue / total_expected_revenue * 100) if total_expected_revenue > 0 else 0.0

        return {
            "academic_term": academic_term.strip(),
            "total_enrolled_students": total_students,
            "total_expected_revenue": round(total_expected_revenue, 2),
            "total_collected_revenue": round(total_collected_revenue, 2),
            "total_outstanding_debt": total_outstanding,
            "overall_collection_rate": round(overall_rate, 1),
            "classes": class_summaries
        }
