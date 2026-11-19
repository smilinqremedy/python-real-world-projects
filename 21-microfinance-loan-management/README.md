# Project 21: Microfinance Loan Management System

A Python and SQLite loan portfolio administration platform designed for microfinance institutions, credit cooperatives, and peer lending organizations to manage borrowers, process credit applications, compute repayment schedules, track balances, and audit debt recovery.

---

## Features

1. **Borrower Registry**: Register borrowers with verified identifiers and baseline monthly incomes.
2. **Loan Applications & Underwriting**: Configurable principal amounts, annual interest rates, and loan terms (months). Rejects applications for nonexistent borrowers.
3. **Approval Lifecycle**: Manages status transitions (`Applied` $\rightarrow$ `Approved` / `Rejected` $\rightarrow$ `Active` $\rightarrow$ `Repaid` / `Defaulted`).
4. **Repayment Schedule Generation**: Generates amortization installments and monthly due dates.
5. **Installment & Excess Payment Accounting**: Supports partial repayments and strictly enforces excess payment auditing by sequestering overpayments into an audited `excess_payments` ledger.
6. **Delinquency Monitoring**: Identifies matured loans with outstanding balances using Python's `datetime` module.
7. **Portfolio Performance**: Key financial metrics including capital disbursed, interest accrued, recovery efficiency %, and total outstanding risk.

---

## Schema Architecture (SQLite)

```sql
CREATE TABLE borrowers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    monthly_income REAL NOT NULL CHECK(monthly_income >= 0)
);

CREATE TABLE loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_reference TEXT UNIQUE NOT NULL,
    borrower_id INTEGER NOT NULL REFERENCES borrowers(id),
    principal_amount REAL NOT NULL CHECK(principal_amount > 0),
    interest_rate_percent REAL NOT NULL CHECK(interest_rate_percent >= 0),
    repayment_period_months INTEGER NOT NULL CHECK(repayment_period_months > 0),
    total_interest REAL NOT NULL CHECK(total_interest >= 0),
    total_payable REAL NOT NULL CHECK(total_payable > 0),
    monthly_installment REAL NOT NULL CHECK(monthly_installment > 0),
    amount_repaid REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'Applied' CHECK(status IN ('Applied', 'Approved', 'Rejected', 'Active', 'Repaid', 'Defaulted')),
    application_date DATE NOT NULL,
    approval_date DATE,
    due_date DATE
);

CREATE TABLE repayments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_reference TEXT UNIQUE NOT NULL,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    amount REAL NOT NULL CHECK(amount > 0),
    payment_date DATE NOT NULL,
    payment_method TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE excess_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    excess_reference TEXT UNIQUE NOT NULL,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    excess_amount REAL NOT NULL CHECK(excess_amount > 0),
    payment_date DATE NOT NULL,
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
python3 -m unittest test_loan.py
```
