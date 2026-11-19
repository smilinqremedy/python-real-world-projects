"""
Business logic and service layer for Laundry Service Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class LaundryService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)
        self.seed_rates()

    def seed_rates(self) -> None:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM service_rates")
            if cursor.fetchone()[0] == 0:
                rates = [
                    ("Shirt", 3.50),
                    ("Trousers", 4.00),
                    ("Suit", 12.00),
                    ("Dress", 8.00),
                    ("Jacket", 7.50),
                    ("Bedding", 10.00),
                    ("Curtains", 15.00),
                ]
                with conn:
                    cursor.executemany("INSERT INTO service_rates (item_type, price_per_item) VALUES (?, ?)", rates)
        finally:
            conn.close()

    def get_service_rates(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM service_rates ORDER BY item_type ASC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def register_customer(self, code: str, name: str, phone: str, email: str = "") -> Dict[str, Any]:
        code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()
        if not code or not name or not phone:
            raise ValueError("Customer code, name, and phone cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO customers (customer_code, name, phone, email) VALUES (?, ?, ?, ?)",
                    (code, name, phone, email.strip())
                )
                return {
                    "id": cursor.lastrowid,
                    "customer_code": code,
                    "name": name,
                    "phone": phone,
                    "email": email.strip()
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Customer code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def create_order(self, customer_code: str, items: List[Dict[str, Any]], order_date_str: Optional[str] = None) -> Dict[str, Any]:
        if not items:
            raise ValueError("An order must contain at least one item.")

        order_date = order_date_str.strip() if order_date_str else str(date.today())
        try:
            datetime.strptime(order_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Order date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM customers WHERE customer_code = ?", (customer_code.strip().upper(),))
                cust = cursor.fetchone()
                if not cust:
                    raise ValueError(f"Customer with code '{customer_code}' not found.")

                # Validate and calculate charges
                total_items = 0
                total_charge = 0.0
                parsed_items = []

                for itm in items:
                    itype = itm.get("item_type", "").strip().capitalize()
                    qty = itm.get("quantity", 0)
                    if qty <= 0:
                        raise ValueError(f"Quantity for {itype} must be greater than zero.")

                    cursor.execute("SELECT price_per_item FROM service_rates WHERE LOWER(item_type) = LOWER(?)", (itype,))
                    rate_row = cursor.fetchone()
                    if not rate_row:
                        raise ValueError(f"Service rate for item type '{itype}' not defined.")

                    unit_price = float(rate_row["price_per_item"])
                    subtotal = round(qty * unit_price, 2)
                    total_items += qty
                    total_charge += subtotal
                    parsed_items.append((itype, qty, unit_price, subtotal))

                order_id_code = f"LND-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO orders (order_id, customer_id, total_items, total_charge, amount_paid, payment_status, status, order_date)
                    VALUES (?, ?, ?, ?, 0.0, 'Unpaid', 'Received', ?)
                    """,
                    (order_id_code, cust["id"], total_items, round(total_charge, 2), order_date)
                )
                db_order_id = cursor.lastrowid

                for p_type, p_qty, p_unit, p_sub in parsed_items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, item_type, quantity, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (db_order_id, p_type, p_qty, p_unit, p_sub)
                    )
        finally:
            conn.close()

        return self.get_order(order_id_code)

    def record_payment(self, order_id_code: str, amount: float,
                       payment_date_str: Optional[str] = None, method: str = "Cash") -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        pay_date = payment_date_str.strip() if payment_date_str else str(date.today())
        try:
            datetime.strptime(pay_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Payment date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, total_charge, amount_paid FROM orders WHERE order_id = ?", (order_id_code.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_id_code}' not found.")

                current_paid = float(order["amount_paid"])
                total_charge = float(order["total_charge"])
                balance = round(total_charge - current_paid, 2)

                if balance <= 0:
                    raise ValueError(f"Order '{order_id_code}' is already fully paid.")
                if round(amount, 2) > balance:
                    raise ValueError(f"Payment amount (${amount:.2f}) exceeds outstanding balance (${balance:.2f}).")

                new_paid = round(current_paid + amount, 2)
                new_status = "Paid" if new_paid >= total_charge else "Partial"

                pay_ref = f"PAY-LND-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO payments (payment_ref, order_id, amount, payment_date, payment_method)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (pay_ref, order["id"], round(amount, 2), pay_date, method.strip())
                )

                cursor.execute(
                    "UPDATE orders SET amount_paid = ?, payment_status = ? WHERE id = ?",
                    (new_paid, new_status, order["id"])
                )
        finally:
            conn.close()

        res = self.get_order(order_id_code)
        res["last_payment_ref"] = pay_ref
        return res

    def update_order_status(self, order_id_code: str, new_status: str) -> Dict[str, Any]:
        status_clean = new_status.strip().capitalize()
        valid_statuses = ["Received", "Washing", "Ready", "Collected"]
        if status_clean not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status, payment_status FROM orders WHERE order_id = ?", (order_id_code.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_id_code}' not found.")

                if status_clean == "Collected":
                    if order["payment_status"] != "Paid":
                        raise ValueError("Order cannot be marked as 'Collected' until payment is completed in full.")

                ready_clause = ", ready_date = CURRENT_DATE" if status_clean == "Ready" else ""
                collected_clause = ", collected_date = CURRENT_DATE" if status_clean == "Collected" else ""

                cursor.execute(
                    f"UPDATE orders SET status = ?{ready_clause}{collected_clause} WHERE id = ?",
                    (status_clean, order["id"])
                )
        finally:
            conn.close()

        return self.get_order(order_id_code)

    def get_order(self, order_id_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT o.*, c.customer_code, c.name as customer_name, c.phone as customer_phone
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.order_id = ?
                """,
                (order_id_code.strip().upper(),)
            )
            order = cursor.fetchone()
            if not order:
                raise ValueError(f"Order '{order_id_code}' not found.")

            cursor.execute(
                "SELECT item_type, quantity, unit_price, subtotal FROM order_items WHERE order_id = ? ORDER BY item_type ASC",
                (order["id"],)
            )
            items = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                "SELECT payment_ref, amount, payment_date, payment_method FROM payments WHERE order_id = ? ORDER BY id ASC",
                (order["id"],)
            )
            payments = [dict(r) for r in cursor.fetchall()]

            res = dict(order)
            res["items"] = items
            res["payments"] = payments
            res["outstanding_balance"] = max(0.0, round(float(order["total_charge"]) - float(order["amount_paid"]), 2))
            return res
        finally:
            conn.close()

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT o.order_id, o.order_date, o.total_items, o.total_charge, o.amount_paid,
                       o.payment_status, o.status, c.customer_code, c.name as customer_name, c.phone
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.status IN ('Received', 'Washing', 'Ready')
                ORDER BY o.id ASC
                """
            )
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_daily_revenue_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        report_date = target_date.strip() if target_date else str(date.today())
        try:
            datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Report date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM payments WHERE payment_date = ?", (report_date,))
            total_rev, total_payments = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(total_items), 0) FROM orders WHERE order_date = ?", (report_date,))
            orders_placed, items_processed = cursor.fetchone()

            cursor.execute(
                """
                SELECT p.payment_ref, p.amount, p.payment_method, o.order_id, c.name as customer_name
                FROM payments p
                JOIN orders o ON p.order_id = o.id
                JOIN customers c ON o.customer_id = c.id
                WHERE p.payment_date = ?
                ORDER BY p.id ASC
                """,
                (report_date,)
            )
            payment_list = [dict(r) for r in cursor.fetchall()]

            return {
                "report_date": report_date,
                "total_revenue": round(float(total_rev), 2),
                "total_payments_received": total_payments,
                "orders_placed_today": orders_placed,
                "items_processed_today": items_processed,
                "payments": payment_list
            }
        finally:
            conn.close()
