"""
Database schema for Supplier Purchase Order Management System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "purchase_orders.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_code TEXT UNIQUE NOT NULL,
            company_name TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
            stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
            reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level >= 0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE RESTRICT NOT NULL,
            order_date TEXT NOT NULL,
            expected_date TEXT,
            status TEXT CHECK(status IN ('Draft', 'Approved', 'Partially Delivered', 'Completed', 'Cancelled')) DEFAULT 'Draft',
            total_amount REAL NOT NULL DEFAULT 0.0 CHECK(total_amount >= 0),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS po_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER REFERENCES purchase_orders(id) ON DELETE CASCADE NOT NULL,
            product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT NOT NULL,
            quantity_ordered INTEGER NOT NULL CHECK(quantity_ordered > 0),
            unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
            quantity_received INTEGER NOT NULL DEFAULT 0 CHECK(quantity_received >= 0),
            subtotal REAL NOT NULL CHECK(subtotal >= 0),
            UNIQUE(po_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS delivery_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_item_id INTEGER REFERENCES po_items(id) ON DELETE CASCADE NOT NULL,
            quantity_delivered INTEGER NOT NULL CHECK(quantity_delivered > 0),
            delivery_date TEXT NOT NULL,
            received_by TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS supplier_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE RESTRICT NOT NULL,
            po_id INTEGER REFERENCES purchase_orders(id) ON DELETE SET NULL,
            payment_ref TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_method TEXT CHECK(payment_method IN ('Bank Transfer', 'Cheque', 'Cash', 'Credit Card')) DEFAULT 'Bank Transfer',
            payment_date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_po_num ON purchase_orders(po_number);
        CREATE INDEX IF NOT EXISTS idx_po_sup ON purchase_orders(supplier_id);
        CREATE INDEX IF NOT EXISTS idx_po_status ON purchase_orders(status);
        CREATE INDEX IF NOT EXISTS idx_prod_sku ON products(sku);
        """)
    conn.close()
