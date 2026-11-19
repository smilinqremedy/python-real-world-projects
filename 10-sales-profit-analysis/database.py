"""
Database Layer for Small Business Sales and Profit Analysis System
Manages SQLite schema creation, foreign key constraints, and default data seeds.
"""

import sqlite3

DEFAULT_DB_FILE = "sales_profit.db"

EXPENSE_CATEGORIES = [
    "Rent & Facilities",
    "Staff Salaries & Wages",
    "Utilities (Power, Water, Internet)",
    "Marketing & Advertising",
    "Logistics & Delivery",
    "Packaging & Office Supplies",
    "Equipment & Maintenance",
    "Taxes & Licenses",
    "Other Operating Costs"
]

PRODUCT_CATEGORIES = [
    "Electronics & Accessories",
    "Apparel & Fashion",
    "Groceries & Foodstuffs",
    "Health & Beauty",
    "Home & Living",
    "General Retail"
]


def get_db_connection(db_path=DEFAULT_DB_FILE):
    """
    Creates and returns a SQLite connection configured with Row factory and foreign keys.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path=DEFAULT_DB_FILE):
    """
    Initializes tables, indexes, and constraints.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Products Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'General Retail',
            cost_price REAL NOT NULL CHECK(cost_price > 0),
            selling_price REAL NOT NULL CHECK(selling_price > 0),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # 2. Sales Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_cost_price REAL NOT NULL CHECK(unit_cost_price > 0),
            unit_selling_price REAL NOT NULL CHECK(unit_selling_price > 0),
            total_revenue REAL NOT NULL,
            total_cogs REAL NOT NULL,
            gross_profit REAL NOT NULL,
            customer_notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
        );
        """)

        # 3. Operational Expenses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS operational_expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

        # Indexes for analytical performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON operational_expenses(expense_date);")

        conn.commit()
