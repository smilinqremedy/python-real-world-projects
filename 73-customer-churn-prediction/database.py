"""
Database Management for Customer Churn Analytics.
Stores historical churn predictions and risk assessments in SQLite.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


DEFAULT_DB_PATH = "churn_records.db"


def init_db(db_path: str = DEFAULT_DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS churn_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id TEXT NOT NULL,
                tenure_months INTEGER NOT NULL,
                contract_type TEXT NOT NULL,
                monthly_charges REAL NOT NULL,
                support_tickets INTEGER NOT NULL,
                payment_delay_days INTEGER NOT NULL,
                churn_probability REAL NOT NULL,
                risk_tier TEXT NOT NULL,
                retention_strategy TEXT NOT NULL,
                predicted_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_prediction(
    customer_id: str,
    tenure_months: int,
    contract_type: str,
    monthly_charges: float,
    support_tickets: int,
    payment_delay_days: int,
    churn_probability: float,
    risk_tier: str,
    retention_strategy: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO churn_predictions (
                customer_id, tenure_months, contract_type, monthly_charges,
                support_tickets, payment_delay_days, churn_probability,
                risk_tier, retention_strategy, predicted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id, tenure_months, contract_type, monthly_charges,
            support_tickets, payment_delay_days, churn_probability,
            risk_tier, retention_strategy, now
        ))
        conn.commit()
        return cursor.lastrowid


def get_all_predictions(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM churn_predictions ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]


def get_risk_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, int]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT risk_tier, COUNT(*) FROM churn_predictions GROUP BY risk_tier")
        counts = {"Low": 0, "Moderate": 0, "High": 0}
        for tier, count in cursor.fetchall():
            counts[tier] = count
        return counts
