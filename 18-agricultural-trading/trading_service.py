"""
Service layer and trading logic for Agricultural Produce Trading System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class TradingService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_farmer(self, code: str, name: str, location: str, phone: str) -> Dict[str, Any]:
        f_code = code.strip().upper()
        name = name.strip()
        location = location.strip()
        phone = phone.strip()

        if not f_code or not name or not location or not phone:
            raise ValueError("Farmer code, name, location, and phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO farmers (farmer_code, name, location, phone) VALUES (?, ?, ?, ?)",
                    (f_code, name, location, phone)
                )
                return {
                    "id": cursor.lastrowid,
                    "farmer_code": f_code,
                    "name": name,
                    "location": location,
                    "phone": phone
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Farmer with code '{f_code}' already exists.")
            raise
        finally:
            conn.close()

    def register_buyer(self, code: str, name: str, phone: str, company: str = "") -> Dict[str, Any]:
        b_code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()

        if not b_code or not name or not phone:
            raise ValueError("Buyer code, name, and phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO buyers (buyer_code, name, company, phone) VALUES (?, ?, ?, ?)",
                    (b_code, name, company.strip(), phone)
                )
                return {
                    "id": cursor.lastrowid,
                    "buyer_code": b_code,
                    "name": name,
                    "company": company.strip(),
                    "phone": phone
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Buyer with code '{b_code}' already exists.")
            raise
        finally:
            conn.close()

    def add_produce(self, farmer_code: str, produce_code: str, name: str,
                    category: str, unit: str, quantity: float, price_per_unit: float) -> Dict[str, Any]:
        p_code = produce_code.strip().upper()
        p_name = name.strip()
        p_cat = category.strip().capitalize()
        p_unit = unit.strip().lower()

        if not p_code or not p_name or not p_cat or not p_unit:
            raise ValueError("Produce code, name, category, and unit cannot be empty.")
        if quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if price_per_unit <= 0:
            raise ValueError("Price per unit must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM farmers WHERE farmer_code = ?", (farmer_code.strip().upper(),))
                farmer = cursor.fetchone()
                if not farmer:
                    raise ValueError(f"Farmer '{farmer_code}' not found.")

                cursor.execute(
                    """
                    INSERT INTO produce (produce_code, farmer_id, name, category, unit, available_quantity, price_per_unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (p_code, farmer["id"], p_name, p_cat, p_unit, round(quantity, 2), round(price_per_unit, 2))
                )
                return {
                    "id": cursor.lastrowid,
                    "produce_code": p_code,
                    "farmer_code": farmer_code.strip().upper(),
                    "name": p_name,
                    "category": p_cat,
                    "unit": p_unit,
                    "available_quantity": round(quantity, 2),
                    "price_per_unit": round(price_per_unit, 2)
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Produce with code '{p_code}' already exists.")
            raise
        finally:
            conn.close()

    def restock_produce(self, produce_code: str, additional_quantity: float) -> Dict[str, Any]:
        if additional_quantity <= 0:
            raise ValueError("Restock quantity must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, available_quantity FROM produce WHERE produce_code = ?", (produce_code.strip().upper(),))
                p = cursor.fetchone()
                if not p:
                    raise ValueError(f"Produce '{produce_code}' not found.")

                new_qty = round(p["available_quantity"] + additional_quantity, 2)
                cursor.execute("UPDATE produce SET available_quantity = ? WHERE id = ?", (new_qty, p["id"]))
        finally:
            conn.close()

        return self.get_produce_by_code(produce_code)

    def process_purchase(self, buyer_code: str, produce_code: str, quantity: float,
                         sale_date_str: Optional[str] = None) -> Dict[str, Any]:
        if quantity <= 0:
            raise ValueError("Purchase quantity must be greater than zero.")

        s_date = sale_date_str.strip() if sale_date_str else str(date.today())
        try:
            datetime.strptime(s_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Sale date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM buyers WHERE buyer_code = ?", (buyer_code.strip().upper(),))
                buyer = cursor.fetchone()
                if not buyer:
                    raise ValueError(f"Buyer '{buyer_code}' not found.")

                cursor.execute(
                    """
                    SELECT p.id, p.name, p.unit, p.available_quantity, p.price_per_unit, f.name as farmer_name
                    FROM produce p
                    JOIN farmers f ON p.farmer_id = f.id
                    WHERE p.produce_code = ?
                    """,
                    (produce_code.strip().upper(),)
                )
                prod = cursor.fetchone()
                if not prod:
                    raise ValueError(f"Produce '{produce_code}' not found.")

                avail = float(prod["available_quantity"])
                if round(quantity, 2) > avail:
                    raise ValueError(f"Insufficient stock for '{prod['name']}'. Requested {quantity} {prod['unit']}, but only {avail} {prod['unit']} available.")

                new_stock = round(avail - quantity, 2)
                unit_price = float(prod["price_per_unit"])
                total_price = round(quantity * unit_price, 2)
                invoice_num = f"AGR-{uuid.uuid4().hex[:6].upper()}"

                # Update stock
                cursor.execute("UPDATE produce SET available_quantity = ? WHERE id = ?", (new_stock, prod["id"]))

                # Insert transaction
                cursor.execute(
                    """
                    INSERT INTO sales_transactions (invoice_number, buyer_id, produce_id, quantity, unit_price, total_price, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (invoice_num, buyer["id"], prod["id"], round(quantity, 2), unit_price, total_price, s_date)
                )
                return {
                    "invoice_number": invoice_num,
                    "buyer_name": buyer["name"],
                    "produce_name": prod["name"],
                    "farmer_name": prod["farmer_name"],
                    "quantity": round(quantity, 2),
                    "unit": prod["unit"],
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "remaining_stock": new_stock,
                    "sale_date": s_date
                }
        finally:
            conn.close()

    def get_produce_by_code(self, produce_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, f.farmer_code, f.name as farmer_name, f.location as farmer_location
                FROM produce p
                JOIN farmers f ON p.farmer_id = f.id
                WHERE p.produce_code = ?
                """,
                (produce_code.strip().upper(),)
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Produce '{produce_code}' not found.")
            return dict(row)
        finally:
            conn.close()

    def list_produce_inventory(self, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT p.*, f.farmer_code, f.name as farmer_name, f.location as farmer_location
                FROM produce p
                JOIN farmers f ON p.farmer_id = f.id
            """
            params = []
            if category_filter:
                query += " WHERE LOWER(p.category) = LOWER(?)"
                params.append(category_filter.strip())
            query += " ORDER BY p.category ASC, p.name ASC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_sales_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            where_clauses = []
            params = []
            if start_date:
                where_clauses.append("t.sale_date >= ?")
                params.append(start_date.strip())
            if end_date:
                where_clauses.append("t.sale_date <= ?")
                params.append(end_date.strip())

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            cursor.execute(
                f"""
                SELECT COUNT(*) as transaction_count,
                       COALESCE(SUM(t.quantity), 0) as total_volume_sold,
                       COALESCE(SUM(t.total_price), 0) as total_revenue
                FROM sales_transactions t
                {where_str}
                """,
                params
            )
            overall = cursor.fetchone()

            cursor.execute(
                f"""
                SELECT p.name as produce_name, p.unit, SUM(t.quantity) as volume_sold, SUM(t.total_price) as revenue
                FROM sales_transactions t
                JOIN produce p ON t.produce_id = p.id
                {where_str}
                GROUP BY p.id
                ORDER BY revenue DESC
                """,
                params
            )
            by_produce = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                f"""
                SELECT b.name as buyer_name, b.company, COUNT(t.id) as purchases_count, SUM(t.total_price) as spent
                FROM sales_transactions t
                JOIN buyers b ON t.buyer_id = b.id
                {where_str}
                GROUP BY b.id
                ORDER BY spent DESC
                """,
                params
            )
            by_buyer = [dict(r) for r in cursor.fetchall()]

            return {
                "period": f"{start_date or 'Beginning'} to {end_date or 'Present'}",
                "transaction_count": overall["transaction_count"],
                "total_volume_sold": round(float(overall["total_volume_sold"]), 2),
                "total_revenue": round(float(overall["total_revenue"]), 2),
                "sales_by_produce": by_produce,
                "sales_by_buyer": by_buyer
            }
        finally:
            conn.close()
