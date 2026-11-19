# Project 20: Donation and Charity Management System

A Python and SQLite treasury and donor contribution management system engineered for non-profit foundations, charities, and philanthropic campaigns to manage donor databases, track pledge campaigns, authorize project fund distributions, and guarantee strict non-negative campaign treasury balances.

---

## Features

1. **Donor Directory**: Register donors categorized as Individual, Corporate, or Foundation.
2. **Campaign Goal Management**: Configure targeted fundraising campaigns with milestones and time windows.
3. **Donation Processing**: Logs contributions across multiple payment methods, generating verifiable receipts (`DON-XXXXXX`).
4. **Campaign Balance Accounting**: Computes real-time fundraising progress and active balances.
5. **Overdraft Lockout**: Prevents fund distributions that exceed the current liquid cash balance of a campaign.
6. **Financial Treasury Reporting**: Transparent accountability tracking net treasury positions, distribution vouchers (`DIS-XXXXXX`), and top donor rankings.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    donor_type TEXT NOT NULL DEFAULT 'Individual' CHECK(donor_type IN ('Individual', 'Corporate', 'Foundation'))
);

CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    target_amount REAL NOT NULL CHECK(target_amount > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Closed', 'Paused'))
);

CREATE TABLE donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_reference TEXT UNIQUE NOT NULL,
    donor_id INTEGER NOT NULL REFERENCES donors(id),
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    amount REAL NOT NULL CHECK(amount > 0),
    donation_date DATE NOT NULL,
    payment_method TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE disbursements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disbursement_reference TEXT UNIQUE NOT NULL,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    purpose TEXT NOT NULL,
    recipient TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    disbursement_date DATE NOT NULL,
    approval_notes TEXT
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
python3 -m unittest test_charity.py
```
