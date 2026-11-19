# Small Business Sales and Profit Analysis System

A command-line financial intelligence and managerial accounting system developed in Python and SQLite to help small business owners calculate true profitability, track Cost of Goods Sold (COGS), monitor operational expenses (OPEX), and generate Profit & Loss (P&L) statements.

---

## 📌 Problem the Project Solves

Small business owners frequently confuse **Gross Cash Inflow (Revenue)** with **True Business Profit**. Without a structured accounting system, entrepreneurs encounter dangerous blind spots:
- **Misleading Revenue Numbers**: Celebrating record-breaking top-line sales while losing money due to unaccounted product procurement costs.
- **Untracked Cost of Goods Sold (COGS)**: Inability to determine individual product gross margins and real unit economics.
- **Ignored Operating Overhead**: Operational expenses (Rent, Staff Wages, Utilities, Packaging, Logistics, and Marketing) are paid ad-hoc and excluded from product pricing strategies.
- **Inability to Identify Real Growth Drivers**: Difficulty pinpointing which products yield the highest net financial returns versus which products merely tie up working capital.

The **Small Business Sales and Profit Analysis System** eliminates financial guesswork by decoupling product margins from business overhead, delivering real-time P&L insights.

---

## 🎯 Project Objectives

- **Dual-Tier Profit Calculation**: Automatically calculate both **Gross Profit** ($\text{Revenue} - \text{COGS}$) and **Net Profit** ($\text{Gross Profit} - \text{Operating Expenses}$).
- **Accurate Financial Formulas**: Maintain strict precision using standard decimal arithmetic to eliminate precision drift across large sales volumes.
- **Comprehensive Expense Tracking**: Categorize operational overhead across Rent, Utilities, Salaries, Marketing, and Supplies.
- **Actionable Merchandising Insights**: Rank top-performing products by both total volume sold and gross profit generated.
- **Separation of Concerns**: Architect the platform into distinct data storage, business logic/service, and interactive CLI presentation layers.

---

## ⚙️ Accounting Equations & Financial Models

```
    TOTAL SALES REVENUE  (Units Sold × Unit Selling Price)
           │
           ▼
  [ - ] COST OF GOODS SOLD (COGS)  (Units Sold × Unit Purchase Cost)
           │
           ▼
    GROSS PROFIT  (Product-level Profitability)
           │
           ▼
  [ - ] OPERATIONAL EXPENSES (OPEX)  (Rent, Salaries, Utilities, Delivery, Marketing)
           │
           ▼
    NET PROFIT  (Actual Take-Home Business Bottom Line)
```

### Core Financial Formulas
1. **Total Revenue**:
   $$\text{Total Revenue} = \sum_{s \in \text{Sales}} (s.\text{quantity} \times s.\text{unit\_selling\_price})$$
2. **Cost of Goods Sold (COGS)**:
   $$\text{Total COGS} = \sum_{s \in \text{Sales}} (s.\text{quantity} \times s.\text{unit\_cost\_price})$$
3. **Gross Profit & Margin**:
   $$\text{Gross Profit} = \text{Total Revenue} - \text{Total COGS}$$
   $$\text{Gross Profit Margin \%} = \frac{\text{Gross Profit}}{\text{Total Revenue}} \times 100$$
4. **Total Operational Expenses (OPEX)**:
   $$\text{Total OPEX} = \sum_{e \in \text{Expenses}} e.\text{amount}$$
5. **Net Profit & Net Margin**:
   $$\text{Total Expenses} = \text{Total COGS} + \text{Total OPEX}$$
   $$\text{Net Profit} = \text{Gross Profit} - \text{Total OPEX} = \text{Total Revenue} - \text{Total Expenses}$$
   $$\text{Net Profit Margin \%} = \frac{\text{Net Profit}}{\text{Total Revenue}} \times 100$$

---

## 🗄 Database Design & Schema (SQLite)

The system persists transactional data in SQLite with relational foreign keys:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│            PRODUCTS             │       │              SALES              │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK  product_id    INTEGER AUTO  │       │ PK  sale_id        INTEGER AUTO │
│     product_name  TEXT UNIQUE   │       │ FK  product_id     INTEGER NOT  │
│     category      TEXT          │       │     sale_date      TEXT NOT NULL│
│     cost_price    REAL (> 0)    │       │     quantity       INTEGER (> 0)│
│     selling_price REAL (> 0)    │       │     unit_cost_price REAL (> 0)  │
│     created_at    TEXT NOT NULL │       │     unit_selling_price REAL(> 0)│
│     updated_at    TEXT NOT NULL │       │     total_revenue  REAL NOT NULL│
└──────────────┬──────────────────┘       │     total_cogs     REAL NOT NULL│
               │                          │     gross_profit   REAL NOT NULL│
               │ 1                        │     customer_notes TEXT         │
               │                          │     created_at     TEXT NOT NULL│
               └────────────────────────► └─────────────────────────────────┘
                                       N

