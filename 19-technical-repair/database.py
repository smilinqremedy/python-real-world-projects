"""
Database configuration and schema for Technical Repair Service Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "repair_service.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS technicians (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tech_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                specialty TEXT NOT NULL,
                phone TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                technician_id INTEGER REFERENCES technicians(id) ON DELETE SET NULL,
                device_type TEXT NOT NULL,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                serial_number TEXT,
                problem_description TEXT NOT NULL,
                parts_cost REAL NOT NULL DEFAULT 0.0 CHECK(parts_cost >= 0),
                labor_cost REAL NOT NULL DEFAULT 0.0 CHECK(labor_cost >= 0),
                total_cost REAL NOT NULL DEFAULT 0.0 CHECK(total_cost >= 0),
                amount_paid REAL NOT NULL DEFAULT 0.0 CHECK(amount_paid >= 0),
                is_paid INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Received' CHECK(status IN ('Received', 'Diagnosing', 'Repairing', 'Completed', 'Collected')),
                received_date DATE NOT NULL,
                completed_date DATE,
                collected_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
