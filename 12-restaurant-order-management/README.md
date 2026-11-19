# Project 12: Restaurant Order Management System

A Python and SQLite order processing application designed for restaurants, cafes, and diners to manage table seating, kitchen order tracking, dynamic item quantities, discounts, billing calculations, and daily sales intelligence.

---

## Features

1. **Menu Management**: Seeded with classic menu items categorized into Appetizers, Mains, Desserts, and Drinks.
2. **Order Lifecycle**: Distinct order numbers (`ORD-XXXXXX`) tracked across `Pending`, `Completed`, and `Cancelled` states.
3. **Dynamic Bill Recalculation**: Automated real-time update of subtotal, configurable percentage discounts, 5% sales tax, and final billing.
4. **Order Item Controls**: Add meals, update serving counts, and safely remove items.
5. **Payment Validation**: Validates tendered amounts against total bill, returns precise change, and locks orders upon payment.
6. **Reporting**: Daily sales metrics showing total receipts, taxes, discounts, and bestselling meals.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK(price > 0),
    is_available INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    table_number TEXT NOT NULL,
    discount_percent REAL NOT NULL DEFAULT 0.0,
    subtotal REAL NOT NULL DEFAULT 0.0,
    discount_amount REAL NOT NULL DEFAULT 0.0,
    tax_amount REAL NOT NULL DEFAULT 0.0,
    total_bill REAL NOT NULL DEFAULT 0.0,
    payment_status TEXT NOT NULL DEFAULT 'Unpaid',
    order_status TEXT NOT NULL DEFAULT 'Pending',
    order_date DATE NOT NULL
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id INTEGER NOT NULL REFERENCES menu_items(id),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    item_total REAL NOT NULL CHECK(item_total > 0),
    UNIQUE(order_id, menu_item_id)
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
python3 -m unittest test_orders.py
```
