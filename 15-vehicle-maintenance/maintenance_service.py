"""
Service layer and domain logic for Vehicle Maintenance Tracking System.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class MaintenanceService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_vehicle(self, reg_number: str, make: str, model: str,
                         year: int, current_mileage: int = 0) -> Dict[str, Any]:
        reg = reg_number.strip().upper()
        make = make.strip()
        model = model.strip()

        if not reg or not make or not model:
            raise ValueError("Registration number, make, and model cannot be empty.")
        if year < 1900 or year > date.today().year + 1:
            raise ValueError(f"Vehicle year must be between 1900 and {date.today().year + 1}.")
        if current_mileage < 0:
            raise ValueError("Current mileage cannot be negative.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO vehicles (reg_number, make, model, year, current_mileage)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (reg, make, model, year, current_mileage)
                )
                v_id = cursor.lastrowid
                return {
                    "id": v_id,
                    "reg_number": reg,
                    "make": make,
                    "model": model,
                    "year": year,
                    "current_mileage": current_mileage
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Vehicle with registration '{reg}' already exists.")
            raise
        finally:
            conn.close()

    def update_mileage(self, reg_number: str, new_mileage: int) -> Dict[str, Any]:
        reg = reg_number.strip().upper()
        if new_mileage < 0:
            raise ValueError("Mileage cannot be negative.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, current_mileage FROM vehicles WHERE reg_number = ?", (reg,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Vehicle '{reg}' not found.")
                if new_mileage < row["current_mileage"]:
                    raise ValueError(f"New mileage ({new_mileage}) cannot be less than current recorded mileage ({row['current_mileage']}).")

                cursor.execute("UPDATE vehicles SET current_mileage = ? WHERE id = ?", (new_mileage, row["id"]))
        finally:
            conn.close()

        return self.get_vehicle_by_reg(reg)

    def record_maintenance(self, reg_number: str, service_type: str, cost: float,
                           mileage_at_service: int, service_date_str: Optional[str] = None,
                           next_due_date_str: Optional[str] = None,
                           next_due_mileage: Optional[int] = None,
                           provider: str = "", notes: str = "") -> Dict[str, Any]:
        reg = reg_number.strip().upper()
        stype = service_type.strip()
        if not stype:
            raise ValueError("Service type cannot be empty.")
        if cost < 0:
            raise ValueError("Maintenance cost cannot be negative.")
        if mileage_at_service < 0:
            raise ValueError("Mileage at service cannot be negative.")

        s_date = service_date_str.strip() if service_date_str else str(date.today())
        try:
            parsed_service_date = datetime.strptime(s_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Service date must be in YYYY-MM-DD format.")

        due_date = None
        if next_due_date_str:
            try:
                parsed_due = datetime.strptime(next_due_date_str.strip(), "%Y-%m-%d").date()
                if parsed_due < parsed_service_date:
                    raise ValueError("Next due date cannot be earlier than service date.")
                due_date = str(parsed_due)
            except ValueError as e:
                if "Next due date cannot be earlier" in str(e):
                    raise
                raise ValueError("Next due date must be in YYYY-MM-DD format.")

        if next_due_mileage is not None and next_due_mileage <= mileage_at_service:
            raise ValueError("Next due mileage must be greater than mileage at service.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, current_mileage FROM vehicles WHERE reg_number = ?", (reg,))
                vehicle = cursor.fetchone()
                if not vehicle:
                    raise ValueError(f"Vehicle '{reg}' not found.")

                cursor.execute(
                    """
                    INSERT INTO maintenance_records (vehicle_id, service_type, service_date, mileage_at_service, cost, service_provider, notes, next_due_date, next_due_mileage)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (vehicle["id"], stype, s_date, mileage_at_service, round(cost, 2), provider.strip(), notes.strip(), due_date, next_due_mileage)
                )
                rec_id = cursor.lastrowid

                # Update vehicle mileage if service mileage is higher
                if mileage_at_service > vehicle["current_mileage"]:
                    cursor.execute("UPDATE vehicles SET current_mileage = ? WHERE id = ?", (mileage_at_service, vehicle["id"]))
        finally:
            conn.close()

        return {
            "id": rec_id,
            "reg_number": reg,
            "service_type": stype,
            "service_date": s_date,
            "cost": round(cost, 2),
            "mileage_at_service": mileage_at_service,
            "next_due_date": due_date,
            "next_due_mileage": next_due_mileage
        }

    def get_overdue_maintenance(self, as_of_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        target_date = datetime.strptime(as_of_date_str.strip(), "%Y-%m-%d").date() if as_of_date_str else date.today()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT m.id, m.service_type, m.service_date, m.next_due_date, m.next_due_mileage,
                       v.reg_number, v.make, v.model, v.current_mileage
                FROM maintenance_records m
                JOIN vehicles v ON m.vehicle_id = v.id
                WHERE (m.next_due_date IS NOT NULL AND m.next_due_date < ?)
                   OR (m.next_due_mileage IS NOT NULL AND v.current_mileage >= m.next_due_mileage)
                ORDER BY m.next_due_date ASC
                """,
                (str(target_date),)
            )
            rows = cursor.fetchall()
            overdue_list = []
            for r in rows:
                reasons = []
                days_overdue = 0
                if r["next_due_date"] and datetime.strptime(r["next_due_date"], "%Y-%m-%d").date() < target_date:
                    due_d = datetime.strptime(r["next_due_date"], "%Y-%m-%d").date()
                    days_overdue = (target_date - due_d).days
                    reasons.append(f"Date overdue by {days_overdue} days (Due: {r['next_due_date']})")
                if r["next_due_mileage"] and r["current_mileage"] >= r["next_due_mileage"]:
                    miles_over = r["current_mileage"] - r["next_due_mileage"]
                    reasons.append(f"Mileage exceeded by {miles_over} miles (Due at: {r['next_due_mileage']})")

                overdue_list.append({
                    "record_id": r["id"],
                    "reg_number": r["reg_number"],
                    "vehicle": f"{r['make']} {r['model']}",
                    "service_type": r["service_type"],
                    "last_service_date": r["service_date"],
                    "current_mileage": r["current_mileage"],
                    "overdue_reasons": "; ".join(reasons)
                })
            return overdue_list
        finally:
            conn.close()

    def get_vehicle_by_reg(self, reg_number: str) -> Dict[str, Any]:
        reg = reg_number.strip().upper()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicles WHERE reg_number = ?", (reg,))
            v = cursor.fetchone()
            if not v:
                raise ValueError(f"Vehicle '{reg}' not found.")

            cursor.execute(
                """
                SELECT id, service_type, service_date, mileage_at_service, cost, service_provider, notes, next_due_date, next_due_mileage
                FROM maintenance_records
                WHERE vehicle_id = ?
                ORDER BY service_date DESC, id DESC
                """,
                (v["id"],)
            )
            records = [dict(r) for r in cursor.fetchall()]

            res = dict(v)
            res["history"] = records
            res["total_maintenance_cost"] = round(sum(r["cost"] for r in records), 2)
            return res
        finally:
            conn.close()

    def search_vehicles(self, query: str) -> List[Dict[str, Any]]:
        term = f"%{query.strip().upper()}%"
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, reg_number, make, model, year, current_mileage
                FROM vehicles
                WHERE UPPER(reg_number) LIKE ? OR UPPER(make) LIKE ? OR UPPER(model) LIKE ?
                ORDER BY reg_number ASC
                """,
                (term, term, term)
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_expense_report(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_vehicles = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(cost), 0) FROM maintenance_records")
            total_services, total_spent = cursor.fetchone()

            cursor.execute(
                """
                SELECT service_type, COUNT(*) as service_count, SUM(cost) as category_spent
                FROM maintenance_records
                GROUP BY service_type
                ORDER BY category_spent DESC
                """
            )
            by_type = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT v.reg_number, v.make, v.model, COUNT(m.id) as services_count, COALESCE(SUM(m.cost), 0) as vehicle_spent
                FROM vehicles v
                LEFT JOIN maintenance_records m ON v.id = m.vehicle_id
                GROUP BY v.id
                ORDER BY vehicle_spent DESC
                """
            )
            by_vehicle = [dict(r) for r in cursor.fetchall()]

            return {
                "total_vehicles": total_vehicles,
                "total_services_logged": total_services,
                "total_spent": round(float(total_spent), 2),
                "expenses_by_service_type": by_type,
                "expenses_by_vehicle": by_vehicle
            }
        finally:
            conn.close()
