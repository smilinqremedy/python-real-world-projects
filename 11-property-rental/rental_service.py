"""
Business logic and operations for Property Rental Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class RentalService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_property(self, code: str, name: str, address: str, monthly_rent: float) -> Dict[str, Any]:
        code = code.strip().upper()
        name = name.strip()
        address = address.strip()

        if not code or not name or not address:
            raise ValueError("Property code, name, and address cannot be empty.")
        if monthly_rent <= 0:
            raise ValueError("Monthly rent must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO properties (property_code, name, address, monthly_rent, status)
                    VALUES (?, ?, ?, ?, 'Vacant')
                    """,
                    (code, name, address, round(monthly_rent, 2))
                )
                prop_id = cursor.lastrowid
                return {
                    "id": prop_id,
                    "property_code": code,
                    "name": name,
                    "address": address,
                    "monthly_rent": round(monthly_rent, 2),
                    "status": "Vacant"
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Property with code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def add_tenant(self, code: str, name: str, email: str, phone: str,
                   lease_start_date: str, property_code: Optional[str] = None) -> Dict[str, Any]:
        code = code.strip().upper()
        name = name.strip()
        email = email.strip()
        phone = phone.strip()

        if not code or not name or not email or not phone:
            raise ValueError("Tenant code, name, email, and phone cannot be empty.")

        try:
            parsed_date = datetime.strptime(lease_start_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Lease start date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                prop_id = None
                if property_code:
                    cursor.execute("SELECT id, status, monthly_rent FROM properties WHERE property_code = ?",
                                   (property_code.strip().upper(),))
                    prop = cursor.fetchone()
                    if not prop:
                        raise ValueError(f"Property '{property_code}' does not exist.")
                    if prop["status"] != "Vacant":
                        raise ValueError(f"Property '{property_code}' is already occupied.")
                    prop_id = prop["id"]

                cursor.execute(
                    """
                    INSERT INTO tenants (tenant_code, name, email, phone, property_id, lease_start_date, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (code, name, email, phone, prop_id, str(parsed_date))
                )
                tenant_id = cursor.lastrowid

                if prop_id:
                    cursor.execute("UPDATE properties SET status = 'Occupied' WHERE id = ?", (prop_id,))

                return {
                    "id": tenant_id,
                    "tenant_code": code,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "property_id": prop_id,
                    "lease_start_date": str(parsed_date),
                    "is_active": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed: tenants.tenant_code" in str(e):
                raise ValueError(f"Tenant code '{code}' already exists.")
            if "UNIQUE constraint failed: tenants.property_id" in str(e):
                raise ValueError(f"Property is already assigned to another tenant.")
            raise
        finally:
            conn.close()

    def record_rent_payment(self, tenant_code: str, amount: float, period_month: str,
                            payment_date: Optional[str] = None, notes: str = "") -> Dict[str, Any]:
        tenant_code = tenant_code.strip().upper()
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        try:
            datetime.strptime(period_month.strip(), "%Y-%m")
            formatted_period = period_month.strip()
        except ValueError:
            raise ValueError("Period month must be in YYYY-MM format.")

        p_date = payment_date.strip() if payment_date else str(date.today())
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
                    SELECT t.id as tenant_id, t.name, t.property_id, p.property_code, p.monthly_rent
                    FROM tenants t
                    JOIN properties p ON t.property_id = p.id
                    WHERE t.tenant_code = ? AND t.is_active = 1
                    """,
                    (tenant_code,)
                )
                record = cursor.fetchone()
                if not record:
                    raise ValueError(f"Active tenant '{tenant_code}' not found or not assigned to an active property.")

                pay_ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
                cursor.execute(
                    """
                    INSERT INTO rent_payments (payment_ref, tenant_id, property_id, amount, payment_date, period_month, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (pay_ref, record["tenant_id"], record["property_id"], round(amount, 2), p_date, formatted_period, notes.strip())
                )
                pay_id = cursor.lastrowid
                return {
                    "id": pay_id,
                    "payment_ref": pay_ref,
                    "tenant_code": tenant_code,
                    "tenant_name": record["name"],
                    "property_code": record["property_code"],
                    "amount": round(amount, 2),
                    "period_month": formatted_period,
                    "payment_date": p_date,
                    "notes": notes.strip()
                }
        finally:
            conn.close()

    def get_tenant_balances(self, as_of_date: Optional[str] = None) -> List[Dict[str, Any]]:
        target_date = datetime.strptime(as_of_date, "%Y-%m-%d").date() if as_of_date else date.today()
        conn = get_connection(self.db_path)
        results = []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.id, t.tenant_code, t.name, t.email, t.phone, t.lease_start_date,
                       p.property_code, p.name as property_name, p.monthly_rent
                FROM tenants t
                JOIN properties p ON t.property_id = p.id
                WHERE t.is_active = 1
                ORDER BY t.name ASC
                """
            )
            tenants = cursor.fetchall()
            for t in tenants:
                lease_start = datetime.strptime(t["lease_start_date"], "%Y-%m-%d").date()
                if target_date < lease_start:
                    months_due = 0
                else:
                    months_due = (target_date.year - lease_start.year) * 12 + (target_date.month - lease_start.month) + 1

                total_expected = months_due * t["monthly_rent"]

                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM rent_payments WHERE tenant_id = ?", (t["id"],))
                total_paid = float(cursor.fetchone()[0])
                outstanding = max(0.0, round(total_expected - total_paid, 2))

                results.append({
                    "tenant_code": t["tenant_code"],
                    "name": t["name"],
                    "property_code": t["property_code"],
                    "monthly_rent": t["monthly_rent"],
                    "lease_start_date": t["lease_start_date"],
                    "months_due": months_due,
                    "total_expected": round(total_expected, 2),
                    "total_paid": round(total_paid, 2),
                    "outstanding_balance": outstanding,
                    "status": "Overdue" if outstanding > 0 else "Up-to-Date"
                })
            return results
        finally:
            conn.close()

    def list_properties(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.id, p.property_code, p.name, p.address, p.monthly_rent, p.status,
                       t.tenant_code, t.name as tenant_name, t.phone as tenant_phone
                FROM properties p
                LEFT JOIN tenants t ON t.property_id = p.id AND t.is_active = 1
            """
            params = []
            if status_filter:
                query += " WHERE p.status = ?"
                params.append(status_filter.capitalize())
            query += " ORDER BY p.property_code ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def search_tenants(self, query: str) -> List[Dict[str, Any]]:
        term = f"%{query.strip().lower()}%"
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.id, t.tenant_code, t.name, t.email, t.phone, t.lease_start_date, t.is_active,
                       p.property_code, p.name as property_name, p.monthly_rent
                FROM tenants t
                LEFT JOIN properties p ON t.property_id = p.id
                WHERE LOWER(t.name) LIKE ? OR LOWER(t.tenant_code) LIKE ?
                   OR LOWER(COALESCE(p.property_code, '')) LIKE ?
                   OR LOWER(COALESCE(p.name, '')) LIKE ?
                ORDER BY t.name ASC
                """,
                (term, term, term, term)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def generate_monthly_report(self, period_month: str) -> Dict[str, Any]:
        try:
            datetime.strptime(period_month.strip(), "%Y-%m")
            formatted_period = period_month.strip()
        except ValueError:
            raise ValueError("Period month must be in YYYY-MM format.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(monthly_rent), 0) FROM properties WHERE status = 'Occupied'")
            expected_rent = float(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0) FROM rent_payments
                WHERE period_month = ?
                """,
                (formatted_period,)
            )
            collected_rent = float(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT rp.payment_ref, rp.amount, rp.payment_date, t.name as tenant_name,
                       p.property_code, p.monthly_rent
                FROM rent_payments rp
                JOIN tenants t ON rp.tenant_id = t.id
                JOIN properties p ON rp.property_id = p.id
                WHERE rp.period_month = ?
                ORDER BY rp.payment_date ASC
                """,
                (formatted_period,)
            )
            payments = [dict(row) for row in cursor.fetchall()]

            collection_rate = (collected_rent / expected_rent * 100) if expected_rent > 0 else 0.0

            return {
                "period_month": formatted_period,
                "expected_rent": round(expected_rent, 2),
                "collected_rent": round(collected_rent, 2),
                "outstanding_deficit": max(0.0, round(expected_rent - collected_rent, 2)),
                "collection_rate_percent": round(collection_rate, 2),
                "payments_count": len(payments),
                "payments": payments
            }
        finally:
            conn.close()
