"""
Queue Management System - Core Business Logic
Implements FIFO queue mechanics with collections.deque and SQLite persistent storage.
Tracks customer lifecycle: Waiting -> Serving -> Completed / Cancelled.
"""

from collections import deque
from datetime import datetime
import sqlite3
from database import get_db_connection, DEFAULT_DB_FILE


class QueueManager:
    def __init__(self, db_path=DEFAULT_DB_FILE):
        self.db_path = db_path
        # In-memory FIFO queues organized by category code and unified queue
        self._waiting_queues = {}  # {category_code: deque([ticket_id, ...])}
        self._unified_queue = deque()  # deque([ticket_id, ...])
        self._sync_in_memory_queues()

    def _sync_in_memory_queues(self):
        """
        Synchronizes in-memory FIFO deques from database for any waiting tickets.
        """
        self._waiting_queues.clear()
        self._unified_queue.clear()

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT code FROM service_categories;")
            for row in cursor.fetchall():
                self._waiting_queues[row["code"]] = deque()

            cursor.execute("""
            SELECT ticket_id, category_code FROM queue_tickets
            WHERE status = 'waiting'
            ORDER BY ticket_id ASC;
            """)
            for row in cursor.fetchall():
                t_id = row["ticket_id"]
                cat = row["category_code"]
                if cat not in self._waiting_queues:
                    self._waiting_queues[cat] = deque()
                self._waiting_queues[cat].append(t_id)
                self._unified_queue.append(t_id)

    # ==========================================
    # 1. CATEGORY & COUNTER MANAGEMENT
    # ==========================================

    def list_categories(self):
        """Returns all available service categories."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM service_categories ORDER BY category_id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    def list_counters(self):
        """Returns all service counters and their active status."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.counter_id, c.officer_name, c.current_ticket_id,
                   t.ticket_number, t.customer_name, t.category_code
            FROM service_counters c
            LEFT JOIN queue_tickets t ON c.current_ticket_id = t.ticket_id
            ORDER BY c.counter_id ASC;
            """)
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 2. TICKET GENERATION & CUSTOMER REGISTRATION
    # ==========================================

    def generate_next_ticket_number(self, category_code):
        """
        Generates unique formatted queue number like TX-101, CS-102.
        """
        code = category_code.strip().upper()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT ticket_number FROM queue_tickets
            WHERE category_code = ?
            ORDER BY ticket_id DESC LIMIT 1;
            """, (code,))
            row = cursor.fetchone()

            if row and "-" in row["ticket_number"]:
                try:
                    seq = int(row["ticket_number"].split("-")[-1])
                    next_seq = seq + 1
                except ValueError:
                    next_seq = 101
            else:
                next_seq = 101

        return f"{code}-{next_seq:03d}"

    def register_and_enqueue_customer(self, customer_name, category_code, customer_phone=None, notes=None):
        """
        Registers a customer, assigns a unique queue number, and adds them to the FIFO waiting queue.
        """
        name = customer_name.strip()
        code = category_code.strip().upper()

        if not name:
            raise ValueError("Customer name cannot be empty.")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM service_categories WHERE code = ?;", (code,))
            cat_row = cursor.fetchone()
            if not cat_row:
                raise ValueError(f"Invalid service category code '{category_code}'.")

            ticket_number = self.generate_next_ticket_number(code)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO queue_tickets (ticket_number, customer_name, customer_phone, category_code, status, created_at, notes)
            VALUES (?, ?, ?, ?, 'waiting', ?, ?);
            """, (ticket_number, name, customer_phone.strip() if customer_phone else None, code, now_str, notes.strip() if notes else None))
            conn.commit()
            ticket_id = cursor.lastrowid

        # Enqueue in memory FIFO
        if code not in self._waiting_queues:
            self._waiting_queues[code] = deque()
        self._waiting_queues[code].append(ticket_id)
        self._unified_queue.append(ticket_id)

        # Compute position in queue
        queue_pos = len(self._waiting_queues[code])

        return {
            "ticket_id": ticket_id,
            "ticket_number": ticket_number,
            "customer_name": name,
            "category_code": code,
            "category_name": cat_row["name"],
            "queue_position": queue_pos,
            "created_at": now_str
        }

    # ==========================================
    # 3. CALLING & SERVING CUSTOMERS
    # ==========================================

    def call_next_customer(self, counter_id, category_code=None):
        """
        Calls the next available customer from the FIFO waiting queue.
        Assigns the customer to the calling counter and logs service start time.
        """
        # Verify counter exists
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM service_counters WHERE counter_id = ?;", (counter_id,))
            counter = cursor.fetchone()
            if not counter:
                raise ValueError(f"Counter #{counter_id} does not exist.")

            # If counter is currently busy, complete previous ticket first
            if counter["current_ticket_id"]:
                raise ValueError(f"Counter #{counter_id} is currently busy serving ticket #{counter['current_ticket_id']}. Please complete it first.")

        # Find next ticket from deque (FIFO)
        selected_ticket_id = None
        if category_code:
            code = category_code.strip().upper()
            if code in self._waiting_queues and len(self._waiting_queues[code]) > 0:
                selected_ticket_id = self._waiting_queues[code].popleft()
                if selected_ticket_id in self._unified_queue:
                    self._unified_queue.remove(selected_ticket_id)
        else:
            if len(self._unified_queue) > 0:
                selected_ticket_id = self._unified_queue.popleft()
                # Also remove from category specific deque
                for cat_deque in self._waiting_queues.values():
                    if selected_ticket_id in cat_deque:
                        cat_deque.remove(selected_ticket_id)
                        break

        if not selected_ticket_id:
            raise ValueError("No customers currently waiting in queue.")

        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM queue_tickets WHERE ticket_id = ?;", (selected_ticket_id,))
            ticket = cursor.fetchone()

            created_dt = datetime.strptime(ticket["created_at"], "%Y-%m-%d %H:%M:%S")
            wait_seconds = max(0, int((now_dt - created_dt).total_seconds()))

            # Update ticket status to 'serving'
            cursor.execute("""
            UPDATE queue_tickets
            SET status = 'serving', counter_id = ?, called_at = ?, wait_time_seconds = ?
            WHERE ticket_id = ?;
            """, (counter_id, now_str, wait_seconds, selected_ticket_id))

            # Assign ticket to counter
            cursor.execute("""
            UPDATE service_counters
            SET current_ticket_id = ?
            WHERE counter_id = ?;
            """, (selected_ticket_id, counter_id))

            conn.commit()

        return self.get_ticket_by_id(selected_ticket_id)

    def mark_as_served(self, counter_id=None, ticket_number_or_id=None):
        """
        Marks an ongoing service as completed.
        Computes service duration and clears counter.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            ticket = None
            if ticket_number_or_id:
                if str(ticket_number_or_id).isdigit():
                    cursor.execute("SELECT * FROM queue_tickets WHERE ticket_id = ?;", (int(ticket_number_or_id),))
                else:
                    cursor.execute("SELECT * FROM queue_tickets WHERE ticket_number = ?;", (str(ticket_number_or_id).strip().upper(),))
                ticket = cursor.fetchone()
            elif counter_id:
                cursor.execute("""
                SELECT t.* FROM queue_tickets t
                JOIN service_counters c ON c.current_ticket_id = t.ticket_id
                WHERE c.counter_id = ?;
                """, (counter_id,))
                ticket = cursor.fetchone()

            if not ticket:
                raise ValueError("Active serving ticket not found.")

            if ticket["status"] != "serving":
                raise ValueError(f"Ticket {ticket['ticket_number']} is not in 'serving' status (current: {ticket['status']}).")

            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            called_dt = datetime.strptime(ticket["called_at"], "%Y-%m-%d %H:%M:%S") if ticket["called_at"] else now_dt
            service_seconds = max(0, int((now_dt - called_dt).total_seconds()))

            # Update ticket
            cursor.execute("""
            UPDATE queue_tickets
            SET status = 'completed', completed_at = ?, service_time_seconds = ?
            WHERE ticket_id = ?;
            """, (now_str, service_seconds, ticket["ticket_id"]))

            # Clear counter
            cursor.execute("""
            UPDATE service_counters
            SET current_ticket_id = NULL
            WHERE current_ticket_id = ?;
            """, (ticket["ticket_id"],))

            conn.commit()

        return self.get_ticket_by_id(ticket["ticket_id"])

    # ==========================================
    # 4. TICKET CANCELLATION
    # ==========================================

    def cancel_ticket(self, ticket_number_or_id, reason="Customer cancelled or left"):
        """
        Cancels a queue ticket. If waiting in line, removes from FIFO deque.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if str(ticket_number_or_id).isdigit():
                cursor.execute("SELECT * FROM queue_tickets WHERE ticket_id = ?;", (int(ticket_number_or_id),))
            else:
                cursor.execute("SELECT * FROM queue_tickets WHERE ticket_number = ?;", (str(ticket_number_or_id).strip().upper(),))
            ticket = cursor.fetchone()

            if not ticket:
                raise ValueError(f"Ticket '{ticket_number_or_id}' not found.")

            if ticket["status"] in ("completed", "cancelled"):
                raise ValueError(f"Cannot cancel ticket in '{ticket['status']}' state.")

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            UPDATE queue_tickets
            SET status = 'cancelled', completed_at = ?, notes = COALESCE(notes || ' | ' || ?, ?)
            WHERE ticket_id = ?;
            """, (now_str, f"Cancelled: {reason}", f"Cancelled: {reason}", ticket["ticket_id"]))

            # Clear from counter if it was serving
            cursor.execute("UPDATE service_counters SET current_ticket_id = NULL WHERE current_ticket_id = ?;", (ticket["ticket_id"],))
            conn.commit()

        # Remove from in-memory deques if present
        t_id = ticket["ticket_id"]
        if t_id in self._unified_queue:
            self._unified_queue.remove(t_id)
        for cat_deque in self._waiting_queues.values():
            if t_id in cat_deque:
                cat_deque.remove(t_id)

        return self.get_ticket_by_id(t_id)

    # ==========================================
    # 5. QUEUE MONITORS & ANALYTICS
    # ==========================================

    def get_ticket_by_id(self, ticket_id):
        """Fetches full ticket details."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, c.name AS category_name, sc.officer_name
            FROM queue_tickets t
            LEFT JOIN service_categories c ON t.category_code = c.code
            LEFT JOIN service_counters sc ON t.counter_id = sc.counter_id
            WHERE t.ticket_id = ?;
            """, (ticket_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Ticket ID {ticket_id} not found.")
            return dict(row)

    def get_waiting_customers(self, category_code=None):
        """
        Returns list of customers currently waiting in FIFO order.
        Includes wait duration so far.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if category_code:
                cursor.execute("""
                SELECT t.*, c.name AS category_name
                FROM queue_tickets t
                JOIN service_categories c ON t.category_code = c.code
                WHERE t.status = 'waiting' AND t.category_code = ?
                ORDER BY t.ticket_id ASC;
                """, (category_code.strip().upper(),))
            else:
                cursor.execute("""
                SELECT t.*, c.name AS category_name
                FROM queue_tickets t
                JOIN service_categories c ON t.category_code = c.code
                WHERE t.status = 'waiting'
                ORDER BY t.ticket_id ASC;
                """)
            rows = [dict(r) for r in cursor.fetchall()]

        now_dt = datetime.now()
        for r in rows:
            created_dt = datetime.strptime(r["created_at"], "%Y-%m-%d %H:%M:%S")
            r["elapsed_wait_seconds"] = max(0, int((now_dt - created_dt).total_seconds()))

        return rows

    def get_currently_serving(self):
        """
        Returns all tickets currently being served at counters.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, c.name AS category_name, sc.counter_id, sc.officer_name
            FROM queue_tickets t
            JOIN service_categories c ON t.category_code = c.code
            JOIN service_counters sc ON t.counter_id = sc.counter_id
            WHERE t.status = 'serving'
            ORDER BY t.called_at ASC;
            """)
            rows = [dict(r) for r in cursor.fetchall()]

        now_dt = datetime.now()
        for r in rows:
            if r["called_at"]:
                called_dt = datetime.strptime(r["called_at"], "%Y-%m-%d %H:%M:%S")
                r["elapsed_service_seconds"] = max(0, int((now_dt - called_dt).total_seconds()))
            else:
                r["elapsed_service_seconds"] = 0

        return rows

    def get_completed_services(self, limit=30):
        """
        Returns completed tickets with recorded wait and service times.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT t.*, c.name AS category_name, sc.officer_name
            FROM queue_tickets t
            JOIN service_categories c ON t.category_code = c.code
            LEFT JOIN service_counters sc ON t.counter_id = sc.counter_id
            WHERE t.status = 'completed'
            ORDER BY t.completed_at DESC LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def calculate_average_waiting_time(self, category_code=None):
        """
        Calculates average waiting time and average service duration for completed tickets.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if category_code:
                cursor.execute("""
                SELECT 
                    COUNT(*) AS served_count,
                    COALESCE(AVG(wait_time_seconds), 0.0) AS avg_wait_sec,
                    COALESCE(AVG(service_time_seconds), 0.0) AS avg_service_sec
                FROM queue_tickets
                WHERE status = 'completed' AND category_code = ?;
                """, (category_code.strip().upper(),))
            else:
                cursor.execute("""
                SELECT 
                    COUNT(*) AS served_count,
                    COALESCE(AVG(wait_time_seconds), 0.0) AS avg_wait_sec,
                    COALESCE(AVG(service_time_seconds), 0.0) AS avg_service_sec
                FROM queue_tickets
                WHERE status = 'completed';
                """)
            row = cursor.fetchone()

        served_count = row["served_count"]
        avg_wait = round(row["avg_wait_sec"], 1)
        avg_service = round(row["avg_service_sec"], 1)

        return {
            "category": category_code or "All Categories",
            "served_count": served_count,
            "avg_wait_seconds": avg_wait,
            "avg_wait_minutes": round(avg_wait / 60, 1),
            "avg_service_seconds": avg_service,
            "avg_service_minutes": round(avg_service / 60, 1)
        }
