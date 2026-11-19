"""
Database Layer for Queue Management System
Manages SQLite schema creation, database connections, and default seeds.
"""

import sqlite3

DEFAULT_DB_FILE = "queue_system.db"

INITIAL_CATEGORIES = [
    ("TX", "Teller / Cash Transactions", "Deposits, withdrawals, and utility bill payments"),
    ("CS", "Customer Service", "Account inquiries, dispute resolution, and card replacements"),
    ("LN", "Loans & Credit Facilities", "Mortgage, personal loan, and business credit consultations"),
    ("AC", "Account Opening & KYC", "New account registration, KYC verification, and biometric updates")
]

INITIAL_COUNTERS = [
    (1, "Officer Alice Johnson (Counter 1 - General Teller)"),
    (2, "Officer Bob Smith (Counter 2 - Customer Service)"),
    (3, "Officer Carol Danvers (Counter 3 - Credit & Loans)")
]


def get_db_connection(db_path=DEFAULT_DB_FILE):
    """
    Creates and returns a SQLite connection configured with Row factory.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path=DEFAULT_DB_FILE):
    """
    Creates required database tables, indexes, and initial seeds if empty.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Service Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        );
        """)

        # 2. Service Counters / Desks Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_counters (
            counter_id INTEGER PRIMARY KEY,
            officer_name TEXT NOT NULL,
            current_ticket_id INTEGER
        );
        """)

        # 3. Queue Tickets Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue_tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            category_code TEXT NOT NULL,
            counter_id INTEGER,
            status TEXT NOT NULL CHECK(status IN ('waiting', 'serving', 'completed', 'cancelled')) DEFAULT 'waiting',
            created_at TEXT NOT NULL,
            called_at TEXT,
            completed_at TEXT,
            wait_time_seconds INTEGER,
            service_time_seconds INTEGER,
            notes TEXT
        );
        """)

        # Indexes for queue queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_status ON queue_tickets(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_category ON queue_tickets(category_code);")

        conn.commit()

        # Seed categories if empty
        cursor.execute("SELECT COUNT(*) FROM service_categories;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO service_categories (code, name, description)
            VALUES (?, ?, ?);
            """, INITIAL_CATEGORIES)
            conn.commit()

        # Seed counters if empty
        cursor.execute("SELECT COUNT(*) FROM service_counters;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO service_counters (counter_id, officer_name)
            VALUES (?, ?);
            """, INITIAL_COUNTERS)
            conn.commit()
