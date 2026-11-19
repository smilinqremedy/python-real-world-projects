# Electricity and Household Power Consumption Tracker

A comprehensive command-line energy auditing and utility budget management system developed in Python and SQLite to monitor prepaid electricity consumption, track generator fuel expenses, and project monthly utility costs.

---

## 📌 Problem the Project Solves

Modern households, particularly in regions with multi-tier energy supply (grid power combined with backup fuel generators), struggle with energy budgeting:
- **Unexpected Power Outages from Depleted Units**: Families run out of prepaid meter credits at inconvenient hours due to a lack of remaining-unit tracking.
- **Unnoticed Energy Spikes**: Inefficient appliances cause rapid credit burn without the homeowner's knowledge.
- **Fragmented Backup Costs**: Generator fuel expenditures are paid in cash and rarely factored into total monthly utility budgets, obscuring true living costs.
- **Lack of Monthly Forecasting**: Inability to estimate next month's utility bill based on historical daily burn rates.

The **Electricity and Household Power Consumption Tracker** solves these issues by unifying grid electricity and generator fuel metrics into a single relational database with real-time depletion alerts and monthly projections.

---

## 🎯 Project Objectives

- **Balance & Depletion Tracking**: Continuously calculate remaining prepaid credits ($\sum \text{Purchased} - \sum \text{Consumed}$) and trigger alerts before power cuts.
- **Consumption Rate Analysis**: Determine average daily kilowatt-hour (kWh) burn rates and estimate the exact number of days of electricity remaining.
- **Dual Energy Accounting**: Track grid electricity tariffs alongside generator fuel costs (liters, prices, and engine burn rates) to reflect 100% of household energy spend.
- **Financial Projections**: Extrapolate current daily habits into accurate 30-day monthly expense forecasts.
- **Data Integrity**: Validate all inputs to reject negative meter readings, invalid dates, and illogical consumption deltas.

---

## 🗄 Database Design & Schema (SQLite)

The system manages relational power records in SQLite across four core tables:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│        PREPAID_PURCHASES        │       │     ELECTRICITY_CONSUMPTION     │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK  purchase_id    INTEGER AUTO │       │ PK  log_id         INTEGER AUTO │
│     purchase_date  TEXT NOT NULL│       │     log_date       TEXT UNIQUE  │
│     amount_paid    REAL (> 0)   │       │     units_consumed REAL (>= 0)  │
│     units_credited REAL (> 0)   │       │     meter_reading  REAL         │
│     unit_rate      REAL         │       │     notes          TEXT         │
│     token_number   TEXT         │       │     created_at     TEXT NOT NULL│
│     created_at     TEXT NOT NULL│       └─────────────────────────────────┘
└─────────────────────────────────┘

┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       GENERATOR_EXPENSES        │       │          APP_SETTINGS           │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK  fuel_id        INTEGER AUTO │       │ PK  setting_key   TEXT          │
│     expense_date   TEXT NOT NULL│       │     setting_value TEXT          │
│     fuel_type      TEXT         │       └─────────────────────────────────┘
│     liters_bought  REAL (> 0)   │
│     cost_per_liter REAL (> 0)   │
│     total_cost     REAL (> 0)   │
│     run_hours      REAL (>= 0)  │
│     notes          TEXT         │
│     created_at     TEXT NOT NULL│
└─────────────────────────────────┘
```

---

## ⚙️ Core Mathematical Models & Algorithms

1. **Prepaid Balance & Remaining Days**:
   $$\text{Remaining kWh} = \sum \text{units\_credited} - \sum \text{units\_consumed}$$
   $$\text{Days Remaining} = \frac{\text{Remaining kWh}}{\text{Average Daily kWh}}$$
2. **Effective Grid Tariff Calculation**:
   $$\text{Effective Tariff (\$/kWh)} = \frac{\sum \text{amount\_paid}}{\sum \text{units\_credited}}$$
3. **Monthly Expense Projection**:
   $$\text{Projected Monthly Grid (\$) } = (\text{Avg Daily kWh} \times 30) \times \text{Effective Tariff}$$
   $$\text{Projected Monthly Generator (\$) } = \left(\frac{\sum \text{Fuel Spend}}{\text{Days Tracked}}\right) \times 30$$
   $$\text{Total Projected Energy Expense} = \text{Projected Grid} + \text{Projected Generator}$$
4. **Meter Reading Differential**:
   $$\Delta \text{kWh} = \text{Reading}_{\text{today}} - \text{Reading}_{\text{previous}} \quad (\text{Validates } \Delta \ge 0)$$

---

## ✨ Features

1. **Record Prepaid Electricity Purchases**: Log token recharges with amount, credited units, and auto-computed unit rates ($/kWh).
2. **Record Daily Consumption**: Enter units consumed directly or calculate consumption via cumulative meter readings.
3. **Remaining Units Balance**: Real-time calculation of remaining prepaid kilowatt-hours.
4. **Average Daily Consumption**: Computes household daily kWh burn rates over configurable rolling windows.
5. **Monthly Expense Estimation**: Projects 30-day electricity and generator budgets.
6. **Separate Generator Fuel Tracking**: Log fuel volume (liters), unit prices, total fuel costs, and engine runtime.
7. **Generator Efficiency & Burn Rate**: Computes generator fuel burn rate ($\text{Liters}/\text{Hour}$).
8. **Low-Units Alert Engine**: Real-time warning banner displayed whenever remaining units drop below safety thresholds (configurable, default: 20.0 kWh).
9. **Monthly Energy Reports**: Generates consolidated breakdowns comparing Grid Spend vs. Generator Spend with percentage share.
10. **Persistent SQLite Storage**: Local, offline SQLite relational storage with zero external database dependencies.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Database**: SQLite 3 (Native Python standard library)
- **Standard Library Modules**:
  - `sqlite3`: Relational database storage and aggregate queries.
  - `datetime`: Date validation, parsing, and formatting.
  - `unittest`: Automated unit and integration testing suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Electricity-Power-Consumption-Tracker/
├── database.py           # SQLite connection manager, schema setup, and settings initialization
├── tracker_service.py    # Business logic: formulas, balances, generator analytics, monthly reports
├── main.py               # Interactive CLI interface and navigation menu
├── test_tracker.py       # Automated unit test suite
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
git clone https://github.com/smilinqremedy/Electricity-Power-Consumption-Tracker.git
cd Electricity-Power-Consumption-Tracker
```

