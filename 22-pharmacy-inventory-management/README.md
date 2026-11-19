# Project 22: Pharmacy Inventory and Sales Management System

A Python and SQLite pharmaceutical inventory and retail dispensing platform engineered for community pharmacies and clinical dispensaries to manage batch traceability, prevent dispensing of expired medications, audit stock levels against reorder limits, and analyze sales revenue.

---

## Features

1. **Pharmaceutical Registry**: Classify medicines across drug therapeutic categories and dispensing units (Tablets, Capsules, Syrup, Ointment).
2. **Batch Traceability**: Segregate inventory by lot/batch numbers with independent cost prices, retail prices, manufacturing dates, and expiration dates.
3. **Strict Expiry Lockout**: Enforces zero-tolerance safety rules by programmatically blocking the sale of expired medication batches.
4. **Stock Auditing**: Real-time atomic stock decrementing upon dispensing with automatic rejection of overselling.
5. **Proactive Alerts**:
   - **Low-Stock Alerts**: Detects medicines whose aggregate non-expired stock drops below configured thresholds.
   - **Expiration Alerts**: Flags lots expired or expiring within configurable periods (e.g. 30 days).
6. **Sales Intelligence**: Itemized daily and monthly revenue reporting.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level >= 0)
);

CREATE TABLE batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE,
    batch_number TEXT UNIQUE NOT NULL,
    cost_price REAL NOT NULL CHECK(cost_price >= 0),
    selling_price REAL NOT NULL CHECK(selling_price >= cost_price),
    initial_quantity INTEGER NOT NULL CHECK(initial_quantity > 0),
    current_quantity INTEGER NOT NULL CHECK(current_quantity >= 0),
    manufacture_date DATE NOT NULL,
    expiry_date DATE NOT NULL
);

CREATE TABLE sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number TEXT UNIQUE NOT NULL,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    medicine_id INTEGER NOT NULL REFERENCES medicines(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    total_price REAL NOT NULL CHECK(total_price > 0),
    sale_date DATE NOT NULL,
    customer_notes TEXT
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
python3 -m unittest test_pharmacy.py
```
