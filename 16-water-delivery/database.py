"""
Database configuration and schema for Water Delivery Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "water_delivery.db"


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
                default_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                vehicle_plate TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
                delivery_address TEXT NOT NULL,
                container_type TEXT NOT NULL DEFAULT '20L Jug',
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                container_unit_price REAL NOT NULL CHECK(container_unit_price > 0),
                delivery_fee REAL NOT NULL DEFAULT 0.0 CHECK(delivery_fee >= 0),
                total_charge REAL NOT NULL CHECK(total_charge > 0),
                payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
                payment_method TEXT,
                status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Assigned', 'Out for Delivery', 'Delivered', 'Cancelled')),
                order_date DATE NOT NULL,
                delivered_at TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
