# Project 19: Technical Repair Service Management System

A Python and SQLite electronics service workshop and RMA ticketing platform designed for phone and computer repair businesses to manage customer device intake, technician dispatches, labor/parts accounting, and customer handoffs.

---

## Features

1. **Intake & Repair Ticketing**: Generates unique service tracking IDs (`REP-XXXXXX`) documenting device make, model, serial, and reported symptoms.
2. **Technician Allocation**: Routes repairs to specialists based on device category.
3. **Itemized Billing**: Independent auditing of replacement component costs and technician labor.
4. **Lifecycle State Machine**: Strict step progression (`Received` $\rightarrow$ `Diagnosing` $\rightarrow$ `Repairing` $\rightarrow$ `Completed` $\rightarrow$ `Collected`).
5. **Collection Lockout Rule**: Strictly prevents device handover until two independent prerequisites are fulfilled:
   - Status must be marked as `Completed`.
   - Invoiced charges must be verified as `Paid` in full.
6. **Business Analytics**: Aggregates workshop throughput, technician efficiency, parts revenue, and outstanding client debts.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT
);

CREATE TABLE technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tech_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    phone TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE repairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    technician_id INTEGER REFERENCES technicians(id) ON DELETE SET NULL,
    device_type TEXT NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    serial_number TEXT,
    problem_description TEXT NOT NULL,
    parts_cost REAL NOT NULL DEFAULT 0.0 CHECK(parts_cost >= 0),
    labor_cost REAL NOT NULL DEFAULT 0.0 CHECK(labor_cost >= 0),
    total_cost REAL NOT NULL DEFAULT 0.0 CHECK(total_cost >= 0),
    amount_paid REAL NOT NULL DEFAULT 0.0 CHECK(amount_paid >= 0),
    is_paid INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Received' CHECK(status IN ('Received', 'Diagnosing', 'Repairing', 'Completed', 'Collected')),
    received_date DATE NOT NULL,
    completed_date DATE,
    collected_date DATE,
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
python3 -m unittest test_repair.py
```
