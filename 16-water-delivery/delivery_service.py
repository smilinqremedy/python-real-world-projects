"""
Business logic and operations for Water Delivery Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class DeliveryService:
    CONTAINER_PRICES = {
        "20L Jug": 4.50,
        "10L Dispenser": 3.00,
        "5L Bottle Pack": 6.00
    }
    STANDARD_DELIVERY_FEE = 3.00
    FREE_DELIVERY_THRESHOLD = 10  # orders with >= 10 containers get free delivery

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_customer(self, code: str, name: str, phone: str, default_address: str) -> Dict[str, Any]:
        c_code = code.strip().upper()
        c_name = name.strip()
        c_phone = phone.strip()
        c_addr = default_address.strip()

        if not c_code or not c_name or not c_phone or not c_addr:
            raise ValueError("Customer code, name, phone, and delivery address cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO customers (customer_code, name, phone, default_address)
                    VALUES (?, ?, ?, ?)
                    """,
                    (c_code, c_name, c_phone, c_addr)
                )
                return {
                    "id": cursor.lastrowid,
                    "customer_code": c_code,
                    "name": c_name,
                    "phone": c_phone,
                    "default_address": c_addr
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Customer code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def register_driver(self, code: str, name: str, phone: str, vehicle_plate: str) -> Dict[str, Any]:
        d_code = code.strip().upper()
        d_name = name.strip()
        d_phone = phone.strip()
        plate = vehicle_plate.strip().upper()

        if not d_code or not d_name or not plate:
            raise ValueError("Driver code, name, and vehicle plate cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO drivers (driver_code, name, phone, vehicle_plate, is_active)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (d_code, d_name, d_phone, plate)
                )
                return {
                    "id": cursor.lastrowid,
                    "driver_code": d_code,
                    "name": d_name,
                    "phone": d_phone,
                    "vehicle_plate": plate,
                    "is_active": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Driver code '{d_code}' already exists.")
            raise
        finally:
            conn.close()

    def create_order(self, customer_code: str, container_type: str, quantity: int,
                     delivery_address: Optional[str] = None, order_date_str: Optional[str] = None,
                     notes: str = "") -> Dict[str, Any]:
        if quantity <= 0:
            raise ValueError("Container quantity must be greater than zero.")

        ctype = container_type.strip()
        if ctype not in self.CONTAINER_PRICES:
            valid_types = ", ".join(self.CONTAINER_PRICES.keys())
            raise ValueError(f"Invalid container type '{container_type}'. Choose from: {valid_types}")

        unit_price = self.CONTAINER_PRICES[ctype]
        delivery_fee = 0.0 if quantity >= self.FREE_DELIVERY_THRESHOLD else self.STANDARD_DELIVERY_FEE
        total_charge = round(quantity * unit_price + delivery_fee, 2)

        o_date = order_date_str.strip() if order_date_str else str(date.today())
        try:
            datetime.strptime(o_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Order date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, default_address FROM customers WHERE customer_code = ?", (customer_code.strip().upper(),))
                cust = cursor.fetchone()
                if not cust:
                    raise ValueError(f"Customer '{customer_code}' not found.")

                addr = delivery_address.strip() if delivery_address and delivery_address.strip() else cust["default_address"]
                if not addr:
                    raise ValueError("Delivery address cannot be empty.")

                order_num = f"WTR-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO orders (order_number, customer_id, delivery_address, container_type, quantity, container_unit_price, delivery_fee, total_charge, status, order_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
                    """,
                    (order_num, cust["id"], addr, ctype, quantity, unit_price, delivery_fee, total_charge, o_date, notes.strip())
                )
        finally:
            conn.close()

        return self.get_order(order_num)

    def assign_driver(self, order_number: str, driver_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["status"] == "Delivered":
                    raise ValueError("Cannot reassign a delivered order.")

                cursor.execute("SELECT id, name, is_active FROM drivers WHERE driver_code = ?", (driver_code.strip().upper(),))
                driver = cursor.fetchone()
                if not driver:
                    raise ValueError(f"Driver '{driver_code}' not found.")
                if not driver["is_active"]:
                    raise ValueError(f"Driver '{driver_code}' is currently inactive.")

                cursor.execute(
                    "UPDATE orders SET driver_id = ?, status = 'Assigned' WHERE id = ?",
                    (driver["id"], order["id"])
                )
        finally:
            conn.close()

        return self.get_order(order_number)

    def update_delivery_status(self, order_number: str, new_status: str) -> Dict[str, Any]:
        status_map = {
            "pending": "Pending",
            "assigned": "Assigned",
            "out for delivery": "Out for Delivery",
            "delivered": "Delivered",
            "cancelled": "Cancelled"
        }
        status_clean = status_map.get(new_status.strip().lower())
        if not status_clean:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: Pending, Assigned, Out for Delivery, Delivered, Cancelled")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, driver_id, status FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")

                if status_clean in ["Out for Delivery", "Delivered"] and not order["driver_id"]:
                    raise ValueError("Cannot mark order as 'Out for Delivery' or 'Delivered' without an assigned driver.")

                deliv_clause = ", delivered_at = CURRENT_TIMESTAMP" if status_clean == "Delivered" else ""
                cursor.execute(f"UPDATE orders SET status = ?{deliv_clause} WHERE id = ?", (status_clean, order["id"]))
        finally:
            conn.close()

        return self.get_order(order_number)

    def record_payment(self, order_number: str, method: str = "Cash") -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status, total_charge FROM orders WHERE order_number = ?", (order_number.strip().upper(),))
                order = cursor.fetchone()
                if not order:
                    raise ValueError(f"Order '{order_number}' not found.")
                if order["payment_status"] == "Paid":
                    raise ValueError(f"Order '{order_number}' has already been paid.")

                cursor.execute(
                    "UPDATE orders SET payment_status = 'Paid', payment_method = ? WHERE id = ?",
                    (method.strip().capitalize(), order["id"])
                )
        finally:
            conn.close()

        return self.get_order(order_number)

    def get_order(self, order_number: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT o.*, c.customer_code, c.name as customer_name, c.phone as customer_phone,
                       d.driver_code, d.name as driver_name, d.vehicle_plate
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                LEFT JOIN drivers d ON o.driver_id = d.id
                WHERE o.order_number = ?
                """,
                (order_number.strip().upper(),)
            )
            order = cursor.fetchone()
            if not order:
                raise ValueError(f"Order '{order_number}' not found.")
            return dict(order)
        finally:
            conn.close()

    def get_deliveries(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT o.*, c.customer_code, c.name as customer_name, c.phone as customer_phone,
                       d.driver_code, d.name as driver_name
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                LEFT JOIN drivers d ON o.driver_id = d.id
            """
            params = []
            if status_filter == "Pending":
                query += " WHERE o.status IN ('Pending', 'Assigned', 'Out for Delivery')"
            elif status_filter == "Completed":
                query += " WHERE o.status = 'Delivered'"
            elif status_filter:
                query += " WHERE o.status = ?"
                params.append(status_filter)

            query += " ORDER BY o.id DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def list_drivers(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers ORDER BY driver_code ASC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_daily_sales_report(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        rep_date = target_date.strip() if target_date else str(date.today())
        try:
            datetime.strptime(rep_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Report date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as orders_count,
                       COALESCE(SUM(quantity), 0) as total_containers,
                       COALESCE(SUM(total_charge), 0) as total_revenue
                FROM orders
                WHERE order_date = ? AND payment_status = 'Paid'
                """,
                (rep_date,)
            )
            summary = cursor.fetchone()

            cursor.execute(
                """
                SELECT container_type, SUM(quantity) as containers_sold, SUM(total_charge) as revenue
                FROM orders
                WHERE order_date = ? AND payment_status = 'Paid'
                GROUP BY container_type
                ORDER BY containers_sold DESC
                """,
                (rep_date,)
            )
            by_type = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT d.name as driver_name, COUNT(o.id) as deliveries_completed
                FROM orders o
                JOIN drivers d ON o.driver_id = d.id
                WHERE o.order_date = ? AND o.status = 'Delivered'
                GROUP BY d.id
                ORDER BY deliveries_completed DESC
                """,
                (rep_date,)
            )
            driver_stats = [dict(r) for r in cursor.fetchall()]

            return {
                "report_date": rep_date,
                "paid_orders_count": summary["orders_count"],
                "total_containers_sold": summary["total_containers"],
                "total_revenue": round(float(summary["total_revenue"]), 2),
                "breakdown_by_container": by_type,
                "driver_deliveries": driver_stats
            }
        finally:
            conn.close()
