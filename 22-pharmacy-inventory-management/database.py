"""
Database configuration and schema for Pharmacy Inventory and Sales Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "pharmacy.db"


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
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit TEXT NOT NULL,
                reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
                batch_number TEXT UNIQUE NOT NULL,
                cost_price REAL NOT NULL CHECK(cost_price >= 0),
                selling_price REAL NOT NULL CHECK(selling_price >= cost_price),
                initial_quantity INTEGER NOT NULL CHECK(initial_quantity > 0),
                current_quantity INTEGER NOT NULL CHECK(current_quantity >= 0),
                manufacture_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                batch_id INTEGER NOT NULL REFERENCES batches(id),
                medicine_id INTEGER NOT NULL REFERENCES medicines(id),
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price > 0),
                total_price REAL NOT NULL CHECK(total_price > 0),
                sale_date DATE NOT NULL,
                customer_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
