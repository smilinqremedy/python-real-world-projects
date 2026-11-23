"""
Database persistence for Network Intrusion Detection System (NIDS).
Stores network packet metadata, flow records, and security alerts.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "nids_events.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS network_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            datetime_str TEXT NOT NULL,
            src_ip TEXT NOT NULL,
            dst_ip TEXT NOT NULL,
            protocol TEXT NOT NULL,
            src_port INTEGER,
            dst_port INTEGER,
            packet_size INTEGER NOT NULL,
            flags TEXT
        );

        CREATE TABLE IF NOT EXISTS security_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            datetime_str TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
            src_ip TEXT NOT NULL,
            dst_ip TEXT,
            rule_triggered TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT CHECK(status IN ('New', 'Investigating', 'Resolved', 'False Positive')) DEFAULT 'New'
        );

        CREATE INDEX IF NOT EXISTS idx_net_src ON network_events(src_ip);
        CREATE INDEX IF NOT EXISTS idx_net_time ON network_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_alert_type ON security_alerts(alert_type);
        CREATE INDEX IF NOT EXISTS idx_alert_sev ON security_alerts(severity);
        """)
    conn.close()
