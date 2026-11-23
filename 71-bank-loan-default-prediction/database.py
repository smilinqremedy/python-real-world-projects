"""
Database schema for Bank Loan Default Prediction System.
Maintains historical and incoming loan applications, borrower profiles,
predicted default probabilities, risk categories, and underwriting decisions.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "loan_predictions.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS loan_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_ref TEXT UNIQUE NOT NULL,
            applicant_name TEXT NOT NULL,
            annual_income REAL NOT NULL CHECK(annual_income > 0),
            loan_amount REAL NOT NULL CHECK(loan_amount > 0),
            interest_rate REAL NOT NULL CHECK(interest_rate > 0),
            employment_years INTEGER NOT NULL CHECK(employment_years >= 0),
            debt_to_income REAL NOT NULL CHECK(debt_to_income >= 0),
            credit_score INTEGER NOT NULL CHECK(credit_score >= 300 AND credit_score <= 850),
            previous_defaults INTEGER NOT NULL DEFAULT 0 CHECK(previous_defaults >= 0),
            default_probability REAL NOT NULL CHECK(default_probability >= 0.0 AND default_probability <= 1.0),
            risk_category TEXT CHECK(risk_category IN ('Low Risk', 'Medium Risk', 'High Risk')) NOT NULL,
            underwriting_recommendation TEXT NOT NULL,
            status TEXT CHECK(status IN ('Pending Underwriting', 'Approved', 'Rejected', 'Collateral Required')) DEFAULT 'Pending Underwriting',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS model_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            precision_val REAL NOT NULL,
            recall_val REAL NOT NULL,
            f1_val REAL NOT NULL,
            roc_auc REAL NOT NULL,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_loan_ref ON loan_applications(application_ref);
        CREATE INDEX IF NOT EXISTS idx_loan_risk ON loan_applications(risk_category);
        """)
    conn.close()
