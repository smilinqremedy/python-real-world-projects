"""
Service Layer for Customer Complaint and Support Ticket Management System
Encapsulates business rules, state machine transitions, priority ordering, and analytics.
"""

from datetime import datetime
import sqlite3
from database import (
    get_db_connection,
    PRIORITY_LEVELS,
    TICKET_STATUSES,
    CATEGORIES,
    DEFAULT_DB_FILE
)


class TicketService:
    def __init__(self, db_path=DEFAULT_DB_FILE):
        self.db_path = db_path

    # ==========================================
    # 1. CUSTOMER REGISTRATION
    # ==========================================

    def register_customer(self, full_name, email, phone=None, company_name=None):
        """
        Registers a new customer. Enforces email uniqueness.
        """
        name = full_name.strip()
        mail = email.strip().lower()

        if not name:
            raise ValueError("Customer full name cannot be blank.")
        if not mail or "@" not in mail:
            raise ValueError("Valid customer email address is required.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO customers (full_name, email, phone, company_name, created_at)
                VALUES (?, ?, ?, ?, ?);
                """, (name, mail, phone.strip() if phone else None, company_name.strip() if company_name else None, now_str))
                conn.commit()
                cust_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError(f"Customer with email '{mail}' is already registered.")

        return self.get_customer_by_id(cust_id)

    def get_customer_by_id(self, customer_id):
        """Retrieves customer by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?;", (customer_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Customer ID {customer_id} not found.")
            return dict(row)

    def list_customers(self):
        """Lists all registered customers."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers ORDER BY customer_id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 2. AGENTS
    # ==========================================

    def list_agents(self):
        """Returns all active support agents."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM support_agents WHERE is_active = 1 ORDER BY agent_id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_agent_by_id(self, agent_id):
        """Retrieves agent by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM support_agents WHERE agent_id = ?;", (agent_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Support Agent ID {agent_id} not found.")
            return dict(row)

    # ==========================================
    # 3. TICKET CREATION & ID GENERATION
    # ==========================================

    def generate_unique_ticket_code(self):
        """
        Generates a unique ticket identifier formatted as TICK-YYYY-NNN.
        """
        year = datetime.now().year
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_code FROM tickets WHERE ticket_code LIKE ?;", (f"TICK-{year}-%",))
            rows = cursor.fetchall()
            existing_nums = []
            for row in rows:
                try:
                    num_part = int(row["ticket_code"].split("-")[-1])
                    existing_nums.append(num_part)
                except ValueError:
                    pass
            next_num = max(existing_nums, default=0) + 1
            return f"TICK-{year}-{next_num:03d}"

    def create_ticket(self, customer_id, title, description, category, priority="Medium", agent_id=None):
        """
        Creates a new customer support complaint ticket.
        """
        # Validate customer
        customer = self.get_customer_by_id(customer_id)

        title_clean = title.strip()
        desc_clean = description.strip()
        cat_clean = category.strip()
        prio_clean = priority.strip().capitalize()

        if not title_clean:
            raise ValueError("Ticket title/summary cannot be blank.")
        if not desc_clean:
            raise ValueError("Complaint description cannot be blank.")
        if cat_clean not in CATEGORIES:
            raise ValueError(f"Invalid category '{category}'. Allowed: {', '.join(CATEGORIES)}")
        if prio_clean not in PRIORITY_LEVELS:
            raise ValueError(f"Invalid priority '{priority}'. Allowed: {', '.join(PRIORITY_LEVELS)}")

        if agent_id is not None:
            self.get_agent_by_id(agent_id)

        ticket_code = self.generate_unique_ticket_code()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO tickets (ticket_code, customer_id, agent_id, title, description, category, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Open', ?, ?);
            """, (ticket_code, customer["customer_id"], agent_id, title_clean, desc_clean, cat_clean, prio_clean, now_str, now_str))
            conn.commit()
            t_id = cursor.lastrowid

        return self.get_ticket_by_id(t_id)

    # ==========================================
    # 4. ASSIGNMENT & STATUS TRANSITIONS
    # ==========================================

    def assign_ticket(self, ticket_id_or_code, agent_id):
        """
        Assigns a support ticket to an agent.
        """
        ticket = self.find_ticket(ticket_id_or_code)
        agent = self.get_agent_by_id(agent_id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE tickets
            SET agent_id = ?, updated_at = ?
            WHERE ticket_id = ?;
            """, (agent["agent_id"], now_str, ticket["ticket_id"]))
            conn.commit()

        return self.get_ticket_by_id(ticket["ticket_id"])

    def update_ticket_status(self, ticket_id_or_code, new_status, resolution_notes=None):
        """
        Updates the status of a ticket.
        CRITICAL BUSINESS RULE:
        Prevents unassigned tickets from moving into 'In Progress'.
        """
        ticket = self.find_ticket(ticket_id_or_code)
        status_clean = new_status.strip()

        # Normalize casing
        normalized_status = None
        for s in TICKET_STATUSES:
            if s.lower() == status_clean.lower():
                normalized_status = s
                break

        if not normalized_status:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(TICKET_STATUSES)}")

        # Business Rule 9: Prevent unassigned tickets from moving into progress
        if normalized_status == "In Progress" and ticket.get("agent_id") is None:
            raise ValueError(
                "Business Rule Violation: Unassigned tickets cannot be moved to 'In Progress'. "
                "Please assign a support agent to the ticket first."
            )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resolved_str = now_str if normalized_status == "Resolved" else ticket.get("resolved_at")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE tickets
            SET status = ?, resolution_notes = COALESCE(?, resolution_notes),
                resolved_at = ?, updated_at = ?
            WHERE ticket_id = ?;
            """, (normalized_status, resolution_notes.strip() if resolution_notes else None, resolved_str, now_str, ticket["ticket_id"]))
            conn.commit()

        return self.get_ticket_by_id(ticket["ticket_id"])

    # ==========================================
    # 5. SEARCH & QUERIES
    # ==========================================

    def find_ticket(self, id_or_code):
        """
        Searches a ticket by numeric ticket_id or ticket_code (e.g. TICK-2026-001).
        """
        query_str = str(id_or_code).strip()
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if query_str.isdigit():
                cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?;", (int(query_str),))
            else:
                cursor.execute("SELECT * FROM tickets WHERE ticket_code = ? COLLATE NOCASE;", (query_str,))
            row = cursor.fetchone()

        if not row:
            raise ValueError(f"Ticket '{id_or_code}' not found.")
        return self.get_ticket_by_id(row["ticket_id"])

    def get_ticket_by_id(self, ticket_id):
        """Fetches full ticket details joined with customer and agent information."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                t.*,
                c.full_name AS customer_name,
                c.email AS customer_email,
                c.phone AS customer_phone,
                c.company_name AS customer_company,
                a.full_name AS agent_name,
                a.email AS agent_email,
                a.department AS agent_department
            FROM tickets t
            JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN support_agents a ON t.agent_id = a.agent_id
            WHERE t.ticket_id = ?;
            """, (ticket_id,))
            row = cursor.fetchone()

        if not row:
            raise ValueError(f"Ticket ID {ticket_id} not found.")
        return dict(row)

    def get_unresolved_tickets_by_priority(self):
        """
        Feature 10: Displays unresolved tickets ('Open', 'In Progress', 'Reopened')
        ordered by priority: Critical -> High -> Medium -> Low, then created_at ASC.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                t.*,
                c.full_name AS customer_name,
                a.full_name AS agent_name
            FROM tickets t
            JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN support_agents a ON t.agent_id = a.agent_id
            WHERE t.status IN ('Open', 'In Progress', 'Reopened')
            ORDER BY 
                CASE t.priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High'     THEN 2
                    WHEN 'Medium'   THEN 3
                    WHEN 'Low'      THEN 4
                    ELSE 5
                END ASC,
                t.created_at ASC;
            """)
            return [dict(r) for r in cursor.fetchall()]

    def list_all_tickets(self, limit=50):
        """Returns all tickets sorted by updated_at descending."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                t.*,
                c.full_name AS customer_name,
                a.full_name AS agent_name
            FROM tickets t
            JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN support_agents a ON t.agent_id = a.agent_id
            ORDER BY t.ticket_id DESC LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 6. REPORTS & ANALYTICS
    # ==========================================

    def generate_ticket_reports(self):
        """
        Feature 12: Generates comprehensive reporting showing:
        - Total tickets
        - Status breakdown
        - Priority breakdown
        - Category breakdown
        - Resolution rate
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) AS total FROM tickets;")
            total_tickets = cursor.fetchone()["total"]

            # Status breakdown
            cursor.execute("SELECT status, COUNT(*) AS count FROM tickets GROUP BY status;")
            status_rows = cursor.fetchall()
            status_counts = {s: 0 for s in TICKET_STATUSES}
            for r in status_rows:
                status_counts[r["status"]] = r["count"]

            # Priority breakdown
            cursor.execute("SELECT priority, COUNT(*) AS count FROM tickets GROUP BY priority;")
            priority_rows = cursor.fetchall()
            priority_counts = {p: 0 for p in PRIORITY_LEVELS}
            for r in priority_rows:
                priority_counts[r["priority"]] = r["count"]

            # Category breakdown
            cursor.execute("SELECT category, COUNT(*) AS count FROM tickets GROUP BY category;")
            category_counts = {r["category"]: r["count"] for r in cursor.fetchall()}

        resolved_count = status_counts.get("Resolved", 0)
        resolution_rate = round((resolved_count / total_tickets * 100), 1) if total_tickets > 0 else 0.0
        unresolved_count = total_tickets - resolved_count

        return {
            "total_tickets": total_tickets,
            "resolved_count": resolved_count,
            "unresolved_count": unresolved_count,
            "resolution_rate_pct": resolution_rate,
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "category_breakdown": category_counts
        }
