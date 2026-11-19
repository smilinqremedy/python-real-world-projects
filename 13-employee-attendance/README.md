# Project 13: Employee Attendance Management System

A Python and SQLite workforce tracking system designed for small to medium enterprises to monitor daily employee clock-ins, detect tardiness relative to scheduled shifts, record absences, and generate attendance rate reports.

---

## Features

1. **Employee Registry**: Record staff members with custom shift start times (e.g. `08:30`, `09:00`).
2. **Clock-In / Clock-Out**: Captures precise timestamps using Python's `datetime` module.
3. **Automated Lateness Detection**: Compares check-in time against employee's scheduled shift and calculates minutes late.
4. **Absence Management**: Explicitly record authorized or unauthorized absences with explanatory notes.
5. **Duplicate Prevention**: Strictly prevents multiple attendance entries for the same staff member on the same calendar day.
6. **Analytics & Reporting**: Generates weekly and monthly attendance percentage metrics across departments and individual workers.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    position TEXT NOT NULL,
    shift_start_time TEXT NOT NULL DEFAULT '09:00',
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in_time TEXT,
    check_out_time TEXT,
    is_late INTEGER NOT NULL DEFAULT 0,
    minutes_late INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Present' CHECK(status IN ('Present', 'Half-Day', 'Absent')),
    notes TEXT,
    UNIQUE(employee_id, attendance_date)
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
python3 -m unittest test_attendance.py
```
