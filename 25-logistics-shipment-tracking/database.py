"""
Database configuration and schema for Logistics and Shipment Tracking System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "logistics_tracking.db"


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
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS couriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                courier_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                vehicle_type TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_number TEXT UNIQUE NOT NULL,
                sender_id INTEGER NOT NULL REFERENCES customers(id),
                receiver_name TEXT NOT NULL,
                receiver_phone TEXT NOT NULL,
                receiver_address TEXT NOT NULL,
                destination_city TEXT NOT NULL,
                parcel_description TEXT NOT NULL,
                weight_kg REAL NOT NULL CHECK(weight_kg > 0),
                shipping_tier TEXT NOT NULL DEFAULT 'Standard' CHECK(shipping_tier IN ('Standard', 'Express', 'Overnight')),
                delivery_fee REAL NOT NULL CHECK(delivery_fee > 0),
                courier_id INTEGER REFERENCES couriers(id) ON DELETE SET NULL,
                status TEXT NOT NULL DEFAULT 'Created' CHECK(status IN ('Created', 'Assigned', 'In Transit', 'Out for Delivery', 'Delivered', 'Cancelled')),
                payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
                created_date DATE NOT NULL,
                delivered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tracking_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
                location TEXT NOT NULL,
                status_update TEXT NOT NULL,
                remarks TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
