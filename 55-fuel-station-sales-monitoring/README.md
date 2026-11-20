# Fuel Station Sales & Tank Monitoring System

A high-precision fuel inventory, pump sales accounting, and underground storage tank reconciliation system built in Python and SQLite for filling stations and petroleum retail outlets.

---

## The Problem

Retail fuel stations manage thousands of litres of volatile petroleum products daily. Manual pen-and-paper dip logs and pump meter readings frequently result in calculation discrepancies, undetected underground tank leakage, delivery shortfalls, and inaccurate financial records caused by floating-point binary rounding errors.

This system provides an exact, auditable tracking engine using Python's `Decimal` type to monitor deliveries, compute pump sales, perform daily dip reconciliation, detect stock discrepancies (leakage/shrinkage vs normal variance), and generate revenue reports.

---

## Architectural Principles & Calculations

1. **Exact Decimal Precision**:
   - All financial amounts and fuel volume calculations utilize Python's `decimal.Decimal` module rather than binary IEEE 754 floating-point arithmetic to guarantee accounting accuracy.
2. **Reconciliation Formula**:
   $$\text{Expected Closing Stock} = \text{Opening Dip} + \text{Deliveries Received} - \text{Pump Meter Sales}$$
   $$\text{Discrepancy} = \text{Actual Physical Dip} - \text{Expected Closing Stock}$$
3. **Discrepancy Evaluation**:
   - Categorizes variances: `Balanced` ($\le 5\text{L}$), `Acceptable Normal Variance` ($\le 0.5\%$ throughput), `Significant Shortage / Leakage`, or `Unaccounted Gain / Overfill`.
4. **Tank Capacity Validation**:
   - Deliveries are validated against current tank volume and maximum safe capacity to prevent overfills.

---

## Running the Application

```bash
cd 55-fuel-station-sales-monitoring
python3 main.py
```

---

## Running Automated Tests

```bash
python3 -m unittest test_fuel_station.py -v
```
