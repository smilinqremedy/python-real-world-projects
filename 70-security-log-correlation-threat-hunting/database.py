"""
Database schema for Security Log Correlation & Threat Hunting Tool.
Stores unified normalized telemetry across authentication, web, and network firewalls.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "threat_hunting.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS normalized_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            epoch_time REAL NOT NULL,
            source_type TEXT CHECK(source_type IN ('Auth', 'Web', 'Firewall')) NOT NULL,
            ip_address TEXT,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            status_code INTEGER,
            bytes_transferred INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS correlated_threats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
            rule_id TEXT NOT NULL,
            ip_address TEXT,
            username TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            timeline_summary TEXT NOT NULL,
            investigation_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_norm_time ON normalized_logs(epoch_time);
        CREATE INDEX IF NOT EXISTS idx_norm_ip ON normalized_logs(ip_address);
        CREATE INDEX IF NOT EXISTS idx_norm_user ON normalized_logs(username);
        CREATE INDEX IF NOT EXISTS idx_threat_sev ON correlated_threats(severity);
        """)
    conn.close()
