"""
Database schema for Security Incident Response Management System (SIRMS).
Enforces relational integrity, audit trails, evidence references, and RBAC accounts.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "incident_response.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('Analyst', 'Lead', 'Admin')) NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_ref TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')) NOT NULL,
            category TEXT CHECK(category IN ('Phishing', 'Malware', 'Data Breach', 'Unauthorized Access', 'DDoS', 'Insider Threat', 'System Compromise')) NOT NULL,
            status TEXT CHECK(status IN ('Reported', 'Investigating', 'Contained', 'Eradicated', 'Recovered', 'Closed')) DEFAULT 'Reported',
            lead_analyst_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_by_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS incident_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            note_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS evidence_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE NOT NULL,
            evidence_type TEXT CHECK(evidence_type IN ('Log', 'File Hash', 'Network PCAP', 'Memory Dump', 'Disk Image', 'Screenshot', 'Email Artifact')) NOT NULL,
            reference_locator TEXT NOT NULL,
            description TEXT NOT NULL,
            sha256 TEXT,
            added_by_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            action TEXT NOT NULL,
            previous_state TEXT,
            new_state TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_inc_ref ON incidents(incident_ref);
        CREATE INDEX IF NOT EXISTS idx_inc_status ON incidents(status);
        CREATE INDEX IF NOT EXISTS idx_inc_sev ON incidents(severity);
        CREATE INDEX IF NOT EXISTS idx_audit_inc ON audit_logs(incident_id);
        """)
    conn.close()
