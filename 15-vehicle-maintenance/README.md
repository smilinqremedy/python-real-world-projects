# Project 15: Vehicle Maintenance Tracking System

A Python and SQLite fleet management and vehicle servicing tracker engineered for transport logistics businesses, car rental companies, and vehicle owners to schedule inspections, log maintenance expenses, and prevent catastrophic failures through automated overdue scheduling.

---

## Features

1. **Vehicle Fleet Registry**: Catalog vehicles by unique registration/license number, make, model, manufacturing year, and odometer mileage.
2. **Maintenance Ledger**: Track oil changes, tire rotations, brake servicing, and comprehensive inspections with cost itemization.
3. **Upcoming & Overdue Scheduling**: Automatically flags vehicles exceeding target service dates or mileage limits using Python's `datetime` module.
4. **Odometer Progression**: Guarantees mileage monotonicity (odometer cannot decrease).
5. **Vehicle History & Search**: Instant retrieval of full maintenance histories and lifetime repair expenditures per vehicle.
6. **Expense Intelligence**: Comprehensive analytics breaking down total fleet spend across service categories and individual vehicles.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_number TEXT UNIQUE NOT NULL,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL CHECK(year >= 1900),
    current_mileage INTEGER NOT NULL CHECK(current_mileage >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    service_type TEXT NOT NULL,
    service_date DATE NOT NULL,
    mileage_at_service INTEGER NOT NULL CHECK(mileage_at_service >= 0),
    cost REAL NOT NULL CHECK(cost >= 0),
    service_provider TEXT,
    notes TEXT,
    next_due_date DATE,
    next_due_mileage INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
python3 -m unittest test_maintenance.py
```
