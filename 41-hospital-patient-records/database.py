"""
Database initialization and schema definition for Hospital Patient Records Management System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "hospital_records.db")


def get_connection(db_path=None):
    """Establish SQLite connection with foreign keys enabled and row factory set."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Initialize database tables with strict constraints, foreign keys, and indexes."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        -- Users & RBAC System
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('admin', 'doctor', 'nurse', 'receptionist', 'billing')) NOT NULL,
            department TEXT,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Patients Demographic Records
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT CHECK(gender IN ('M', 'F', 'Other')) NOT NULL,
            blood_group TEXT CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'Unknown')) DEFAULT 'Unknown',
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            emergency_name TEXT,
            emergency_phone TEXT,
            allergies TEXT DEFAULT 'None reported',
            chronic_conditions TEXT DEFAULT 'None reported',
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Patient Appointments
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_ref TEXT UNIQUE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
            doctor_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            department TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT CHECK(status IN ('Scheduled', 'In-Progress', 'Completed', 'Cancelled', 'No-Show')) DEFAULT 'Scheduled',
            notes TEXT,
            scheduled_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Hospital Visits / Clinical Encounters
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_ref TEXT UNIQUE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
            appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
            visit_date TEXT NOT NULL,
            visit_type TEXT CHECK(visit_type IN ('Outpatient', 'Inpatient', 'Emergency', 'Follow-up')) NOT NULL,
            attending_staff_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            chief_complaint TEXT NOT NULL,
            status TEXT CHECK(status IN ('Active', 'Discharged', 'Transferred')) DEFAULT 'Active',
            discharge_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Vital Signs Records
        CREATE TABLE IF NOT EXISTS vital_signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER REFERENCES visits(id) ON DELETE CASCADE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
            recorded_by INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            systolic_bp INTEGER CHECK(systolic_bp >= 50 AND systolic_bp <= 300),
            diastolic_bp INTEGER CHECK(diastolic_bp >= 30 AND diastolic_bp <= 200),
            heart_rate INTEGER CHECK(heart_rate >= 30 AND heart_rate <= 250),
            temperature_c REAL CHECK(temperature_c >= 30.0 AND temperature_c <= 45.0),
            respiratory_rate INTEGER CHECK(respiratory_rate >= 6 AND respiratory_rate <= 60),
            spo2_percent REAL CHECK(spo2_percent >= 50.0 AND spo2_percent <= 100.0),
            weight_kg REAL CHECK(weight_kg >= 1.0 AND weight_kg <= 500.0),
            height_cm REAL CHECK(height_cm >= 30.0 AND height_cm <= 260.0),
            bmi REAL,
            notes TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Authorized Clinical Notes (No automated diagnosis or prescription)
        CREATE TABLE IF NOT EXISTS clinical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER REFERENCES visits(id) ON DELETE CASCADE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
            author_id INTEGER REFERENCES users(id) ON DELETE RESTRICT NOT NULL,
            note_type TEXT CHECK(note_type IN ('Consultation', 'Progress Note', 'Nursing Note', 'Discharge Summary')) NOT NULL,
            subjective_observations TEXT NOT NULL,
            objective_observations TEXT NOT NULL,
            clinical_assessment TEXT NOT NULL,
            care_plan TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Billing & Invoicing Records
        CREATE TABLE IF NOT EXISTS billing_invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_ref TEXT UNIQUE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE NOT NULL,
            visit_id INTEGER REFERENCES visits(id) ON DELETE SET NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount >= 0),
            amount_paid REAL DEFAULT 0.0 CHECK(amount_paid >= 0),
            status TEXT CHECK(status IN ('Pending', 'Partial', 'Paid', 'Cancelled')) DEFAULT 'Pending',
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            paid_at TIMESTAMP
        );

        -- Security & Privacy Audit Trail (Sanitized details only)
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Performance and query indexes
        CREATE INDEX IF NOT EXISTS idx_patients_pid ON patients(patient_id);
        CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
        CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
        CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
        CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, doctor_id);
        CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id);
        CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vital_signs(patient_id);
        CREATE INDEX IF NOT EXISTS idx_clinical_notes_patient ON clinical_notes(patient_id);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
        """)
    conn.close()
