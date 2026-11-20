"""
Database schema for Fuel Station Sales & Tank Monitoring System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fuel_station.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS fuel_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL, -- e.g. PMS (Petrol), AGO (Diesel), DPK (Kerosene)
            name TEXT NOT NULL,
            unit_price TEXT NOT NULL, -- Stored as text to preserve exact Decimal representation
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS storage_tanks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tank_code TEXT UNIQUE NOT NULL, -- e.g. TK-PMS-01, TK-AGO-01
            product_id INTEGER REFERENCES fuel_products(id) ON DELETE RESTRICT NOT NULL,
            capacity_litres TEXT NOT NULL,
            current_volume_litres TEXT NOT NULL,
            last_reconciled_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fuel_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_ref TEXT UNIQUE NOT NULL,
            tank_id INTEGER REFERENCES storage_tanks(id) ON DELETE RESTRICT NOT NULL,
            supplier_name TEXT NOT NULL,
            waybill_number TEXT,
            quantity_litres TEXT NOT NULL,
            unit_cost TEXT NOT NULL,
            total_cost TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pump_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_ref TEXT UNIQUE NOT NULL,
            tank_id INTEGER REFERENCES storage_tanks(id) ON DELETE RESTRICT NOT NULL,
            pump_id TEXT NOT NULL,
            sale_date TEXT NOT NULL,
            opening_meter TEXT NOT NULL,
            closing_meter TEXT NOT NULL,
            litres_sold TEXT NOT NULL,
            unit_price TEXT NOT NULL,
            total_revenue TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tank_reconciliations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recon_ref TEXT UNIQUE NOT NULL,
            tank_id INTEGER REFERENCES storage_tanks(id) ON DELETE RESTRICT NOT NULL,
            reconciliation_date TEXT NOT NULL,
            opening_dip_litres TEXT NOT NULL,
            deliveries_received_litres TEXT NOT NULL,
            pump_sales_litres TEXT NOT NULL,
            expected_closing_litres TEXT NOT NULL,
            actual_closing_dip_litres TEXT NOT NULL,
            discrepancy_litres TEXT NOT NULL,
            discrepancy_status TEXT NOT NULL, -- Balanced, Normal Variance, Significant Shortage, Unaccounted Gain
            total_revenue TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_tank_code ON storage_tanks(tank_code);
        CREATE INDEX IF NOT EXISTS idx_sales_date ON pump_sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_deliv_date ON fuel_deliveries(delivery_date);
        CREATE INDEX IF NOT EXISTS idx_recon_date ON tank_reconciliations(reconciliation_date);
        """)
    conn.close()
