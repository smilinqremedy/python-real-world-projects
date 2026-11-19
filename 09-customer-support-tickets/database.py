"""
Database Layer for Customer Complaint and Support Ticket Management System
Manages SQLite schema creation, foreign key constraints, and initial agent seeds.
"""

import sqlite3
from datetime import datetime

DEFAULT_DB_FILE = "support_tickets.db"

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

TICKET_STATUSES = ["Open", "In Progress", "Resolved", "Reopened"]

CATEGORIES = [
    "Billing & Payments",
    "Technical Support",
    "Product Quality & Defects",
    "Delivery & Shipping",
    "Account Access & Security",
    "General Inquiry"
]

INITIAL_AGENTS = [
    ("Alex Rivera", "a.rivera@support.com", "Tier 1 Support"),
    ("Samantha Hayes", "s.hayes@support.com", "Technical Operations"),
    ("Marcus Chen", "m.chen@support.com", "Billing & Finance"),
    ("Fatima Al-Mansoor", "f.almansoor@support.com", "Quality Assurance")
]


def get_db_connection(db_path=DEFAULT_DB_FILE):
    """
    Creates and returns a SQLite connection with foreign keys and Row factory enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path=DEFAULT_DB_FILE):
    """
    Creates relational database tables, indexes, and initial seeds if empty.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Customers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            company_name TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # 2. Support Agents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_agents (
            agent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 3. Support Tickets Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_code TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            agent_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
            status TEXT NOT NULL CHECK(status IN ('Open', 'In Progress', 'Resolved', 'Reopened')) DEFAULT 'Open',
            resolution_notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT,
            FOREIGN KEY (agent_id) REFERENCES support_agents(agent_id) ON DELETE SET NULL
        );
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_code ON tickets(ticket_code);")

        conn.commit()

        # Seed agents if empty
        cursor.execute("SELECT COUNT(*) FROM support_agents;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO support_agents (full_name, email, department)
            VALUES (?, ?, ?);
            """, INITIAL_AGENTS)
            conn.commit()
