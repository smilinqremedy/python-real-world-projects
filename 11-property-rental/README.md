# Project 11: Property Rental Management System

A Python and SQLite management solution designed for landlords and property management agencies to streamline properties, tenants, monthly rental billing, and debt tracking.

---

## Features

1. **Property Registration**: Manage units with unique codes, locations, and monthly rental rates.
2. **Tenant Allocation**: Enforce 1-to-1 tenant property lease assignments with status auto-updates.
3. **Rent Collection**: Record payments against specific billing periods with auto-generated references (`PAY-XXXXXX`).
4. **Delinquency & Balance Tracking**: Calculate cumulative rent liabilities vs. total payments from lease commencement.
5. **Occupancy Status**: Filter vacant vs. occupied units.
6. **Tenant Search**: Search across tenant names, codes, or property addresses.
7. **Monthly Collection Reports**: Real-time expected vs. collected rent analytics and collection efficiency percentages.

---

## Database Architecture (SQLite)

```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    monthly_rent REAL NOT NULL CHECK(monthly_rent > 0),
    status TEXT NOT NULL DEFAULT 'Vacant' CHECK(status IN ('Vacant', 'Occupied'))
);

CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    property_id INTEGER UNIQUE REFERENCES properties(id) ON DELETE SET NULL,
    lease_start_date DATE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE rent_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_ref TEXT UNIQUE NOT NULL,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    property_id INTEGER NOT NULL REFERENCES properties(id),
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date DATE NOT NULL,
    period_month TEXT NOT NULL,
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
python3 -m unittest test_rental.py
```
