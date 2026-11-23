"""
Database module for Employee Attrition & Workforce Retention Analytics.
Stores employee risk profiles, attrition probabilities, and HR action plans in SQLite.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


DEFAULT_DB_PATH = "workforce_records.db"


def init_db(db_path: str = DEFAULT_DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attrition_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                department TEXT NOT NULL,
                tenure_years INTEGER NOT NULL,
                monthly_hours INTEGER NOT NULL,
                satisfaction_score REAL NOT NULL,
                last_evaluation REAL NOT NULL,
                promotion_last_5years INTEGER NOT NULL,
                salary_level TEXT NOT NULL,
                overtime TEXT NOT NULL,
                attrition_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                hr_recommendations TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_assessment(
    employee_id: str,
    department: str,
    tenure_years: int,
    monthly_hours: int,
    satisfaction_score: float,
    last_evaluation: float,
    promotion: int,
    salary_level: str,
    overtime: str,
    probability: float,
    risk_level: str,
    recommendations: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attrition_assessments (
                employee_id, department, tenure_years, monthly_hours,
                satisfaction_score, last_evaluation, promotion_last_5years,
                salary_level, overtime, attrition_probability, risk_level,
                hr_recommendations, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id, department, tenure_years, monthly_hours,
            satisfaction_score, last_evaluation, promotion,
            salary_level, overtime, probability, risk_level,
            recommendations, now
        ))
        conn.commit()
        return cursor.lastrowid


def get_all_assessments(db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> List[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attrition_assessments ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_attrition_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, int]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT risk_level, COUNT(*) FROM attrition_assessments GROUP BY risk_level")
        counts = {"Low Risk": 0, "Medium Risk": 0, "High Risk": 0}
        for level, count in cursor.fetchall():
            counts[level] = count
        return counts
