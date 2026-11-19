"""
Database configuration and schema definition for Property Rental Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "property_rental.db"


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
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                monthly_rent REAL NOT NULL CHECK(monthly_rent > 0),
                status TEXT NOT NULL DEFAULT 'Vacant' CHECK(status IN ('Vacant', 'Occupied')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                property_id INTEGER UNIQUE REFERENCES properties(id) ON DELETE SET NULL,
                lease_start_date DATE NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rent_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_ref TEXT UNIQUE NOT NULL,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                property_id INTEGER NOT NULL REFERENCES properties(id),
                amount REAL NOT NULL CHECK(amount > 0),
                payment_date DATE NOT NULL,
                period_month TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
