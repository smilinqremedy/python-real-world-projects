# Project 24: Internet Cafe Management System

A Python and SQLite terminal workstation and billing governance system engineered for cybercafes, gaming lounges, and public telecenters to monitor workstation availability, manage customer session timers, handle overnight sessions crossing midnight, and track cash receipts.

---

## Features

1. **Hardware & Terminal Registry**: Manage individual PC terminals with static IP addresses, hardware specifications, and hourly tariff rates.
2. **Session Concurrency Prevention**: Strictly prevents a terminal from being allocated to more than one active session concurrently.
3. **High-Precision Duration Tracking**: Uses Python's `datetime` module to calculate session durations down to the minute, seamlessly resolving sessions spanning across midnight.
4. **Pro-Rata Tariff Engine**: Converts elapsed session minutes into proportional billing amounts with configurable minimum charges.
5. **Cashier Point of Sale**: Validates cash tendered, checks against unpaid balances, computes change, and automatically unlocks terminals for subsequent clients.
6. **Utilization & Revenue Reporting**: Aggregates terminal utilization metrics, total operational hours, and gross revenue collections.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE computers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    computer_code TEXT UNIQUE NOT NULL,
    ip_address TEXT NOT NULL,
    specs TEXT NOT NULL,
    hourly_rate REAL NOT NULL CHECK(hourly_rate > 0),
    status TEXT NOT NULL DEFAULT 'Available' CHECK(status IN ('Available', 'In Use', 'Maintenance'))
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    computer_id INTEGER NOT NULL REFERENCES computers(id),
    customer_name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER DEFAULT 0,
    hourly_rate_applied REAL NOT NULL,
    total_bill REAL NOT NULL DEFAULT 0.0 CHECK(total_bill >= 0),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
    amount_paid REAL NOT NULL DEFAULT 0.0 CHECK(amount_paid >= 0),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Cancelled'))
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
python3 -m unittest test_cafe.py
```
