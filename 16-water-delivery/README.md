# Project 16: Water Delivery Management System

A Python and SQLite logistics and container distribution application tailored for commercial water bottling and refilling businesses to coordinate customer drop-offs, assign drivers, dispatch vehicles, and track daily sales revenue.

---

## Features

1. **Customer & Address Management**: Maintain primary client directories and delivery addresses.
2. **Container Tier Pricing**: Configurable rates for 20L Jugs ($4.50), 10L Dispensers ($3.00), and 5L Bottle Packs ($6.00).
3. **Automated Freight Calculation**: Standard $3.00 delivery fee waived for orders of 10 containers or more.
4. **Fleet & Driver Assignment**: Pair orders with registered couriers and transport vehicles.
5. **State Progression**: Enforce lifecycle states (`Pending` $\rightarrow$ `Assigned` $\rightarrow$ `Out For Delivery` $\rightarrow$ `Delivered`); rejects marking deliveries complete without an assigned courier.
6. **Payment & Reconciliation**: Cash/Card payment tracking and daily sales aggregation.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    default_address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    vehicle_plate TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
    delivery_address TEXT NOT NULL,
    container_type TEXT NOT NULL DEFAULT '20L Jug',
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    container_unit_price REAL NOT NULL CHECK(container_unit_price > 0),
    delivery_fee REAL NOT NULL DEFAULT 0.0,
    total_charge REAL NOT NULL CHECK(total_charge > 0),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
    payment_method TEXT,
    status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Assigned', 'Out For Delivery', 'Delivered', 'Cancelled')),
    order_date DATE NOT NULL,
    delivered_at TIMESTAMP
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
python3 -m unittest test_delivery.py
```
