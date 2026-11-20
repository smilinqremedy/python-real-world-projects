"""
Database initialization and schema for Digital Asset and Equipment Assignment Tracker.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "asset_tracker.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            designation TEXT NOT NULL,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_tag TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL, -- Laptop, Mobile Phone, Monitor, Peripheral, Furniture, Networking
            model_number TEXT,
            serial_number TEXT UNIQUE NOT NULL,
            purchase_date TEXT NOT NULL,
            purchase_cost REAL NOT NULL CHECK(purchase_cost >= 0),
            current_condition TEXT CHECK(current_condition IN ('New', 'Good', 'Fair', 'Damaged', 'Broken')) NOT NULL,
            status TEXT CHECK(status IN ('Available', 'Assigned', 'Under Repair', 'Damaged', 'Lost / Missing', 'Retired')) DEFAULT 'Available',
            current_holder_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS asset_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_ref TEXT UNIQUE NOT NULL,
            asset_id INTEGER REFERENCES assets(id) ON DELETE RESTRICT NOT NULL,
            employee_id INTEGER REFERENCES employees(id) ON DELETE RESTRICT NOT NULL,
            assigned_date TEXT NOT NULL,
            expected_return_date TEXT,
            returned_date TEXT,
            condition_at_assignment TEXT NOT NULL,
            condition_at_return TEXT,
            status TEXT CHECK(status IN ('Active', 'Returned', 'Overdue', 'Marked Missing')) DEFAULT 'Active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS asset_condition_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE NOT NULL,
            previous_condition TEXT,
            new_condition TEXT NOT NULL,
            action TEXT NOT NULL, -- e.g. Assignment, Return, Damage Report, Repair Completed
            recorded_by TEXT,
            notes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_assets_tag ON assets(asset_tag);
        CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
        CREATE INDEX IF NOT EXISTS idx_emp_id ON employees(employee_id);
        CREATE INDEX IF NOT EXISTS idx_assign_asset ON asset_assignments(asset_id);
        CREATE INDEX IF NOT EXISTS idx_assign_emp ON asset_assignments(employee_id);
        """)
    conn.close()
