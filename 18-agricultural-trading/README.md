# Project 18: Agricultural Produce Trading System

A Python and SQLite commodities trading and inventory management platform designed for farmer cooperatives, grain aggregators, food wholesalers, and agricultural brokers to record crop inventory, track bulk trade transactions, enforce stock limits, and monitor revenue flows.

---

## Features

1. **Agribusiness Registry**: Catalog farm suppliers and produce buyers with contact details.
2. **Crop & Commodity Cataloging**: Supports grains, tubers, vegetables, legumes, and fruits with dynamic pricing per unit (kg, bag, crate, ton).
3. **Inventory Restocking**: Real-time batch stock replenishment.
4. **Order Execution with Stock Protection**: Enforces atomic stock depletion; strictly denies purchase requests exceeding verified on-hand quantities.
5. **Invoice Generation**: Formats transaction records with unique serial identifiers (`AGR-XXXXXX`).
6. **Market Intelligence**: Sales volume analytics grouped by crop type, supplier, and purchasing customer.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    phone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE buyers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    company TEXT,
    phone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE produce (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produce_code TEXT UNIQUE NOT NULL,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    available_quantity REAL NOT NULL CHECK(available_quantity >= 0),
    price_per_unit REAL NOT NULL CHECK(price_per_unit > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT UNIQUE NOT NULL,
    buyer_id INTEGER NOT NULL REFERENCES buyers(id),
    produce_id INTEGER NOT NULL REFERENCES produce(id),
    quantity REAL NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    total_price REAL NOT NULL CHECK(total_price > 0),
    sale_date DATE NOT NULL,
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
python3 -m unittest test_trading.py
```
