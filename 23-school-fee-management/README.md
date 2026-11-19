# Project 23: School Fee Payment Management System

A Python and SQLite academic bursary and student accounts platform designed for primary and secondary schools to manage fee schedules, process recurring payment installments, generate receipts, and track arrears.

---

## Features

1. **Class Fee Architecture**: Configure tuition and term levies across different academic levels and sessions.
2. **Student Accounts**: Maintain student rosters linked with parent/guardian contact credentials.
3. **Installment Payment Processing**: Supports fractional and multi-stage payment installments across terms (`Term 1`, `Term 2`, `Term 3`).
4. **Negative Payment Lockout**: Strictly enforces positive financial transactions (`amount > 0`).
5. **Real-time Arrears Reconciliation**: Dynamically updates outstanding dues and categorizes accounts as `Paid`, `Partial`, or `Unpaid`.
6. **Defaulter Auditing**: Quick identification of students with outstanding school fee balances.
7. **Class & Institutional Reporting**: Macro financial summaries covering expected revenues, gross collections, outstanding debt, and collection efficiency percentages.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    academic_session TEXT NOT NULL,
    term_fee REAL NOT NULL CHECK(term_fee > 0)
);

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_reg_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    class_id INTEGER NOT NULL REFERENCES classes(id),
    parent_name TEXT NOT NULL,
    parent_phone TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_reference TEXT UNIQUE NOT NULL,
    student_id INTEGER NOT NULL REFERENCES students(id),
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date DATE NOT NULL,
    payment_method TEXT NOT NULL,
    academic_term TEXT NOT NULL,
    notes TEXT
);
```

---

## Quickstart

### Launch CLI
```bash
python3 main.py
```

### Run Tests
```bash
python3 -m unittest test_fees.py
```
