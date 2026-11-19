"""
Database configuration and schema for Event Registration and Ticketing System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "event_ticketing.db"


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
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                event_date DATE NOT NULL,
                location TEXT NOT NULL,
                ticket_price REAL NOT NULL CHECK(ticket_price >= 0),
                max_capacity INTEGER NOT NULL CHECK(max_capacity > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attendees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE NOT NULL,
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                attendee_id INTEGER NOT NULL REFERENCES attendees(id),
                purchase_date DATE NOT NULL,
                price_paid REAL NOT NULL CHECK(price_paid >= 0),
                payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
                is_checked_in INTEGER NOT NULL DEFAULT 0,
                check_in_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(event_id, attendee_id)
            );
        """)
    conn.close()
