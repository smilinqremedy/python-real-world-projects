"""
Business logic and shipment tracking services for Logistics and Shipment Tracking System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class LogisticsService:
    TIER_RATES = {
        "Standard": {"base": 5.00, "per_kg": 2.00},
        "Express": {"base": 10.00, "per_kg": 3.50},
        "Overnight": {"base": 20.00, "per_kg": 5.00}
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def calculate_delivery_charge(self, weight_kg: float, tier: str = "Standard") -> float:
        if weight_kg <= 0:
            raise ValueError("Parcel weight must be greater than zero.")
        tier_clean = tier.strip().capitalize()
        if tier_clean not in self.TIER_RATES:
            allowed = ", ".join(self.TIER_RATES.keys())
            raise ValueError(f"Invalid shipping tier '{tier}'. Allowed: {allowed}")

        rates = self.TIER_RATES[tier_clean]
        charge = rates["base"] + (weight_kg * rates["per_kg"])
        return round(charge, 2)

    def register_customer(self, code: str, name: str, phone: str,
                          email: str = "", address: str = "") -> Dict[str, Any]:
        c_code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()
        addr = address.strip()

        if not c_code or not name or not phone or not addr:
            raise ValueError("Customer code, name, phone, and address cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO customers (customer_code, name, phone, email, address)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (c_code, name, phone, email.strip(), addr)
                )
                return {
                    "id": cursor.lastrowid,
                    "customer_code": c_code,
                    "name": name,
                    "phone": phone,
                    "email": email.strip(),
                    "address": addr
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Customer with code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def register_courier(self, code: str, name: str, phone: str, vehicle_type: str) -> Dict[str, Any]:
        c_code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()
        veh = vehicle_type.strip().capitalize()

        if not c_code or not name or not phone or not veh:
            raise ValueError("Courier code, name, phone, and vehicle type cannot be empty.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO couriers (courier_code, name, phone, vehicle_type, is_active)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (c_code, name, phone, veh)
                )
                return {
                    "id": cursor.lastrowid,
                    "courier_code": c_code,
                    "name": name,
                    "phone": phone,
                    "vehicle_type": veh,
                    "is_active": 1
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Courier with code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def create_shipment(self, sender_code: str, receiver_name: str, receiver_phone: str,
                        receiver_address: str, destination_city: str, parcel_description: str,
                        weight_kg: float, shipping_tier: str = "Standard",
                        origin_hub: str = "Central Sorting Facility",
                        created_date_str: Optional[str] = None) -> Dict[str, Any]:
        r_name = receiver_name.strip()
        r_phone = receiver_phone.strip()
        r_addr = receiver_address.strip()
        dest_city = destination_city.strip()
        desc = parcel_description.strip()
        tier_clean = shipping_tier.strip().capitalize()

        if not r_name or not r_phone or not r_addr or not dest_city or not desc:
            raise ValueError("Receiver name, phone, address, destination city, and parcel description cannot be empty.")

        delivery_fee = self.calculate_delivery_charge(weight_kg, tier_clean)

        c_date = created_date_str.strip() if created_date_str else str(date.today())
        try:
            datetime.strptime(c_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Creation date must be in YYYY-MM-DD format.")

        tracking_num = f"TRK-{uuid.uuid4().hex[:8].upper()}"

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM customers WHERE customer_code = ?", (sender_code.strip().upper(),))
                sender = cursor.fetchone()
                if not sender:
                    raise ValueError(f"Sender customer '{sender_code}' not found.")

                cursor.execute(
                    """
                    INSERT INTO shipments (tracking_number, sender_id, receiver_name, receiver_phone,
                                           receiver_address, destination_city, parcel_description,
                                           weight_kg, shipping_tier, delivery_fee, status, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Created', ?)
                    """,
                    (tracking_num, sender["id"], r_name, r_phone, r_addr, dest_city, desc,
                     round(weight_kg, 2), tier_clean, delivery_fee, c_date)
                )
                shipment_id = cursor.lastrowid

                # Initial milestone
                cursor.execute(
                    """
                    INSERT INTO tracking_milestones (shipment_id, location, status_update, remarks)
                    VALUES (?, ?, 'Created', ?)
                    """,
                    (shipment_id, origin_hub.strip(), f"Shipment booked by sender [{desc}, {weight_kg}kg]")
                )
        finally:
            conn.close()

        return self.get_shipment_details(tracking_num)

    def assign_courier(self, tracking_number: str, courier_code: str) -> Dict[str, Any]:
        trk = tracking_number.strip().upper()
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status FROM shipments WHERE tracking_number = ?", (trk,))
                ship = cursor.fetchone()
                if not ship:
                    raise ValueError(f"Shipment '{trk}' not found.")
                if ship["status"] in ["Delivered", "Cancelled"]:
                    raise ValueError(f"Cannot assign courier to shipment with status '{ship['status']}'.")

                cursor.execute("SELECT id, name, is_active FROM couriers WHERE courier_code = ?", (courier_code.strip().upper(),))
                cour = cursor.fetchone()
                if not cour:
                    raise ValueError(f"Courier '{courier_code}' not found.")
                if not cour["is_active"]:
                    raise ValueError(f"Courier '{courier_code}' is inactive.")

                cursor.execute("UPDATE shipments SET courier_id = ?, status = 'Assigned' WHERE id = ?", (cour["id"], ship["id"]))

                cursor.execute(
                    """
                    INSERT INTO tracking_milestones (shipment_id, location, status_update, remarks)
                    VALUES (?, 'Dispatch Center', 'Assigned', ?)
                    """,
                    (ship["id"], f"Assigned to courier: {cour['name']} ({courier_code.upper()})")
                )
        finally:
            conn.close()

        return self.get_shipment_details(trk)

    def update_shipment_status(self, tracking_number: str, new_status: str,
                               current_location: str, remarks: str = "") -> Dict[str, Any]:
        trk = tracking_number.strip().upper()
        loc = current_location.strip()
        if not loc:
            raise ValueError("Current location is required for status tracking update.")

        status_map = {
            "created": "Created",
            "assigned": "Assigned",
            "in transit": "In Transit",
            "out for delivery": "Out for Delivery",
            "delivered": "Delivered",
            "cancelled": "Cancelled"
        }
        status_clean = status_map.get(new_status.strip().lower())
        if not status_clean:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: Created, Assigned, In Transit, Out for Delivery, Delivered, Cancelled")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status, courier_id FROM shipments WHERE tracking_number = ?", (trk,))
                ship = cursor.fetchone()
                if not ship:
                    raise ValueError(f"Shipment '{trk}' not found.")

                if status_clean in ["Out for Delivery", "Delivered"] and not ship["courier_id"]:
                    raise ValueError(f"Cannot mark shipment as '{status_clean}' without assigning a courier.")

                delivered_clause = ", delivered_at = CURRENT_TIMESTAMP" if status_clean == "Delivered" else ""
                cursor.execute(
                    f"UPDATE shipments SET status = ?{delivered_clause} WHERE id = ?",
                    (status_clean, ship["id"])
                )

                cursor.execute(
                    """
                    INSERT INTO tracking_milestones (shipment_id, location, status_update, remarks)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ship["id"], loc, status_clean, remarks.strip() or f"Status updated to {status_clean}")
                )
        finally:
            conn.close()

        return self.get_shipment_details(trk)

    def record_payment(self, tracking_number: str) -> Dict[str, Any]:
        trk = tracking_number.strip().upper()
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status FROM shipments WHERE tracking_number = ?", (trk,))
                ship = cursor.fetchone()
                if not ship:
                    raise ValueError(f"Shipment '{trk}' not found.")
                if ship["payment_status"] == "Paid":
                    raise ValueError(f"Shipment '{trk}' is already marked as Paid.")

                cursor.execute("UPDATE shipments SET payment_status = 'Paid' WHERE id = ?", (ship["id"],))
        finally:
            conn.close()

        return self.get_shipment_details(trk)

    def get_shipment_details(self, tracking_number: str) -> Dict[str, Any]:
        trk = tracking_number.strip().upper()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.*, c.customer_code as sender_code, c.name as sender_name, c.phone as sender_phone, c.address as sender_address,
                       cr.courier_code, cr.name as courier_name, cr.phone as courier_phone, cr.vehicle_type
                FROM shipments s
                JOIN customers c ON s.sender_id = c.id
                LEFT JOIN couriers cr ON s.courier_id = cr.id
                WHERE s.tracking_number = ?
                """,
                (trk,)
            )
            ship = cursor.fetchone()
            if not ship:
                raise ValueError(f"Shipment '{tracking_number}' not found.")

            cursor.execute(
                """
                SELECT location, status_update, remarks, timestamp
                FROM tracking_milestones
                WHERE shipment_id = ?
                ORDER BY id ASC
                """,
                (ship["id"],)
            )
            milestones = [dict(r) for r in cursor.fetchall()]

            res = dict(ship)
            res["milestones"] = milestones
            return res
        finally:
            conn.close()

    def list_shipments(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT s.*, c.name as sender_name, cr.name as courier_name
                FROM shipments s
                JOIN customers c ON s.sender_id = c.id
                LEFT JOIN couriers cr ON s.courier_id = cr.id
            """
            params = []
            if status_filter:
                query += " WHERE s.status = ?"
                params.append(status_filter)
            query += " ORDER BY s.id DESC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def list_couriers(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM couriers ORDER BY courier_code ASC")
            return [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

    def generate_logistics_report(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM shipments")
            total_shipments = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM shipments
                GROUP BY status
                """
            )
            status_breakdown = {r["status"]: r["count"] for r in cursor.fetchall()}

            cursor.execute(
                """
                SELECT COALESCE(SUM(weight_kg), 0) as total_weight,
                       COALESCE(SUM(delivery_fee), 0) as total_freight,
                       COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN delivery_fee ELSE 0 END), 0) as total_collected
                FROM shipments
                """
            )
            totals = cursor.fetchone()

            cursor.execute(
                """
                SELECT cr.name as courier_name, cr.vehicle_type, COUNT(s.id) as parcels_assigned,
                       SUM(CASE WHEN s.status = 'Delivered' THEN 1 ELSE 0 END) as parcels_delivered
                FROM couriers cr
                LEFT JOIN shipments s ON cr.id = s.courier_id
                GROUP BY cr.id
                ORDER BY parcels_delivered DESC
                """
            )
            courier_perf = [dict(r) for r in cursor.fetchall()]

            return {
                "total_shipments": total_shipments,
                "status_breakdown": status_breakdown,
                "total_weight_handled_kg": round(float(totals["total_weight"]), 2),
                "total_freight_invoiced": round(float(totals["total_freight"]), 2),
                "total_freight_collected": round(float(totals["total_collected"]), 2),
                "courier_performance": courier_perf
            }
        finally:
            conn.close()
