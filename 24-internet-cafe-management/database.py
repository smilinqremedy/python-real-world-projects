"""
Database schema and configuration for Internet Cafe Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "internet_cafe.db"


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
            CREATE TABLE IF NOT EXISTS computers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computer_code TEXT UNIQUE NOT NULL,
                ip_address TEXT NOT NULL,
                specs TEXT NOT NULL,
                hourly_rate REAL NOT NULL CHECK(hourly_rate > 0),
                status TEXT NOT NULL DEFAULT 'Available' CHECK(status IN ('Available', 'In Use', 'Maintenance')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                computer_id INTEGER NOT NULL REFERENCES computers(id),
                customer_name TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_minutes INTEGER DEFAULT 0,
                hourly_rate_applied REAL NOT NULL,
                total_bill REAL NOT NULL DEFAULT 0.0 CHECK(total_bill >= 0),
                payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
                amount_paid REAL NOT NULL DEFAULT 0.0 CHECK(amount_paid >= 0),
                status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
