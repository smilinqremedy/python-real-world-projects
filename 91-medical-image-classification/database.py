"""
SQLite Database module for recording inference audits and prediction history.
Ensures traceability of automated medical image screening events.
"""
import sqlite3
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medical_history.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initializes schema for prediction logs and model training run history."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                image_name TEXT NOT NULL,
                image_sha256 TEXT NOT NULL,
                predicted_class TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                normal_probability REAL NOT NULL,
                pneumonia_probability REAL NOT NULL,
                disclaimer_acknowledged INTEGER NOT NULL DEFAULT 1,
                user_notes TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                dataset_size INTEGER NOT NULL,
                train_accuracy REAL NOT NULL,
                val_accuracy REAL NOT NULL,
                val_f1_score REAL NOT NULL,
                weights_path TEXT NOT NULL
            );
        """)
        conn.commit()


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA256 cryptographic checksum of an image file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def log_prediction(
    image_name: str,
    file_path: str,
    predicted_class: str,
    confidence_score: float,
    normal_prob: float,
    pneumonia_prob: float,
    db_path: str = DEFAULT_DB_PATH,
    user_notes: str = ""
) -> int:
    """Logs a single inference event to the audit trail."""
    init_db(db_path)
    sha256 = compute_file_sha256(file_path) if os.path.exists(file_path) else "NA"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prediction_history (
                timestamp, image_name, image_sha256, predicted_class,
                confidence_score, normal_probability, pneumonia_probability,
                disclaimer_acknowledged, user_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (ts, image_name, sha256, predicted_class, confidence_score, normal_prob, pneumonia_prob, user_notes))
        conn.commit()
        return cursor.lastrowid


def get_prediction_history(limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves recent prediction logs."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM prediction_history ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
