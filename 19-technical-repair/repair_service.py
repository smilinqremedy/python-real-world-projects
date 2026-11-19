"""
Business logic and service layer for Technical Repair Service Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class RepairService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_customer(self, code: str, name: str, phone: str, email: str = "") -> Dict[str, Any]:
        c_code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()

        if not c_code or not name or not phone:
            raise ValueError("Customer code, name, and phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO customers (customer_code, name, phone, email) VALUES (?, ?, ?, ?)",
                    (c_code, name, phone, email.strip())
                )
                return {
                    "id": cursor.lastrowid,
                    "customer_code": c_code,
                    "name": name,
                    "phone": phone,
                    "email": email.strip()
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Customer code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def register_technician(self, code: str, name: str, specialty: str, phone: str) -> Dict[str, Any]:
        t_code = code.strip().upper()
        name = name.strip()
        spec = specialty.strip()
        phone = phone.strip()

        if not t_code or not name or not spec or not phone:
            raise ValueError("Technician code, name, specialty, and phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO technicians (tech_code, name, specialty, phone, is_active) VALUES (?, ?, ?, ?, 1)",
                    (t_code, name, spec, phone)
                )
                return {
                    "id": cursor.lastrowid,
                    "tech_code": t_code,
                    "name": name,
                    "specialty": spec,
                    "phone": phone,
                    "is_active": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Technician code '{t_code}' already exists.")
            raise
        finally:
            conn.close()

    def check_in_device(self, customer_code: str, device_type: str, brand: str,
                        model: str, problem_description: str, serial_number: str = "",
                        received_date_str: Optional[str] = None) -> Dict[str, Any]:
        dtype = device_type.strip()
        brand = brand.strip()
        model = model.strip()
        problem = problem_description.strip()

        if not dtype or not brand or not model or not problem:
            raise ValueError("Device type, brand, model, and reported problem cannot be empty.")

        r_date = received_date_str.strip() if received_date_str else str(date.today())
        try:
            datetime.strptime(r_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Received date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM customers WHERE customer_code = ?", (customer_code.strip().upper(),))
                cust = cursor.fetchone()
                if not cust:
                    raise ValueError(f"Customer '{customer_code}' not found.")

                ref_num = f"REP-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO repairs (reference_number, customer_id, device_type, brand, model, serial_number, problem_description, status, received_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Received', ?)
                    """,
                    (ref_num, cust["id"], dtype, brand, model, serial_number.strip(), problem, r_date)
                )
        finally:
            conn.close()

        return self.get_repair_by_ref(ref_num)

    def assign_technician(self, ref_num: str, tech_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status FROM repairs WHERE reference_number = ?", (ref_num.strip().upper(),))
                repair = cursor.fetchone()
                if not repair:
                    raise ValueError(f"Repair record '{ref_num}' not found.")

                cursor.execute("SELECT id, name, is_active FROM technicians WHERE tech_code = ?", (tech_code.strip().upper(),))
                tech = cursor.fetchone()
                if not tech:
                    raise ValueError(f"Technician '{tech_code}' not found.")
                if not tech["is_active"]:
                    raise ValueError(f"Technician '{tech_code}' is inactive.")

                # If status was Received, transition to Diagnosing
                new_status = "Diagnosing" if repair["status"] == "Received" else repair["status"]

                cursor.execute(
                    "UPDATE repairs SET technician_id = ?, status = ? WHERE id = ?",
                    (tech["id"], new_status, repair["id"])
                )
        finally:
            conn.close()

        return self.get_repair_by_ref(ref_num)

    def set_repair_costs(self, ref_num: str, parts_cost: float, labor_cost: float) -> Dict[str, Any]:
        if parts_cost < 0 or labor_cost < 0:
            raise ValueError("Parts and labor costs cannot be negative.")

        total = round(parts_cost + labor_cost, 2)
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, amount_paid FROM repairs WHERE reference_number = ?", (ref_num.strip().upper(),))
                repair = cursor.fetchone()
                if not repair:
                    raise ValueError(f"Repair record '{ref_num}' not found.")

                paid_amt = float(repair["amount_paid"])
                is_paid = 1 if (paid_amt >= total and total > 0) else 0

                cursor.execute(
                    """
                    UPDATE repairs
                    SET parts_cost = ?, labor_cost = ?, total_cost = ?, is_paid = ?
                    WHERE id = ?
                    """,
                    (round(parts_cost, 2), round(labor_cost, 2), total, is_paid, repair["id"])
                )
        finally:
            conn.close()

        return self.get_repair_by_ref(ref_num)

    def record_payment(self, ref_num: str, amount: float) -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, total_cost, amount_paid FROM repairs WHERE reference_number = ?", (ref_num.strip().upper(),))
                repair = cursor.fetchone()
                if not repair:
                    raise ValueError(f"Repair record '{ref_num}' not found.")

                current_paid = float(repair["amount_paid"])
                total_cost = float(repair["total_cost"])
                new_paid = round(current_paid + amount, 2)
                is_paid = 1 if new_paid >= total_cost else 0

                cursor.execute(
                    "UPDATE repairs SET amount_paid = ?, is_paid = ? WHERE id = ?",
                    (new_paid, is_paid, repair["id"])
                )
        finally:
            conn.close()

        return self.get_repair_by_ref(ref_num)

    def update_repair_status(self, ref_num: str, new_status: str) -> Dict[str, Any]:
        status_clean = new_status.strip().capitalize()
        valid = ["Received", "Diagnosing", "Repairing", "Completed", "Collected"]
        if status_clean not in valid:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(valid)}")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status, is_paid, total_cost, amount_paid FROM repairs WHERE reference_number = ?", (ref_num.strip().upper(),))
                repair = cursor.fetchone()
                if not repair:
                    raise ValueError(f"Repair record '{ref_num}' not found.")

                current_status = repair["status"]

                if status_clean == "Collected":
                    # Rule: cannot mark as collected before repair completion
                    if current_status != "Completed":
                        raise ValueError(f"Cannot mark device as 'Collected' before repair is completed (Current status: {current_status}).")
                    # Rule: cannot mark as collected before payment confirmation
                    if not repair["is_paid"]:
                        balance = round(float(repair["total_cost"]) - float(repair["amount_paid"]), 2)
                        raise ValueError(f"Cannot mark device as 'Collected' before payment confirmation (Outstanding balance: ${balance:.2f}).")

                completed_clause = ", completed_date = CURRENT_DATE" if status_clean == "Completed" else ""
                collected_clause = ", collected_date = CURRENT_DATE" if status_clean == "Collected" else ""

                cursor.execute(
                    f"UPDATE repairs SET status = ?{completed_clause}{collected_clause} WHERE id = ?",
                    (status_clean, repair["id"])
                )
        finally:
            conn.close()

        return self.get_repair_by_ref(ref_num)

    def get_repair_by_ref(self, ref_num: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.*, c.customer_code, c.name as customer_name, c.phone as customer_phone,
                       t.tech_code, t.name as technician_name, t.specialty as tech_specialty
                FROM repairs r
                JOIN customers c ON r.customer_id = c.id
                LEFT JOIN technicians t ON r.technician_id = t.id
                WHERE r.reference_number = ?
                """,
                (ref_num.strip().upper(),)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Repair record '{ref_num}' not found.")

            res = dict(row)
            res["balance_due"] = max(0.0, round(float(res["total_cost"]) - float(res["amount_paid"]), 2))
            return res
        finally:
            conn.close()

    def search_repairs(self, query: str) -> List[Dict[str, Any]]:
        term = f"%{query.strip().lower()}%"
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.*, c.customer_code, c.name as customer_name, c.phone as customer_phone,
                       t.name as technician_name
                FROM repairs r
                JOIN customers c ON r.customer_id = c.id
                LEFT JOIN technicians t ON r.technician_id = t.id
                WHERE LOWER(r.reference_number) LIKE ?
                   OR LOWER(c.name) LIKE ?
                   OR LOWER(r.brand) LIKE ?
                   OR LOWER(r.model) LIKE ?
                   OR LOWER(COALESCE(r.serial_number, '')) LIKE ?
                ORDER BY r.id DESC
                """,
                (term, term, term, term, term)
            )
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["balance_due"] = max(0.0, round(float(d["total_cost"]) - float(d["amount_paid"]), 2))
                results.append(d)
            return results
        finally:
            conn.close()

    def generate_report(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM repairs")
            total_repairs = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM repairs
                GROUP BY status
                """
            )
            status_breakdown = {r["status"]: r["count"] for r in cursor.fetchall()}

            cursor.execute(
                """
                SELECT COALESCE(SUM(parts_cost), 0) as total_parts,
                       COALESCE(SUM(labor_cost), 0) as total_labor,
                       COALESCE(SUM(total_cost), 0) as total_billed,
                       COALESCE(SUM(amount_paid), 0) as total_collected
                FROM repairs
                """
            )
            finances = cursor.fetchone()

            cursor.execute(
                """
                SELECT t.name as tech_name, COUNT(r.id) as jobs_assigned,
                       SUM(CASE WHEN r.status IN ('Completed', 'Collected') THEN 1 ELSE 0 END) as jobs_completed
                FROM repairs r
                JOIN technicians t ON r.technician_id = t.id
                GROUP BY t.id
                ORDER BY jobs_completed DESC
                """
            )
            tech_performance = [dict(r) for r in cursor.fetchall()]

            return {
                "total_repairs_logged": total_repairs,
                "status_breakdown": status_breakdown,
                "financials": {
                    "parts_revenue": round(float(finances["total_parts"]), 2),
                    "labor_revenue": round(float(finances["total_labor"]), 2),
                    "total_billed": round(float(finances["total_billed"]), 2),
                    "total_collected": round(float(finances["total_collected"]), 2),
                    "outstanding_debt": max(0.0, round(float(finances["total_billed"]) - float(finances["total_collected"]), 2))
                },
                "technician_performance": tech_performance
            }
        finally:
            conn.close()
