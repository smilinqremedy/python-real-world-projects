"""
Database module for Road Accident Severity Analysis.
Stores accident records, predicted severity classes, and risk evaluation logs in SQLite.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


DEFAULT_DB_PATH = "accident_records.db"


def init_db(db_path: str = DEFAULT_DB_PATH):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accident_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_ref TEXT NOT NULL,
                weather_condition TEXT NOT NULL,
                road_surface TEXT NOT NULL,
                light_condition TEXT NOT NULL,
                speed_limit INTEGER NOT NULL,
                vehicle_type TEXT NOT NULL,
                predicted_severity TEXT NOT NULL,
                fatal_prob REAL NOT NULL,
                serious_prob REAL NOT NULL,
                slight_prob REAL NOT NULL,
                safety_recommendations TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_prediction(
    incident_ref: str,
    weather: str,
    road_surface: str,
    light: str,
    speed_limit: int,
    vehicle_type: str,
    predicted_severity: str,
    fatal_prob: float,
    serious_prob: float,
    slight_prob: float,
    safety_recommendations: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accident_predictions (
                incident_ref, weather_condition, road_surface, light_condition,
                speed_limit, vehicle_type, predicted_severity, fatal_prob,
                serious_prob, slight_prob, safety_recommendations, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_ref, weather, road_surface, light, speed_limit, vehicle_type,
            predicted_severity, fatal_prob, serious_prob, slight_prob,
            safety_recommendations, now
        ))
        conn.commit()
        return cursor.lastrowid


def get_all_records(db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> List[Dict[str, Any]]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accident_predictions ORDER BY id DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def get_severity_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, int]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT predicted_severity, COUNT(*) FROM accident_predictions GROUP BY predicted_severity")
        counts = {"Slight": 0, "Serious": 0, "Fatal": 0}
        for sev, count in cursor.fetchall():
            counts[sev] = count
        return counts
