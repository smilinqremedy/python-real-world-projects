"""
Database and Audit Trail for Financial Fraud Investigations.
Stores transactions, risk assessments, and human-in-the-loop analyst decisions.
"""
import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fraud_investigations.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                transaction_id TEXT UNIQUE NOT NULL,
                amount REAL NOT NULL,
                supervised_prob REAL NOT NULL,
                anomaly_score REAL NOT NULL,
                risk_score REAL NOT NULL,
                risk_tier TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'flagged', -- 'flagged', 'cleared', 'confirmed_fraud'
                analyst_disposition TEXT,
                analyst_notes TEXT
            );
        """)
        conn.commit()


def log_transaction_risk(
    transaction_id: str,
    amount: float,
    supervised_prob: float,
    anomaly_score: float,
    risk_score: float,
    risk_tier: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO transaction_audits (
                timestamp, transaction_id, amount, supervised_prob, anomaly_score,
                risk_score, risk_tier, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ts, transaction_id, amount, supervised_prob, anomaly_score, risk_score, risk_tier,
              "flagged" if risk_tier == "HIGH" else "auto_cleared"))
        conn.commit()
        return cursor.lastrowid


def update_analyst_disposition(
    transaction_id: str,
    disposition: str,
    notes: str,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE transaction_audits
            SET status = ?, analyst_disposition = ?, analyst_notes = ?
            WHERE transaction_id = ?
        """, (disposition, disposition, notes, transaction_id))
        conn.commit()
        return cursor.rowcount > 0


def get_transactions_by_status(status: Optional[str] = None, limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM transaction_audits WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM transaction_audits ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cursor.fetchall()]
