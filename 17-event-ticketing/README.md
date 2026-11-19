# Project 17: Event Registration and Ticketing System

A Python and SQLite registration and admission management system designed for event managers, conference planners, and seminar hosts to manage ticketing, seat capacity limits, guest entry validation, and revenue reconciliation.

---

## Features

1. **Event Scheduling**: Configure events with fixed venue capacities, locations, and pricing tiers.
2. **Attendee Registration**: Issues cryptographically unique ticket vouchers (`TCK-XXXXXX`).
3. **Capacity Protection**: Rejects bookings automatically once venue thresholds are reached.
4. **Anti-Duplicate Enforcement**: Restricts attendees from submitting duplicate bookings using matching credentials.
5. **Admission Gatekeeping**: Verifies admission at entry gates, enforces prerequisite payment verification, and locks against double check-ins.
6. **Analytics & Turnout Reporting**: Aggregates occupancy ratios, gross ticket receipts, and real-time attendance turnout rates.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    event_date DATE NOT NULL,
    location TEXT NOT NULL,
    ticket_price REAL NOT NULL CHECK(ticket_price >= 0),
    max_capacity INTEGER NOT NULL CHECK(max_capacity > 0)
);

CREATE TABLE attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    attendee_id INTEGER NOT NULL REFERENCES attendees(id),
    purchase_date DATE NOT NULL,
    price_paid REAL NOT NULL CHECK(price_paid >= 0),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
    is_checked_in INTEGER NOT NULL DEFAULT 0,
    check_in_time TIMESTAMP,
    UNIQUE(event_id, attendee_id)
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
python3 -m unittest test_ticketing.py
```
