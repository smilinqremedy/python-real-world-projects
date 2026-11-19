"""
Service logic for Restaurant Order Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class OrderService:
    TAX_RATE = 0.05  # 5% sales tax

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)
        self.seed_sample_menu()

    def seed_sample_menu(self) -> None:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM menu_items")
            if cursor.fetchone()[0] == 0:
                sample_items = [
                    ("M-101", "Classic Cheeseburger", "Main", 12.50),
                    ("M-102", "Margherita Pizza", "Main", 14.00),
                    ("M-103", "Creamy Alfredo Pasta", "Main", 13.50),
                    ("M-104", "Crispy Caesar Salad", "Appetizer", 8.00),
                    ("M-105", "Garlic Butter Breadsticks", "Appetizer", 6.50),
                    ("M-106", "Chocolate Lava Cake", "Dessert", 7.00),
                    ("M-107", "Iced Lemon Mint Tea", "Drink", 4.00),
                    ("M-108", "Fresh Berry Smoothie", "Drink", 5.50),
                ]
                with conn:
                    cursor.executemany(
                        """
                        INSERT INTO menu_items (item_code, name, category, price, is_available)
                        VALUES (?, ?, ?, ?, 1)
                        """,
                        sample_items
                    )
        finally:
            conn.close()

    def add_menu_item(self, code: str, name: str, category: str, price: float) -> Dict[str, Any]:
        code = code.strip().upper()
        name = name.strip()
        category = category.strip().capitalize()
        if not code or not name:
            raise ValueError("Item code and name cannot be empty.")
        if price <= 0:
            raise ValueError("Price must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO menu_items (item_code, name, category, price, is_available)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (code, name, category, round(price, 2))
                )
                return {
                    "id": cursor.lastrowid,
                    "item_code": code,
                    "name": name,
                    "category": category,
                    "price": round(price, 2),
                    "is_available": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Menu item code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def get_menu(self, available_only: bool = True) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM menu_items"
            if available_only:
                query += " WHERE is_available = 1"
            query += " ORDER BY category ASC, name ASC"
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def create_order(self, customer_name: str, table_number: str) -> Dict[str, Any]:
        c_name = customer_name.strip()
        table = table_number.strip()
        if not c_name or not table:
            raise ValueError("Customer name and table number cannot be empty.")

        order_num = f"ORD-{uuid.uuid4().hex[:6].upper()}"
        today = str(date.today())

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, customer_name, table_number, order_date)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_num, c_name, table, today)
                )
                return {
                    "id": cursor.lastrowid,
                    "order_number": order_num,
                    "customer_name": c_name,
                    "table_number": table,
                    "order_date": today,
                    "subtotal": 0.0,
                    "discount_percent": 0.0,
                    "discount_amount": 0.0,
                    "tax_amount": 0.0,
                    "total_bill": 0.0,
                    "payment_status": "Unpaid",
                    "order_status": "Pending"
                }
        finally:
            conn.close()

    def _recalculate_bill(self, conn: Any, order_id: int) -> None:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(item_total), 0) FROM order_items WHERE order_id = ?", (order_id,))
        subtotal = float(cursor.fetchone()[0])

        cursor.execute("SELECT discount_percent FROM orders WHERE id = ?", (order_id,))
        discount_percent = float(cursor.fetchone()[0])

        discount_amount = round(subtotal * (discount_percent / 100.0), 2)
        net_after_discount = max(0.0, subtotal - discount_amount)
        tax_amount = round(net_after_discount * self.TAX_RATE, 2)
        total_bill = round(net_after_discount + tax_amount, 2)

        cursor.execute(
            """
            UPDATE orders
            SET subtotal = ?, discount_amount = ?, tax_amount = ?, total_bill = ?
            WHERE id = ?
            """,
            (subtotal, discount_amount, tax_amount, total_bill, order_id)
        )

    def add_meal_to_order(self, order_number: str, item_code: str, quantity: int) -> Dict[str, Any]:
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status, order_status FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["payment_status"] == "Paid" or order["order_status"] == "Completed":
                    raise ValueError("Cannot modify an order that has already been paid or completed.")

                cursor.execute("SELECT id, name, price, is_available FROM menu_items WHERE item_code = ?", (item_code.strip().upper(),))
                item = cursor.fetchone()
                if not item:
                    raise ValueError(f"Menu item '{item_code}' not found.")
                if not item["is_available"]:
                    raise ValueError(f"Menu item '{item['name']}' is currently unavailable.")

                order_id = order["id"]
                menu_id = item["id"]
                unit_price = item["price"]

                cursor.execute("SELECT id, quantity FROM order_items WHERE order_id = ? AND menu_item_id = ?", (order_id, menu_id))
                existing = cursor.fetchone()
                if existing:
                    new_qty = existing["quantity"] + quantity
                    new_total = round(new_qty * unit_price, 2)
                    cursor.execute("UPDATE order_items SET quantity = ?, item_total = ? WHERE id = ?", (new_qty, new_total, existing["id"]))
                else:
                    item_total = round(quantity * unit_price, 2)
                    cursor.execute(
                        """
                        INSERT INTO order_items (order_id, menu_item_id, quantity, unit_price, item_total)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (order_id, menu_id, quantity, unit_price, item_total)
                    )

                self._recalculate_bill(conn, order_id)
        finally:
            conn.close()
        return self.get_order_details(order_number)

    def change_item_quantity(self, order_number: str, item_code: str, new_quantity: int) -> Dict[str, Any]:
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["payment_status"] == "Paid":
                    raise ValueError("Cannot change items on a paid order.")

                order_id = order["id"]
                cursor.execute("SELECT id, price FROM menu_items WHERE item_code = ?", (item_code.strip().upper(),))
                menu_item = cursor.fetchone()
                if not menu_item:
                    raise ValueError(f"Menu item '{item_code}' not found.")

                if new_quantity == 0:
                    cursor.execute("DELETE FROM order_items WHERE order_id = ? AND menu_item_id = ?", (order_id, menu_item["id"]))
                else:
                    new_total = round(new_quantity * menu_item["price"], 2)
                    cursor.execute(
                        """
                        UPDATE order_items
                        SET quantity = ?, item_total = ?
                        WHERE order_id = ? AND menu_item_id = ?
                        """,
                        (new_quantity, new_total, order_id, menu_item["id"])
                    )

                self._recalculate_bill(conn, order_id)
        finally:
            conn.close()
        return self.get_order_details(order_number)

    def remove_item_from_order(self, order_number: str, item_code: str) -> Dict[str, Any]:
        return self.change_item_quantity(order_number, item_code, 0)

    def apply_discount(self, order_number: str, discount_percent: float) -> Dict[str, Any]:
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("Discount percentage must be between 0 and 100.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["payment_status"] == "Paid":
                    raise ValueError("Cannot apply discount to a paid order.")

                order_id = order["id"]
                cursor.execute("UPDATE orders SET discount_percent = ? WHERE id = ?", (round(discount_percent, 2), order_id))
                self._recalculate_bill(conn, order_id)
        finally:
            conn.close()
        return self.get_order_details(order_number)

    def record_payment(self, order_number: str, amount_tendered: float) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, total_bill, payment_status, subtotal FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["subtotal"] <= 0:
                    raise ValueError("Cannot process payment for an empty order.")
                if order["payment_status"] == "Paid":
                    raise ValueError("This order has already been paid.")

                total_bill = order["total_bill"]
                if round(amount_tendered, 2) < total_bill:
                    raise ValueError(f"Insufficient payment. Total bill is ${total_bill:.2f}, but received ${amount_tendered:.2f}.")

                change = round(amount_tendered - total_bill, 2)
                cursor.execute(
                    """
                    UPDATE orders
                    SET payment_status = 'Paid', amount_paid = ?, order_status = 'Completed'
                    WHERE id = ?
                    """,
                    (round(amount_tendered, 2), order["id"])
                )
        finally:
            conn.close()

        details = self.get_order_details(order_number)
        details["change"] = change
        return details

    def get_order_details(self, order_number: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
            order = cursor.fetchone()
            if not order:
                raise ValueError(f"Order '{order_number}' not found.")

            cursor.execute(
                """
                SELECT oi.id, m.item_code, m.name, oi.quantity, oi.unit_price, oi.item_total
                FROM order_items oi
                JOIN menu_items m ON oi.menu_item_id = m.id
                WHERE oi.order_id = ?
                ORDER BY m.name ASC
                """,
                (order["id"],)
            )
            items = [dict(r) for r in cursor.fetchall()]
            result = dict(order)
            result["items"] = items
            return result
        finally:
            conn.close()

    def get_orders(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM orders"
            params = []
            if status_filter:
                query += " WHERE order_status = ?"
                params.append(status_filter.capitalize())
            query += " ORDER BY id DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_daily_sales_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        report_date = target_date.strip() if target_date else str(date.today())
        try:
            datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Report date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as total_orders,
                       COALESCE(SUM(total_bill), 0) as total_revenue,
                       COALESCE(SUM(tax_amount), 0) as total_tax,
                       COALESCE(SUM(discount_amount), 0) as total_discounts
                FROM orders
                WHERE order_date = ? AND payment_status = 'Paid'
                """,
                (report_date,)
            )
            stats = cursor.fetchone()

            cursor.execute(
                """
                SELECT m.name, SUM(oi.quantity) as units_sold, SUM(oi.item_total) as revenue
                FROM order_items oi
                JOIN menu_items m ON oi.menu_item_id = m.id
                JOIN orders o ON oi.order_id = o.id
                WHERE o.order_date = ? AND o.payment_status = 'Paid'
                GROUP BY m.id
                ORDER BY units_sold DESC
                LIMIT 5
                """,
                (report_date,)
            )
            top_items = [dict(r) for r in cursor.fetchall()]

            return {
                "report_date": report_date,
                "total_completed_orders": stats["total_orders"],
                "total_revenue": round(float(stats["total_revenue"]), 2),
                "total_tax": round(float(stats["total_tax"]), 2),
                "total_discounts": round(float(stats["total_discounts"]), 2),
                "top_items": top_items
            }
        finally:
            conn.close()
