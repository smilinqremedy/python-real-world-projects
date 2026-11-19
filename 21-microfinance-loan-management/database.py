"""
Database configuration and schema for Microfinance Loan Management System.
"""

import sqlite3
from typing import Optional

DEFAULT_DB_PATH = "microfinance.db"


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
            CREATE TABLE IF NOT EXISTS borrowers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                borrower_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                monthly_income REAL NOT NULL CHECK(monthly_income >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_reference TEXT UNIQUE NOT NULL,
                borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
                principal_amount REAL NOT NULL CHECK(principal_amount > 0),
                interest_rate_percent REAL NOT NULL CHECK(interest_rate_percent >= 0),
                repayment_period_months INTEGER NOT NULL CHECK(repayment_period_months > 0),
                total_interest REAL NOT NULL CHECK(total_interest >= 0),
                total_payable REAL NOT NULL CHECK(total_payable > 0),
                monthly_installment REAL NOT NULL CHECK(monthly_installment > 0),
                amount_repaid REAL NOT NULL DEFAULT 0.0 CHECK(amount_repaid >= 0),
                status TEXT NOT NULL DEFAULT 'Applied' CHECK(status IN ('Applied', 'Approved', 'Rejected', 'Active', 'Repaid', 'Defaulted')),
                application_date DATE NOT NULL,
                approval_date DATE,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS repayments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_reference TEXT UNIQUE NOT NULL,
                loan_id INTEGER NOT NULL REFERENCES loans(id),
                amount REAL NOT NULL CHECK(amount > 0),
                payment_date DATE NOT NULL,
                payment_method TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS excess_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                excess_reference TEXT UNIQUE NOT NULL,
                loan_id INTEGER NOT NULL REFERENCES loans(id),
                excess_amount REAL NOT NULL CHECK(excess_amount > 0),
                payment_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.close()