*(No third-party packages are required; everything runs out of the box using Python's standard library).*

---

## 💻 How to Run the Application

Launch the command-line interface:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_tracker.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu (with Low-Units Warning)
```text
==========================================================
   ELECTRICITY & POWER CONSUMPTION TRACKER (CLI)   
==========================================================
 [!] LOW UNITS WARNING: Only 14.5 kWh remaining! (Est. 1.2 days left)
----------------------------------------------------------
 1. Record Prepaid Electricity Purchase
 2. Record Daily Electricity Consumption
 3. View Remaining Units & Balance Status
 4. View Average Daily Consumption
 5. Estimate Monthly Energy Expenses
 6. Record Generator Fuel Purchase
 7. View Generator Fuel Expenses Summary
 8. View Recent Daily Consumption History
 9. Generate Monthly Energy Report
 10. Configure Low-Units Alert Threshold
 11. Exit Application
==========================================================
Enter your choice (1-11):
```

### 2. Remaining Units & Balance Status
```text
==================================================
          PREPAID ELECTRICITY BALANCE
==================================================
 Total Units Purchased:          300.00 kWh
 Total Units Consumed:           285.50 kWh
--------------------------------------------------
 Remaining Units Balance:          14.50 kWh
 Equivalent Dollar Value:         $ 2.90
 Low-Units Alert Level:            20.0 kWh
--------------------------------------------------
 STATUS: [!] LOW UNITS ALERT (< 20.0 kWh)
 Estimated Days Remaining: ~1.2 days
==================================================
```

### 3. Monthly Energy Projections
```text
======================================================
          MONTHLY ENERGY EXPENSES PROJECTION
======================================================
 Average Daily Consumption:            12.50 kWh/day
 Projected 30-Day Usage:              375.00 kWh
 Effective Grid Tariff:              $ 0.2000 /kWh
------------------------------------------------------
 Projected Grid Electricity:          $ 75.00
 Projected Generator Fuel:            $ 45.00
======================================================
 TOTAL ESTIMATED MONTHLY BILL:        $ 120.00
======================================================
```

### 4. Consolidated Monthly Energy Report
```text
==========================================================
           ENERGY CONSUMPTION REPORT: 2026-11
==========================================================
 GRID ELECTRICITY:
   Units Purchased:                 300.00 kWh
   Units Consumed:                  285.50 kWh
   Days Tracked:                        24 days
   Daily Average Usage:              11.90 kWh/day
   Total Grid Spend:                $ 60.00
----------------------------------------------------------
 GENERATOR EXPENSES (BACKUP POWER):
   Fuel Purchased:                   30.00 Liters
   Run Hours:                        12.0 hrs
   Total Generator Spend:           $ 45.00
==========================================================
 TOTAL COMBINED ENERGY COST:        $ 105.00
   Grid Power Cost Share:             57.1%
   Generator Cost Share:              42.9%
==========================================================
```

---

## 🧪 Testing

The repository contains automated unit and integration tests in `test_tracker.py`:
- Prepaid purchase recording and unit rate calculation
- Input validation (rejecting negative units, zero recharges, invalid dates)
- Direct consumption and meter reading differentials
- Balance and remaining unit depletion logic
- Low-stock alert triggering
- Average daily consumption computations
- Generator fuel purchase tracking and burn rate calculation
- Monthly consolidated report aggregations

Run tests:
```bash
python3 -m unittest test_tracker.py
```
Output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.534s

OK
```
