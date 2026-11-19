"""
Database configuration and schema for Donation and Charity Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "charity_management.db"


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
            CREATE TABLE IF NOT EXISTS donors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                donor_type TEXT NOT NULL DEFAULT 'Individual' CHECK(donor_type IN ('Individual', 'Corporate', 'Foundation')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Closed', 'Paused')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_reference TEXT UNIQUE NOT NULL,
                donor_id INTEGER NOT NULL REFERENCES donors(id),
                campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
                amount REAL NOT NULL CHECK(amount > 0),
                donation_date DATE NOT NULL,
                payment_method TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS disbursements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disbursement_reference TEXT UNIQUE NOT NULL,
                campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
                purpose TEXT NOT NULL,
                recipient TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                disbursement_date DATE NOT NULL,
                approval_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
