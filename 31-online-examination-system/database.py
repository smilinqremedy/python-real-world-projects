"""
Database initialization and schema definition for Online Examination Management System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "examination.db")


def get_connection(db_path=None):
    """Establish connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Initialize database tables with constraints and indexes."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('student', 'teacher', 'admin')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            teacher_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_code TEXT UNIQUE NOT NULL,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE RESTRICT NOT NULL,
            title TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL CHECK(duration_minutes > 0),
            passing_score REAL NOT NULL DEFAULT 50.0 CHECK(passing_score >= 0 AND passing_score <= 100),
            start_window TEXT,
            end_window TEXT,
            is_published INTEGER DEFAULT 0 CHECK(is_published IN (0, 1)),
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE NOT NULL,
            question_number INTEGER NOT NULL CHECK(question_number > 0),
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
            points REAL NOT NULL DEFAULT 1.0 CHECK(points > 0),
            UNIQUE(exam_id, question_number)
        );

        CREATE TABLE IF NOT EXISTS exam_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE NOT NULL,
            student_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'assigned' CHECK(status IN ('assigned', 'in_progress', 'completed')),
            retake_authorized INTEGER DEFAULT 0 CHECK(retake_authorized IN (0, 1)),
            UNIQUE(exam_id, student_id)
        );

        CREATE TABLE IF NOT EXISTS exam_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER REFERENCES exam_assignments(id) ON DELETE CASCADE NOT NULL,
            exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE NOT NULL,
            student_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
            started_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            submitted_at TEXT,
            status TEXT NOT NULL DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'submitted', 'auto_submitted')),
            score REAL DEFAULT 0.0,
            total_points REAL DEFAULT 0.0,
            percentage REAL DEFAULT 0.0,
            passed INTEGER DEFAULT 0 CHECK(passed IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS student_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES exam_sessions(id) ON DELETE CASCADE NOT NULL,
            question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE NOT NULL,
            selected_option TEXT CHECK(selected_option IN ('A', 'B', 'C', 'D')),
            is_correct INTEGER DEFAULT 0 CHECK(is_correct IN (0, 1)),
            points_awarded REAL DEFAULT 0.0,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, question_id)
        );

        CREATE INDEX IF NOT EXISTS idx_assignments_student ON exam_assignments(student_id);
        CREATE INDEX IF NOT EXISTS idx_assignments_exam ON exam_assignments(exam_id);
        CREATE INDEX IF NOT EXISTS idx_questions_exam ON questions(exam_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_exam ON exam_sessions(exam_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_student ON exam_sessions(student_id);
        """)
    conn.close()
