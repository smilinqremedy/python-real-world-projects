"""
Database configuration and schema for Employee Attendance Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "attendance.db"


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
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                shift_start_time TEXT NOT NULL DEFAULT '09:00',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
                attendance_date DATE NOT NULL,
                check_in_time TEXT,
                check_out_time TEXT,
                is_late INTEGER NOT NULL DEFAULT 0,
                minutes_late INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Present' CHECK(status IN ('Present', 'Half-Day', 'Absent')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, attendance_date)
            );
        """)
    conn.close()
