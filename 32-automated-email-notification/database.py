"""
Database schema and connection management for Automated Email Notification System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "notifications.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            consent_status TEXT NOT NULL DEFAULT 'subscribed' CHECK(consent_status IN ('subscribed', 'unsubscribed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            subject_template TEXT NOT NULL,
            body_template TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT NOT NULL,
            recipient_name TEXT,
            template_name TEXT,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')),
            retry_count INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3,
            idempotency_key TEXT UNIQUE,
            last_error TEXT,
            sent_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_id INTEGER REFERENCES email_queue(id) ON DELETE SET NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'simulated')),
            delivery_mode TEXT NOT NULL,
            error_message TEXT,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_queue_status_sched ON email_queue(status, scheduled_at);
        CREATE INDEX IF NOT EXISTS idx_logs_recipient ON email_logs(recipient_email);
        CREATE INDEX IF NOT EXISTS idx_logs_status ON email_logs(status);
        """)
    conn.close()
