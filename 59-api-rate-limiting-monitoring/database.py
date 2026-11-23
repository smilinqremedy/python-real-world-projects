"""
Database schema for API Rate Limiting & Request Monitoring System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "api_monitoring.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES api_users(id) ON DELETE CASCADE NOT NULL,
            key_value TEXT UNIQUE NOT NULL,
            tier TEXT CHECK(tier IN ('free', 'starter', 'pro', 'unlimited')) DEFAULT 'free',
            rate_limit_per_minute INTEGER NOT NULL CHECK(rate_limit_per_minute > 0),
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            ip_address TEXT,
            duration_ms REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_api_key_val ON api_keys(key_value);
        CREATE INDEX IF NOT EXISTS idx_req_logs_key ON request_logs(api_key_id);
        CREATE INDEX IF NOT EXISTS idx_req_logs_time ON request_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_req_logs_status ON request_logs(status_code);
        """)
    conn.close()
