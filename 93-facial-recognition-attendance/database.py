"""
Database schema and persistence module for Facial Recognition Attendance System.
Enforces unique session-attendance constraints and comprehensive audit logging.
"""
import sqlite3
import os
import io
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance_system.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initializes tables for admins, participants, sessions, attendance records, and audit logs."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Admin & Operator users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operator',
                created_at TEXT NOT NULL
            );
        """)

        # Registered participants (biometric consent and embeddings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                email TEXT,
                consent_granted INTEGER NOT NULL,
                consent_timestamp TEXT,
                opt_in_biometrics INTEGER NOT NULL,
                biometric_embedding BLOB,
                created_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );
        """)

        # Attendance sessions (e.g. Daily Shift, Lecture, Meeting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_code TEXT UNIQUE NOT NULL,
                session_name TEXT NOT NULL,
                session_date TEXT NOT NULL,
                created_by TEXT NOT NULL,
                is_open INTEGER NOT NULL DEFAULT 1
            );
        """)

        # Attendance check-in records: Strictly UNIQUE(session_id, participant_id) to prevent duplicates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                participant_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                date TEXT NOT NULL,
                method TEXT NOT NULL, -- 'facial_biometric' or 'manual_alternative'
                confidence_score REAL,
                verified_by TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'present', -- 'present', 'corrected', 'excused'
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES attendance_sessions (id),
                FOREIGN KEY (participant_id) REFERENCES participants (id),
                UNIQUE(session_id, participant_id)
            );
        """)

        # Security & Audit Trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                actor_username TEXT NOT NULL,
                action_type TEXT NOT NULL,
                details TEXT NOT NULL
            );
        """)
        conn.commit()


def serialize_embedding(emb: np.ndarray) -> bytes:
    """Serializes a NumPy embedding array into binary blob."""
    buf = io.BytesIO()
    np.save(buf, emb.astype(np.float32))
    return buf.getvalue()


def deserialize_embedding(blob: bytes) -> np.ndarray:
    """Deserializes a binary blob into a NumPy embedding array."""
    buf = io.BytesIO(blob)
    return np.load(buf)


def log_audit_event(actor: str, action: str, details: str, db_path: str = DEFAULT_DB_PATH):
    """Records an audit log entry for system traceability."""
    init_db(db_path)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (timestamp, actor_username, action_type, details)
            VALUES (?, ?, ?, ?)
        """, (ts, actor, action, details))
        conn.commit()
