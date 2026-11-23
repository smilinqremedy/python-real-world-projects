"""
Database schema for Digital Forensics File Metadata Analyzer.
Maintains forensic evidence records, cryptographic baselines, and integrity audit trails.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "forensics_evidence.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS forensic_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            investigator TEXT NOT NULL,
            target_directory TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS evidence_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER REFERENCES forensic_cases(id) ON DELETE CASCADE NOT NULL,
            relative_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            extension TEXT NOT NULL,
            size_bytes INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            md5 TEXT NOT NULL,
            created_timestamp TEXT NOT NULL,
            modified_timestamp TEXT NOT NULL,
            accessed_timestamp TEXT NOT NULL,
            is_duplicate INTEGER DEFAULT 0 CHECK(is_duplicate IN (0, 1)),
            duplicate_group_hash TEXT,
            suspicious_flags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS integrity_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER REFERENCES forensic_cases(id) ON DELETE CASCADE NOT NULL,
            verification_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_checked INTEGER NOT NULL,
            intact_count INTEGER NOT NULL,
            modified_count INTEGER NOT NULL,
            missing_count INTEGER NOT NULL,
            summary_notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_evid_case ON evidence_items(case_id);
        CREATE INDEX IF NOT EXISTS idx_evid_sha ON evidence_items(sha256);
        """)
    conn.close()
