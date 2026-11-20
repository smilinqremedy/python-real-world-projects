"""
Database schema and initialization for Hospital Pharmacy Prescription Management System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pharmacy.db")


def get_connection(db_path=None):
    """Establish SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Initialize relational database tables for hospital pharmacy operations."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            gender TEXT CHECK(gender IN ('M', 'F', 'Other')) NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            allergies TEXT DEFAULT 'None reported',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            license_number TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dosage_form TEXT NOT NULL, -- e.g. Tablet, Syrup, Injection, Capsule
            strength TEXT NOT NULL,    -- e.g. 500mg, 10ml, 250mg/5ml
            stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
            reorder_level INTEGER DEFAULT 10 CHECK(reorder_level >= 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            manufacturer TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_ref TEXT UNIQUE NOT NULL,
            patient_id INTEGER REFERENCES patients(id) ON DELETE RESTRICT NOT NULL,
            doctor_id INTEGER REFERENCES doctors(id) ON DELETE RESTRICT NOT NULL,
            diagnosis TEXT NOT NULL,
            status TEXT CHECK(status IN ('Pending', 'Dispensed', 'Cancelled')) DEFAULT 'Pending',
            prescribed_date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prescription_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER REFERENCES prescriptions(id) ON DELETE CASCADE NOT NULL,
            medicine_id INTEGER REFERENCES medicines(id) ON DELETE RESTRICT NOT NULL,
            quantity_prescribed INTEGER NOT NULL CHECK(quantity_prescribed > 0),
            dosage_instructions TEXT NOT NULL, -- e.g. "1 tablet twice daily"
            duration_days INTEGER NOT NULL CHECK(duration_days > 0),
            status TEXT CHECK(status IN ('Pending', 'Dispensed', 'Unavailable')) DEFAULT 'Pending'
        );

        CREATE TABLE IF NOT EXISTS dispense_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispense_ref TEXT UNIQUE NOT NULL,
            prescription_id INTEGER REFERENCES prescriptions(id) ON DELETE RESTRICT NOT NULL,
            pharmacist_name TEXT NOT NULL,
            dispensed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS dispense_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispense_id INTEGER REFERENCES dispense_records(id) ON DELETE CASCADE NOT NULL,
            medicine_id INTEGER REFERENCES medicines(id) ON DELETE RESTRICT NOT NULL,
            quantity_dispensed INTEGER NOT NULL CHECK(quantity_dispensed > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            subtotal REAL NOT NULL CHECK(subtotal >= 0)
        );

        CREATE INDEX IF NOT EXISTS idx_patients_pid ON patients(patient_id);
        CREATE INDEX IF NOT EXISTS idx_doctors_did ON doctors(doctor_id);
        CREATE INDEX IF NOT EXISTS idx_meds_mid ON medicines(medicine_id);
        CREATE INDEX IF NOT EXISTS idx_rx_patient ON prescriptions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_rx_status ON prescriptions(status);
        CREATE INDEX IF NOT EXISTS idx_dispense_date ON dispense_records(dispensed_at);
        """)
    conn.close()
