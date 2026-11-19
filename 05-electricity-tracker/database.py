"""
Database Layer for Electricity and Household Power Consumption Tracker
Manages SQLite schema creation, connections, and initial configuration.
"""

import sqlite3
from datetime import datetime

DEFAULT_DB_FILE = "power_tracker.db"


def get_db_connection(db_path=DEFAULT_DB_FILE):
    """
    Creates and returns a SQLite connection configured with Row factory.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path=DEFAULT_DB_FILE):
    """
    Creates required database tables and default configuration settings.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Prepaid Electricity Purchases
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prepaid_purchases (
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_date TEXT NOT NULL,
            amount_paid REAL NOT NULL CHECK(amount_paid > 0),
            units_credited REAL NOT NULL CHECK(units_credited > 0),
            unit_rate REAL NOT NULL,
            token_number TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # 2. Electricity Daily Consumption Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS electricity_consumption (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL UNIQUE,
            units_consumed REAL NOT NULL CHECK(units_consumed >= 0),
            meter_reading REAL,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # 3. Generator Fuel Expenses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS generator_expenses (
            fuel_id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            fuel_type TEXT NOT NULL DEFAULT 'Petrol',
            liters_bought REAL NOT NULL CHECK(liters_bought > 0),
            cost_per_liter REAL NOT NULL CHECK(cost_per_liter > 0),
            total_cost REAL NOT NULL CHECK(total_cost > 0),
            run_hours REAL CHECK(run_hours >= 0),
            notes TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # 4. Application Settings (Key-Value)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        );
        """)

        # Default alert threshold: 20.0 kWh
        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (setting_key, setting_value)
        VALUES ('low_units_threshold', '20.0');
        """)

        # Default fallback electricity tariff per kWh: $0.20
        cursor.execute("""
        INSERT OR IGNORE INTO app_settings (setting_key, setting_value)
        VALUES ('default_tariff_rate', '0.20');
        """)

        conn.commit()
