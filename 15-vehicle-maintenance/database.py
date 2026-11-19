"""
Database configuration and schema for Vehicle Maintenance Tracking System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "vehicle_maintenance.db"


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
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_number TEXT UNIQUE NOT NULL,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL CHECK(year >= 1900),
                current_mileage INTEGER NOT NULL CHECK(current_mileage >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                service_type TEXT NOT NULL,
                service_date DATE NOT NULL,
                mileage_at_service INTEGER NOT NULL CHECK(mileage_at_service >= 0),
                cost REAL NOT NULL CHECK(cost >= 0),
                service_provider TEXT,
                notes TEXT,
                next_due_date DATE,
                next_due_mileage INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
