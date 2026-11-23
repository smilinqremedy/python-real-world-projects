"""
Database storage for Email Spam Classification.
Logs scanned emails and classifications in SQLite.
"""
import sqlite3
from typing import List, Dict, Any
from datetime import datetime, timezone


DEFAULT_DB_PATH = "spam_scans.db"


def init_db(db_path: str = DEFAULT_DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                body_snippet TEXT NOT NULL,
                is_spam INTEGER NOT NULL,
                spam_probability REAL NOT NULL,
                flagged_keywords TEXT,
                scanned_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_scan(
    subject: str,
    body: str,
    is_spam: bool,
    spam_probability: float,
    flagged_keywords: List[str],
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)
    snippet = body[:200]
    kw_str = ", ".join(flagged_keywords) if flagged_keywords else "None"
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scanned_emails (
                subject, body_snippet, is_spam, spam_probability,
                flagged_keywords, scanned_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (subject, snippet, 1 if is_spam else 0, spam_probability, kw_str, now))
        conn.commit()
        return cursor.lastrowid


def get_scan_history(db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> List[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scanned_emails ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_scan_stats(db_path: str = DEFAULT_DB_PATH) -> Dict[str, int]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), SUM(is_spam) FROM scanned_emails")
        total, spam_count = cursor.fetchone()
        spam_count = spam_count or 0
        total = total or 0
        return {
            "total_scanned": total,
            "spam_detected": spam_count,
            "ham_detected": total - spam_count
        }
