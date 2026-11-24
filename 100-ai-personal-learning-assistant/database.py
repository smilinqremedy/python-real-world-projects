"""
Database Persistence Module for AI Personal Learning Assistant.
Maintains users, subjects, learning topics, generated quiz questions,
attempt histories, and personalized revision schedules in SQLite.
"""
import sqlite3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learning_assistant.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH):
    """Initializes schema for learning management, quiz generation, and performance tracking."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # Subjects table (e.g. Computer Science, Neuroscience)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, title)
            );
        """)

        # Learning Topics under subjects
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content_text TEXT NOT NULL,
                summary TEXT,
                source_filename TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (subject_id) REFERENCES subjects (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)

        # Grounded Quiz Questions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL, -- 'mcq' or 'short_answer'
                options_json TEXT, -- JSON array of choices for MCQ
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                source_excerpt TEXT,
                FOREIGN KEY (topic_id) REFERENCES topics (id)
            );
        """)

        # Quiz Attempt History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                score_pct REAL NOT NULL,
                total_questions INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                completed_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (topic_id) REFERENCES topics (id)
            );
        """)

        # Personalized Revision Recommendations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS revision_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                priority TEXT NOT NULL, -- 'HIGH', 'MEDIUM', 'MAINTAIN'
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (topic_id) REFERENCES topics (id)
            );
        """)

        conn.commit()
