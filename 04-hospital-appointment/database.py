"""
Database Layer for Hospital Appointment Management System
Manages SQLite database connections, schema migrations, and initial seeds.
"""

import sqlite3
import os
from datetime import datetime

DEFAULT_DB_FILE = "clinic.db"

STANDARD_TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30",
    "11:00", "11:30", "13:00", "13:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30"
]

INITIAL_DOCTORS = [
    ("Dr. Sarah Jenkins", "Cardiology", "+1-555-0101", "s.jenkins@clinic.org"),
    ("Dr. Marcus Vance", "Pediatrics", "+1-555-0102", "m.vance@clinic.org"),
    ("Dr. Elena Rostova", "General Medicine", "+1-555-0103", "e.rostova@clinic.org"),
    ("Dr. David Chen", "Orthopedics", "+1-555-0104", "d.chen@clinic.org"),
    ("Dr. Amara Okafor", "Dermatology", "+1-555-0105", "a.okafor@clinic.org")
]

INITIAL_PATIENTS = [
    ("PAT-2026-001", "John Doe", "1988-04-12", "Male", "+1-555-0201", "johndoe@email.com"),
    ("PAT-2026-002", "Jane Smith", "1994-09-23", "Female", "+1-555-0202", "janesmith@email.com"),
    ("PAT-2026-003", "Robert Taylor", "1975-11-05", "Male", "+1-555-0203", "robertt@email.com")
]


def get_db_connection(db_path=DEFAULT_DB_FILE):
    """
    Creates and returns a SQLite connection with row_factory and foreign keys enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_database(db_path=DEFAULT_DB_FILE):
    """
    Creates database tables, indexes, and populates initial doctor/patient seeds if empty.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Patients Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT,
            created_at TEXT NOT NULL
        );
        """)

        # 2. Doctors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone_number TEXT,
            email TEXT,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 3. Appointments Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            reason TEXT,
            status TEXT NOT NULL CHECK(status IN ('scheduled', 'completed', 'cancelled')) DEFAULT 'scheduled',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT,
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT
        );
        """)

        # 4. Partial Unique Index to prevent overlapping active bookings for the same doctor
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_doctor_slot
        ON appointments(doctor_id, appointment_date, time_slot)
        WHERE status = 'scheduled';
        """)

        # Partial Unique Index to prevent a patient from having two active appointments at the same time
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_patient_slot
        ON appointments(patient_id, appointment_date, time_slot)
        WHERE status = 'scheduled';
        """)

        # Indexes for query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_date ON appointments(appointment_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_patient ON appointments(patient_id);")

        conn.commit()

        # Seed initial doctors if table is empty
        cursor.execute("SELECT COUNT(*) FROM doctors;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
            INSERT INTO doctors (full_name, specialty, phone_number, email)
            VALUES (?, ?, ?, ?);
            """, INITIAL_DOCTORS)
            conn.commit()

        # Seed initial fictional patients if table is empty
        cursor.execute("SELECT COUNT(*) FROM patients;")
        if cursor.fetchone()[0] == 0:
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.executemany("""
            INSERT INTO patients (patient_id, full_name, date_of_birth, gender, phone_number, email, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, [(p[0], p[1], p[2], p[3], p[4], p[5], now_iso) for p in INITIAL_PATIENTS])
            conn.commit()
