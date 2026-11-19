"""
Database configuration and schema for Laundry Service Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "laundry.db"


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

            CREATE TABLE IF NOT EXISTS service_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT UNIQUE NOT NULL,
                price_per_item REAL NOT NULL CHECK(price_per_item > 0)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                total_items INTEGER NOT NULL DEFAULT 0,
                total_charge REAL NOT NULL DEFAULT 0.0,
                amount_paid REAL NOT NULL DEFAULT 0.0,
                payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Partial', 'Paid')),
                status TEXT NOT NULL DEFAULT 'Received' CHECK(status IN ('Received', 'Washing', 'Ready', 'Collected')),
                order_date DATE NOT NULL,
                ready_date DATE,
                collected_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                item_type TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price > 0),
                subtotal REAL NOT NULL CHECK(subtotal > 0)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_ref TEXT UNIQUE NOT NULL,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                amount REAL NOT NULL CHECK(amount > 0),
                payment_date DATE NOT NULL,
                payment_method TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
