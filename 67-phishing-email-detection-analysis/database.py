"""
Database schema for Phishing Email Detection & Analysis Tool.
Stores parsed email metadata, risk ratings, and identified phishing indicators.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "phishing_analysis.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS email_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            subject TEXT NOT NULL,
            sender_display TEXT,
            sender_email TEXT NOT NULL,
            reply_to TEXT,
            date_header TEXT,
            risk_score INTEGER NOT NULL CHECK(risk_score >= 0 AND risk_score <= 100),
            verdict TEXT CHECK(verdict IN ('Low Risk', 'Suspicious', 'Phishing')) NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS phishing_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER REFERENCES email_analyses(id) ON DELETE CASCADE NOT NULL,
            category TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
            description TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_phish_verdict ON email_analyses(verdict);
        CREATE INDEX IF NOT EXISTS idx_phish_score ON email_analyses(risk_score);
        """)
    conn.close()
