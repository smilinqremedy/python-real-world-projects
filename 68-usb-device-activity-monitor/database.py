"""
Database schema for USB Device Activity Monitoring & Audit System.
Stores approved device allowlists, connection/disconnection event logs, and security alerts.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "usb_monitor.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS approved_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE NOT NULL,
            vendor_name TEXT NOT NULL,
            product_name TEXT NOT NULL,
            vendor_id TEXT NOT NULL, -- e.g. '0951'
            product_id TEXT NOT NULL, -- e.g. '1666'
            approved_by TEXT NOT NULL,
            approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS device_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT CHECK(event_type IN ('CONNECTED', 'DISCONNECTED')) NOT NULL,
            serial_number TEXT NOT NULL,
            vendor_name TEXT,
            product_name TEXT,
            vendor_id TEXT,
            product_id TEXT,
            device_type TEXT DEFAULT 'Mass Storage',
            host TEXT NOT NULL,
            user TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            is_approved INTEGER NOT NULL CHECK(is_approved IN (0, 1)),
            alert_triggered INTEGER DEFAULT 0 CHECK(alert_triggered IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS device_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER REFERENCES device_events(id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL,
            host TEXT NOT NULL,
            user TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
            serial_number TEXT NOT NULL,
            details TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_usb_serial ON device_events(serial_number);
        CREATE INDEX IF NOT EXISTS idx_usb_app ON approved_devices(serial_number);
        CREATE INDEX IF NOT EXISTS idx_usb_alerts ON device_alerts(severity);
        """)
    conn.close()
