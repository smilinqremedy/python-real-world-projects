"""
Database schema for Customer Subscription & Renewal Management System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "subscriptions.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            company TEXT,
            status TEXT CHECK(status IN ('Active', 'Inactive')) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_code TEXT UNIQUE NOT NULL, -- e.g. STARTER-M, PRO-M, PRO-Y, ENTERPRISE-Y
            name TEXT NOT NULL,
            billing_cycle TEXT CHECK(billing_cycle IN ('Monthly', 'Quarterly', 'Yearly')) NOT NULL,
            price REAL NOT NULL CHECK(price > 0),
            description TEXT,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_ref TEXT UNIQUE NOT NULL,
            customer_id INTEGER REFERENCES customers(id) ON DELETE RESTRICT NOT NULL,
            plan_id INTEGER REFERENCES subscription_plans(id) ON DELETE RESTRICT NOT NULL,
            start_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT CHECK(status IN ('Active', 'Grace Period', 'Suspended', 'Cancelled')) DEFAULT 'Active',
            auto_renew INTEGER DEFAULT 1 CHECK(auto_renew IN (0, 1)),
            cancellation_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subscription_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_ref TEXT UNIQUE NOT NULL,
            subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE RESTRICT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_method TEXT CHECK(payment_method IN ('Credit Card', 'Bank Transfer', 'Direct Debit', 'PayPal')) DEFAULT 'Credit Card',
            payment_date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS renewal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE NOT NULL,
            previous_expiry TEXT NOT NULL,
            new_expiry TEXT NOT NULL,
            amount_paid REAL NOT NULL,
            renewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_sub_ref ON subscriptions(subscription_ref);
        CREATE INDEX IF NOT EXISTS idx_sub_cust ON subscriptions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_sub_expiry ON subscriptions(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_sub_status ON subscriptions(status);
        """)
    conn.close()
