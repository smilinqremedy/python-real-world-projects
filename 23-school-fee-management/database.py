"""
Database configuration and schema for School Fee Payment Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "school_fees.db"


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
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                academic_session TEXT NOT NULL,
                term_fee REAL NOT NULL CHECK(term_fee > 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_reg_no TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                class_id INTEGER NOT NULL REFERENCES classes(id),
                parent_name TEXT NOT NULL,
                parent_phone TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_reference TEXT UNIQUE NOT NULL,
                student_id INTEGER NOT NULL REFERENCES students(id),
                amount REAL NOT NULL CHECK(amount > 0),
                payment_date DATE NOT NULL,
                payment_method TEXT NOT NULL,
                academic_term TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
