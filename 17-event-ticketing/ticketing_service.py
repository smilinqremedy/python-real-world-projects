"""
Business logic and ticketing operations for Event Registration and Ticketing System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class TicketingService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def create_event(self, code: str, title: str, event_date: str,
                     location: str, ticket_price: float, max_capacity: int) -> Dict[str, Any]:
        code = code.strip().upper()
        title = title.strip()
        location = location.strip()

        if not code or not title or not location:
            raise ValueError("Event code, title, and location cannot be empty.")
        if ticket_price < 0:
            raise ValueError("Ticket price cannot be negative.")
        if max_capacity <= 0:
            raise ValueError("Maximum capacity must be greater than zero.")

        try:
            parsed_date = datetime.strptime(event_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Event date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO events (event_code, title, event_date, location, ticket_price, max_capacity)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (code, title, str(parsed_date), location, round(ticket_price, 2), max_capacity)
                )
                return {
                    "id": cursor.lastrowid,
                    "event_code": code,
                    "title": title,
                    "event_date": str(parsed_date),
                    "location": location,
                    "ticket_price": round(ticket_price, 2),
                    "max_capacity": max_capacity
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Event with code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def register_attendee(self, event_code: str, name: str, email: str, phone: str,
                          is_paid: bool = False, reg_date_str: Optional[str] = None) -> Dict[str, Any]:
        code = event_code.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not code or not name or not email or not phone:
            raise ValueError("Event code, attendee name, email, and phone cannot be empty.")

        r_date = reg_date_str.strip() if reg_date_str else str(date.today())
        try:
            datetime.strptime(r_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Registration date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, ticket_price, max_capacity FROM events WHERE event_code = ?", (code,))
                event = cursor.fetchone()
                if not event:
                    raise ValueError(f"Event '{code}' not found.")

                # Capacity Check
                cursor.execute("SELECT COUNT(*) FROM tickets WHERE event_id = ?", (event["id"],))
                current_count = cursor.fetchone()[0]
                if current_count >= event["max_capacity"]:
                    raise ValueError(f"Event '{event['title']}' has reached maximum attendee capacity ({event['max_capacity']}). Booking rejected.")

                # Retrieve or insert attendee
                cursor.execute("SELECT id FROM attendees WHERE email = ?", (email,))
                att_row = cursor.fetchone()
                if att_row:
                    attendee_id = att_row["id"]
                else:
                    cursor.execute("INSERT INTO attendees (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
                    attendee_id = cursor.lastrowid

                # Duplicate registration prevention for same event
                cursor.execute("SELECT id FROM tickets WHERE event_id = ? AND attendee_id = ?", (event["id"], attendee_id))
                if cursor.fetchone():
                    raise ValueError(f"Attendee with email '{email}' is already registered for this event.")

                # Create ticket
                ticket_code = f"TCK-{uuid.uuid4().hex[:6].upper()}"
                payment_status = "Paid" if (is_paid or event["ticket_price"] == 0) else "Unpaid"
                cursor.execute(
                    """
                    INSERT INTO tickets (ticket_id, event_id, attendee_id, purchase_date, price_paid, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (ticket_code, event["id"], attendee_id, r_date, event["ticket_price"], payment_status)
                )
        finally:
            conn.close()

        return self.get_ticket_details(ticket_code)

    def record_payment(self, ticket_id: str) -> Dict[str, Any]:
        t_id = ticket_id.strip().upper()
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status FROM tickets WHERE ticket_id = ?", (t_id,))
                ticket = cursor.fetchone()
                if not ticket:
                    raise ValueError(f"Ticket '{t_id}' not found.")
                if ticket["payment_status"] == "Paid":
                    raise ValueError(f"Ticket '{t_id}' is already paid.")

                cursor.execute("UPDATE tickets SET payment_status = 'Paid' WHERE id = ?", (ticket["id"],))
        finally:
            conn.close()

        return self.get_ticket_details(t_id)

    def check_in_attendee(self, ticket_id: str) -> Dict[str, Any]:
        t_id = ticket_id.strip().upper()
        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, payment_status, is_checked_in, check_in_time FROM tickets WHERE ticket_id = ?", (t_id,))
                ticket = cursor.fetchone()
                if not ticket:
                    raise ValueError(f"Ticket '{t_id}' not found.")
                if ticket["payment_status"] != "Paid":
                    raise ValueError(f"Ticket '{t_id}' has not been paid yet. Payment confirmation required before check-in.")
                if ticket["is_checked_in"]:
                    raise ValueError(f"Ticket '{t_id}' is already checked in (Checked in at: {ticket['check_in_time']}).")

                cursor.execute("UPDATE tickets SET is_checked_in = 1, check_in_time = CURRENT_TIMESTAMP WHERE id = ?", (ticket["id"],))
        finally:
            conn.close()

        return self.get_ticket_details(t_id)

    def get_ticket_details(self, ticket_id: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.*, e.event_code, e.title as event_title, e.event_date, e.location,
                       a.name as attendee_name, a.email as attendee_email, a.phone as attendee_phone
                FROM tickets t
                JOIN events e ON t.event_id = e.id
                JOIN attendees a ON t.attendee_id = a.id
                WHERE t.ticket_id = ?
                """,
                (ticket_id.strip().upper(),)
            )
            ticket = cursor.fetchone()
            if not ticket:
                raise ValueError(f"Ticket '{ticket_id}' not found.")
            return dict(ticket)
        finally:
            conn.close()

    def get_event_availability(self, event_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, event_code, title, event_date, location, ticket_price, max_capacity FROM events WHERE event_code = ?", (event_code.strip().upper(),))
            event = cursor.fetchone()
            if not event:
                raise ValueError(f"Event '{event_code}' not found.")

            cursor.execute("SELECT COUNT(*) FROM tickets WHERE event_id = ?", (event["id"],))
            registered_count = cursor.fetchone()[0]
            remaining = max(0, event["max_capacity"] - registered_count)

            res = dict(event)
            res["registered_attendees"] = registered_count
            res["remaining_tickets"] = remaining
            res["is_sold_out"] = (remaining == 0)
            return res
        finally:
            conn.close()

    def list_events(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, COUNT(t.id) as tickets_booked
                FROM events e
                LEFT JOIN tickets t ON e.id = t.event_id
                GROUP BY e.id
                ORDER BY e.event_date ASC
                """
            )
            events = []
            for r in cursor.fetchall():
                d = dict(r)
                d["remaining"] = max(0, d["max_capacity"] - d["tickets_booked"])
                events.append(d)
            return events
        finally:
            conn.close()

    def generate_report(self, event_code: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = "SELECT id, event_code, title, event_date, ticket_price, max_capacity FROM events"
            params = []
            if event_code:
                query += " WHERE event_code = ?"
                params.append(event_code.strip().upper())
            query += " ORDER BY event_date ASC"
            cursor.execute(query, params)
            events = cursor.fetchall()

            reports = []
            for ev in events:
                cursor.execute(
                    """
                    SELECT COUNT(*) as total_tickets,
                           SUM(CASE WHEN payment_status = 'Paid' THEN 1 ELSE 0 END) as paid_tickets,
                           SUM(CASE WHEN is_checked_in = 1 THEN 1 ELSE 0 END) as checked_in_count,
                           SUM(CASE WHEN payment_status = 'Paid' THEN price_paid ELSE 0 END) as total_revenue
                    FROM tickets
                    WHERE event_id = ?
                    """,
                    (ev["id"],)
                )
                stats = cursor.fetchone()
                total_t = stats["total_tickets"] or 0
                paid_t = stats["paid_tickets"] or 0
                checked_in = stats["checked_in_count"] or 0
                rev = float(stats["total_revenue"] or 0.0)

                occupancy_rate = (total_t / ev["max_capacity"] * 100) if ev["max_capacity"] > 0 else 0.0
                turnout_rate = (checked_in / total_t * 100) if total_t > 0 else 0.0

                reports.append({
                    "event_code": ev["event_code"],
                    "title": ev["title"],
                    "event_date": ev["event_date"],
                    "max_capacity": ev["max_capacity"],
                    "tickets_issued": total_t,
                    "remaining_capacity": max(0, ev["max_capacity"] - total_t),
                    "paid_tickets": paid_t,
                    "checked_in_count": checked_in,
                    "total_revenue": round(rev, 2),
                    "occupancy_rate": round(occupancy_rate, 1),
                    "turnout_rate": round(turnout_rate, 1)
                })
            return reports
        finally:
            conn.close()
