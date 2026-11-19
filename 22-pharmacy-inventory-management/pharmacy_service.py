"""
Business logic and inventory governance for Pharmacy Inventory and Sales Management System.
"""

from datetime import datetime, date, timedelta
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class PharmacyService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_medicine(self, code: str, name: str, category: str,
                          unit: str, reorder_level: int = 10) -> Dict[str, Any]:
        m_code = code.strip().upper()
        name = name.strip()
        cat = category.strip().capitalize()
        unit = unit.strip().capitalize()

        if not m_code or not name or not cat or not unit:
            raise ValueError("Medicine code, name, category, and unit cannot be empty.")
        if reorder_level < 0:
            raise ValueError("Reorder level cannot be negative.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO medicines (medicine_code, name, category, unit, reorder_level)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (m_code, name, cat, unit, reorder_level)
                )
                return {
                    "id": cursor.lastrowid,
                    "medicine_code": m_code,
                    "name": name,
                    "category": cat,
                    "unit": unit,
                    "reorder_level": reorder_level
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Medicine with code '{m_code}' already exists.")
            raise
        finally:
            conn.close()

    def record_medicine_purchase(self, medicine_code: str, batch_number: str,
                                 cost_price: float, selling_price: float, quantity: int,
                                 manufacture_date_str: str, expiry_date_str: str) -> Dict[str, Any]:
        b_num = batch_number.strip().upper()
        if not b_num:
            raise ValueError("Batch number cannot be empty.")
        if cost_price < 0 or selling_price < 0:
            raise ValueError("Prices cannot be negative.")
        if selling_price < cost_price:
            raise ValueError("Selling price cannot be less than purchase cost price.")
        if quantity <= 0:
            raise ValueError("Purchase quantity must be greater than zero.")

        try:
            m_date = datetime.strptime(manufacture_date_str.strip(), "%Y-%m-%d").date()
            e_date = datetime.strptime(expiry_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format.")

        if e_date <= m_date:
            raise ValueError("Expiry date must be after manufacture date.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM medicines WHERE medicine_code = ?", (medicine_code.strip().upper(),))
                med = cursor.fetchone()
                if not med:
                    raise ValueError(f"Medicine '{medicine_code}' not found.")

                cursor.execute(
                    """
                    INSERT INTO batches (medicine_id, batch_number, cost_price, selling_price,
                                         initial_quantity, current_quantity, manufacture_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (med["id"], b_num, round(cost_price, 2), round(selling_price, 2),
                     quantity, quantity, str(m_date), str(e_date))
                )
                return {
                    "id": cursor.lastrowid,
                    "medicine_code": medicine_code.strip().upper(),
                    "medicine_name": med["name"],
                    "batch_number": b_num,
                    "cost_price": round(cost_price, 2),
                    "selling_price": round(selling_price, 2),
                    "quantity": quantity,
                    "expiry_date": str(e_date)
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Batch with number '{b_num}' already exists.")
            raise
        finally:
            conn.close()

    def process_sale(self, batch_number: str, quantity: int,
                     sale_date_str: Optional[str] = None, customer_notes: str = "") -> Dict[str, Any]:
        b_num = batch_number.strip().upper()
        if quantity <= 0:
            raise ValueError("Sale quantity must be greater than zero.")

        s_date_str = sale_date_str.strip() if sale_date_str else str(date.today())
        try:
            s_date = datetime.strptime(s_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Sale date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT b.id, b.medicine_id, b.current_quantity, b.selling_price, b.expiry_date,
                           m.name as medicine_name, m.unit
                    FROM batches b
                    JOIN medicines m ON b.medicine_id = m.id
                    WHERE b.batch_number = ?
                    """,
                    (b_num,)
                )
                batch = cursor.fetchone()
                if not batch:
                    raise ValueError(f"Batch '{b_num}' not found.")

                # Expiry gate: Prevent expired products from being sold
                exp_date = datetime.strptime(batch["expiry_date"], "%Y-%m-%d").date()
                if exp_date < s_date:
                    raise ValueError(f"Sale rejected! Batch '{b_num}' of {batch['medicine_name']} expired on {batch['expiry_date']}. Expired medicines cannot be sold.")

                # Stock check
                if quantity > batch["current_quantity"]:
                    raise ValueError(f"Insufficient stock! Requested {quantity} {batch['unit']}, but only {batch['current_quantity']} available in batch '{b_num}'.")

                unit_price = float(batch["selling_price"])
                total_price = round(quantity * unit_price, 2)
                receipt_num = f"PHARM-{uuid.uuid4().hex[:6].upper()}"

                # Atomically update batch quantity
                new_qty = batch["current_quantity"] - quantity
                cursor.execute("UPDATE batches SET current_quantity = ? WHERE id = ?", (new_qty, batch["id"]))

                # Record sale
                cursor.execute(
                    """
                    INSERT INTO sales (receipt_number, batch_id, medicine_id, quantity, unit_price, total_price, sale_date, customer_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (receipt_num, batch["id"], batch["medicine_id"], quantity, unit_price, total_price, s_date_str, customer_notes.strip())
                )
                return {
                    "receipt_number": receipt_num,
                    "batch_number": b_num,
                    "medicine_name": batch["medicine_name"],
                    "quantity": quantity,
                    "unit": batch["unit"],
                    "unit_price": unit_price,
                    "total_price": total_price,
                    "remaining_batch_stock": new_qty,
                    "sale_date": s_date_str
                }
        finally:
            conn.close()

    def get_low_stock_medicines(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT m.id, m.medicine_code, m.name, m.category, m.unit, m.reorder_level,
                       COALESCE(SUM(b.current_quantity), 0) as total_stock
                FROM medicines m
                LEFT JOIN batches b ON m.id = b.medicine_id
                GROUP BY m.id
                HAVING total_stock <= m.reorder_level
                ORDER BY total_stock ASC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def get_expiry_alerts(self, days_threshold: int = 30, as_of_date_str: Optional[str] = None) -> Dict[str, Any]:
        target_date = datetime.strptime(as_of_date_str.strip(), "%Y-%m-%d").date() if as_of_date_str else date.today()
        warning_limit = target_date + timedelta(days=days_threshold)

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT b.batch_number, b.current_quantity, b.expiry_date,
                       m.medicine_code, m.name as medicine_name, m.unit
                FROM batches b
                JOIN medicines m ON b.medicine_id = m.id
                WHERE b.current_quantity > 0 AND b.expiry_date < ?
                ORDER BY b.expiry_date ASC
                """,
                (str(target_date),)
            )
            expired = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT b.batch_number, b.current_quantity, b.expiry_date,
                       m.medicine_code, m.name as medicine_name, m.unit
                FROM batches b
                JOIN medicines m ON b.medicine_id = m.id
                WHERE b.current_quantity > 0 AND b.expiry_date >= ? AND b.expiry_date <= ?
                ORDER BY b.expiry_date ASC
                """,
                (str(target_date), str(warning_limit))
            )
            approaching = [dict(r) for r in cursor.fetchall()]

            return {
                "check_date": str(target_date),
                "expired_batches": expired,
                "approaching_expiry_batches": approaching
            }
        finally:
            conn.close()

    def list_inventory(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT b.id, b.batch_number, b.current_quantity, b.cost_price, b.selling_price, b.expiry_date,
                       m.medicine_code, m.name as medicine_name, m.category, m.unit
                FROM batches b
                JOIN medicines m ON b.medicine_id = m.id
                ORDER BY m.name ASC, b.expiry_date ASC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_sales_report(self, target_date: Optional[str] = None, target_month: Optional[str] = None) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            where_clauses = []
            params = []
            if target_date:
                where_clauses.append("s.sale_date = ?")
                params.append(target_date.strip())
            elif target_month:
                where_clauses.append("s.sale_date LIKE ?")
                params.append(f"{target_month.strip()}%")

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            cursor.execute(
                f"""
                SELECT COUNT(*) as transactions_count,
                       COALESCE(SUM(s.quantity), 0) as total_units_sold,
                       COALESCE(SUM(s.total_price), 0) as total_revenue
                FROM sales s
                {where_str}
                """,
                params
            )
            overall = cursor.fetchone()

            cursor.execute(
                f"""
                SELECT m.name as medicine_name, m.category, SUM(s.quantity) as units_sold, SUM(s.total_price) as revenue
                FROM sales s
                JOIN medicines m ON s.medicine_id = m.id
                {where_str}
                GROUP BY m.id
                ORDER BY revenue DESC
                """,
                params
            )
            by_medicine = [dict(r) for r in cursor.fetchall()]

            period_desc = target_date or target_month or "All Time"
            return {
                "period": period_desc,
                "transactions_count": overall["transactions_count"],
                "total_units_sold": overall["total_units_sold"],
                "total_revenue": round(float(overall["total_revenue"]), 2),
                "sales_breakdown": by_medicine
            }
        finally:
            conn.close()
