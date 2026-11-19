# Project 25: Logistics and Shipment Tracking System

A Python and SQLite freight courier and package tracking management system engineered for logistics companies, parcel couriers, and distribution networks to manage senders, receivers, tiered freight fees, dispatch couriers, and milestone audit trails.

---

## Features

1. **Client & Fleet Directory**: Maintain sender contact profiles and couriers linked to transportation vehicles (Motorcycles, Vans, Heavy Trucks).
2. **Waybill & Consignment Generation**: Unique tracking serials (`TRK-XXXXXXXX`) capturing origin, destination, parcel description, and cargo weight.
3. **Multi-Tier Freight Calculator**: Dynamic shipping tier pricing:
   - **Standard**: $5.00 base + $2.00/kg
   - **Express**: $10.00 base + $3.50/kg
   - **Overnight**: $20.00 base + $5.00/kg
4. **Dispatcher Assignment**: Routes shipments to designated active couriers.
5. **Milestone Progression & Audit Trail**: Chronological event logs recording checkpoints across `Created` $\rightarrow$ `Assigned` $\rightarrow$ `In Transit` $\rightarrow$ `Out for Delivery` $\rightarrow$ `Delivered`.
6. **Delivery Lockout Rule**: Strictly prohibits marking shipments as `Out for Delivery` or `Delivered` without a courier assignment.
7. **Logistics Analytics**: Freight volume (kg), gross billings, collection revenue, and courier delivery efficiency.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    address TEXT NOT NULL
);

CREATE TABLE couriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    courier_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_number TEXT UNIQUE NOT NULL,
    sender_id INTEGER NOT NULL REFERENCES customers(id),
    receiver_name TEXT NOT NULL,
    receiver_phone TEXT NOT NULL,
    receiver_address TEXT NOT NULL,
    destination_city TEXT NOT NULL,
    parcel_description TEXT NOT NULL,
    weight_kg REAL NOT NULL CHECK(weight_kg > 0),
    shipping_tier TEXT NOT NULL DEFAULT 'Standard' CHECK(shipping_tier IN ('Standard', 'Express', 'Overnight')),
    delivery_fee REAL NOT NULL CHECK(delivery_fee > 0),
    courier_id INTEGER REFERENCES couriers(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'Created' CHECK(status IN ('Created', 'Assigned', 'In Transit', 'Out for Delivery', 'Delivered', 'Cancelled')),
    payment_status TEXT NOT NULL DEFAULT 'Unpaid' CHECK(payment_status IN ('Unpaid', 'Paid')),
    created_date DATE NOT NULL,
    delivered_at TIMESTAMP
);

CREATE TABLE tracking_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shipment_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    location TEXT NOT NULL,
    status_update TEXT NOT NULL,
    remarks TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
python3 -m unittest test_logistics.py
```
