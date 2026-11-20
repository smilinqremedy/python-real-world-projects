"""
Database schema and initialization for Nigerian Tax and Business Revenue Calculator.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "business_finance.db")


def get_connection(db_path=None):
    """Establish SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Initialize SQLite database tables with constraints and default tax rules."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        -- Registered Business Profile
        CREATE TABLE IF NOT EXISTS business_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            rc_number TEXT UNIQUE NOT NULL,
            tin TEXT UNIQUE,
            business_type TEXT CHECK(business_type IN ('Sole Proprietorship', 'Partnership', 'Limited Liability Company (LLC)', 'Enterprise')) NOT NULL,
            sector TEXT NOT NULL,
            contact_email TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            address TEXT,
            currency TEXT DEFAULT 'NGN',
            currency_symbol TEXT DEFAULT '₦',
            financial_year_start TEXT DEFAULT '01-01',
            financial_year_end TEXT DEFAULT '12-31',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Configurable Tax Rules (Nigerian Finance Act / CITA / PITA)
        CREATE TABLE IF NOT EXISTS tax_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_name TEXT NOT NULL,
            small_turnover_threshold REAL DEFAULT 25000000.0 CHECK(small_turnover_threshold >= 0),
            medium_turnover_threshold REAL DEFAULT 100000000.0 CHECK(medium_turnover_threshold >= small_turnover_threshold),
            small_cit_rate REAL DEFAULT 0.0 CHECK(small_cit_rate >= 0 AND small_cit_rate <= 1),
            medium_cit_rate REAL DEFAULT 0.20 CHECK(medium_cit_rate >= 0 AND medium_cit_rate <= 1),
            large_cit_rate REAL DEFAULT 0.30 CHECK(large_cit_rate >= 0 AND large_cit_rate <= 1),
            education_tax_rate REAL DEFAULT 0.03 CHECK(education_tax_rate >= 0 AND education_tax_rate <= 1),
            vat_rate REAL DEFAULT 0.075 CHECK(vat_rate >= 0 AND vat_rate <= 1),
            minimum_tax_rate REAL DEFAULT 0.005 CHECK(minimum_tax_rate >= 0 AND minimum_tax_rate <= 1),
            wht_standard_rate REAL DEFAULT 0.05 CHECK(wht_standard_rate >= 0 AND wht_standard_rate <= 1),
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Daily Sales & Revenue Entries
        CREATE TABLE IF NOT EXISTS sales_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_ref TEXT UNIQUE NOT NULL,
            sale_date TEXT NOT NULL,
            customer_name TEXT,
            category TEXT NOT NULL CHECK(category IN ('Product Sales', 'Services Rendered', 'Wholesale', 'Consulting', 'Commission', 'Other Revenue')),
            description TEXT NOT NULL,
            gross_amount REAL NOT NULL CHECK(gross_amount > 0),
            vat_applied INTEGER DEFAULT 0 CHECK(vat_applied IN (0, 1)),
            vat_amount REAL DEFAULT 0.0 CHECK(vat_amount >= 0),
            net_amount REAL NOT NULL CHECK(net_amount > 0),
            payment_method TEXT CHECK(payment_method IN ('Bank Transfer', 'POS', 'Cash', 'Cheque', 'Online Payment')) DEFAULT 'Bank Transfer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Business Expenses Entries
        CREATE TABLE IF NOT EXISTS expense_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_ref TEXT UNIQUE NOT NULL,
            expense_date TEXT NOT NULL,
            vendor_name TEXT,
            category TEXT NOT NULL,
            expense_type TEXT NOT NULL CHECK(expense_type IN ('COGS', 'Operating', 'Capital')),
            description TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            is_tax_deductible INTEGER DEFAULT 1 CHECK(is_tax_deductible IN (0, 1)),
            receipt_ref TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Saved Tax Estimations & Snapshot History
        CREATE TABLE IF NOT EXISTS tax_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_label TEXT NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            total_turnover REAL NOT NULL,
            cost_of_goods_sold REAL NOT NULL,
            gross_profit REAL NOT NULL,
            operating_expenses REAL NOT NULL,
            net_profit REAL NOT NULL,
            taxable_profit REAL NOT NULL,
            cit_rate_applied REAL NOT NULL,
            estimated_cit REAL NOT NULL,
            estimated_edt REAL NOT NULL,
            estimated_vat_collected REAL NOT NULL,
            estimated_minimum_tax REAL NOT NULL,
            estimated_total_tax REAL NOT NULL,
            assumptions TEXT NOT NULL,
            disclaimer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for query optimization
        CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_transactions(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_transactions(category);
        CREATE INDEX IF NOT EXISTS idx_expenses_date ON expense_transactions(expense_date);
        CREATE INDEX IF NOT EXISTS idx_expenses_type ON expense_transactions(expense_type);
        CREATE INDEX IF NOT EXISTS idx_expenses_category ON expense_transactions(category);
        """)

        # Insert default Nigerian tax rules if none exist
        existing = conn.execute("SELECT count(*) FROM tax_rules").fetchone()[0]
        if existing == 0:
            conn.execute("""
            INSERT INTO tax_rules (
                rule_name, small_turnover_threshold, medium_turnover_threshold,
                small_cit_rate, medium_cit_rate, large_cit_rate, education_tax_rate,
                vat_rate, minimum_tax_rate, wht_standard_rate, is_active
            ) VALUES ('Nigeria Finance Act Baseline', 25000000.0, 100000000.0, 0.0, 0.20, 0.30, 0.03, 0.075, 0.005, 0.05, 1)
            """)

    conn.close()