┌─────────────────────────────────┐
│      OPERATIONAL_EXPENSES       │
├─────────────────────────────────┤
│ PK  expense_id    INTEGER AUTO  │
│     expense_date  TEXT NOT NULL │
│     category      TEXT NOT NULL │
│     amount        REAL (> 0)    │
│     description   TEXT NOT NULL │
│     created_at    TEXT NOT NULL │
└─────────────────────────────────┘
```

---

## ✨ Features

1. **Product Catalog Registration**: Register products with distinct purchase costs and retail selling prices.
2. **Pricing Maintenance**: Update baseline cost and selling prices at any time.
3. **Transaction Logging**: Record customer sales with quantity and automatic pricing snapshots.
4. **Automated COGS & Revenue Calculation**: Computes sales revenue and cost of goods sold simultaneously upon checkout.
5. **Gross Profit Tracking**: Measures immediate trading profitability per transaction.
6. **Operational Expense Recording**: Track business overhead across Rent, Salaries, Utilities, Transport, and Supplies.
7. **Net Profit Calculation**: Factors operating expenses against gross earnings to calculate net income.
8. **Best-Selling Product Identification**: Identifies top revenue drivers and volume leaders.
9. **Daily Sales Reports**: Provides day-by-day revenue, COGS, and gross profit audits.
10. **Monthly Financial P&L Statement**: Full monthly Profit & Loss financial statements with category breakdowns.
11. **Overall Financial Dashboard**: Unified display of lifetime revenue, total expenses, and net profit margins.
12. **Persistent SQLite Database**: Local, offline SQLite storage requiring zero external database configuration.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Database**: SQLite 3 (Standard Library)
- **Standard Library Modules**:
  - `sqlite3`: Relational schema, aggregate functions, and foreign keys.
  - `datetime`: Standardized date formatting and month aggregations.
  - `unittest`: Automated unit and integration testing.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Small-Business-Sales-Profit-Analysis-System/
├── database.py           # SQLite connection, schema setup, check constraints, indexes
├── analytics_service.py  # Business logic: accounting formulas, P&L reports, bestsellers
├── main.py               # Interactive CLI interface
├── test_analytics.py     # Automated unit and integration test suite
├── .gitignore            # Git exclusion rules
└── README.md             # Project documentation and user manual
```

---

## 🚀 Installation Instructions

### Prerequisites
- Python 3.8 or higher installed on your computer. Verify with:
  ```bash
  python3 --version
  ```

### Clone the Repository
```bash
git clone https://github.com/smilinqremedy/Small-Business-Sales-Profit-Analysis-System.git
cd Small-Business-Sales-Profit-Analysis-System
```

*(No third-party packages or virtual environment installations required; runs purely with standard Python).*

---

## 💻 How to Run the Application

Launch the command-line interface:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_analytics.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
==========================================================
   SMALL BUSINESS SALES & PROFIT ANALYSIS SYSTEM (CLI)   
==========================================================
 1. Register New Product
 2. Record Customer Sale
 3. Record Operational Expense
 4. View Financial Summary (Revenue, Expenses & Profit)
 5. Identify Best-Selling Products
 6. Generate Daily Sales Report
 7. Generate Monthly Financial Report (P&L)
 8. View Product Catalog & Update Pricing
 9. View Recent Sales Log
 10. View Operational Expenses Log
 11. Exit System
==========================================================
Enter your choice (1-11):
```

### 2. Recording a Customer Sale
```text
--- [Record Customer Sale] ---
Enter Product ID sold: 1
Enter quantity sold: 5
Enter sale date (YYYY-MM-DD) [default: 2026-11-19]: 

==================================================
                 SALE RECORDED
==================================================
 Sale ID:        #1
 Product:        Artisan Coffee Beans
 Quantity:       5 units @ $18.00
 Total Revenue:  $90.00
 Cost of Goods:  $40.00
 Gross Profit:   $50.00
==================================================
```

### 3. Overall Financial Summary
```text
======================================================
           OVERALL FINANCIAL & PROFIT SUMMARY
======================================================
 Total Sales Completed:                    14
 Total Product Units Sold:                 85
------------------------------------------------------
 TOTAL REVENUE (Inflow):             $   1,530.00
 Cost of Goods Sold (COGS):          $     680.00
------------------------------------------------------
 GROSS PROFIT:                       $     850.00
 Gross Profit Margin:                       55.56%
------------------------------------------------------
 Total Operating Expenses:           $     320.00
 Total Overall Expenses:             $   1,000.00
======================================================
 NET PROFIT:                         $     530.00 [SURPLUS (Net Profit)]
 Net Profit Margin:                         34.64%
======================================================
```

### 4. Monthly Profit & Loss Statement (P&L)
```text
============================================================
         PROFIT & LOSS FINANCIAL STATEMENT: 2026-11
============================================================
 REVENUE:
   Gross Sales Revenue:            $       1,530.00
   Cost of Goods Sold (COGS):      $         680.00
------------------------------------------------------------
 GROSS PROFIT:                     $         850.00 (55.6%)
------------------------------------------------------------
 OPERATIONAL EXPENSES (OPEX):
   • Rent & Facilities             : $       150.00
   • Utilities (Power & Internet)  : $        70.00
   • Logistics & Delivery          : $        60.00
   • Packaging Supplies            : $        40.00
   Total Operating Expenses:       $         320.00
============================================================
 NET PROFIT:                       $         530.00 [SURPLUS]
 Net Profit Margin:                           34.6%
 Total Expenses (COGS + OPEX):     $       1,000.00
============================================================
```

---

## 🧪 Testing

The repository contains automated unit tests in `test_analytics.py` validating:
- Product catalog registration and pricing update logic
- Input validation (rejecting negative costs, negative amounts, invalid dates)
- Exact COGS, Revenue, and Gross Profit computations
- Operational expense recording and classification
- Net profit deduction ($\text{Gross Profit} - \text{OPEX}$)
- Best-selling product rankings (by volume and by revenue)
- Daily sales report aggregations
- Monthly P&L statement generation

Run tests:
```bash
python3 -m unittest test_analytics.py
```
Output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.530s

OK
```
