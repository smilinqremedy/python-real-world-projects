# Hospital Pharmacy Prescription Management System

A modular, relational pharmacy prescription management and medication dispensing tracking engine built in Python and SQLite for hospital pharmacies and outpatient clinics.

---

## The Problem

Hospital pharmacies process dozens of physician prescriptions daily. Without reliable automation, paper and fragmented workflows risk dispensing incorrect quantities, medication errors, dispensing out-of-stock items, or dispensing more medicine than is physically available in the pharmacy's inventory.

This system provides a structured, automated workflow that verifies doctor and patient records, constructs multi-item prescriptions, evaluates real-time stock availability, strictly prevents over-dispensing, records dispensed medications atomically, tracks patient prescription history, and generates daily dispensing audit reports.

---

## Architecture & Features

1. **Patient & Physician Registration**:
   - Register patients with demographic validation (past date of birth, phone formatting, drug allergies).
   - Register doctors with medical specialization and professional license numbers. Inactive doctors cannot issue prescriptions.

2. **Medicine Inventory Tracking**:
   - Catalog medicines with dosage forms (Tablets, Syrups, Injections, Capsules, Inhalers), strengths, stock counts, unit prices, and reorder levels.
   - Dynamic stock updates and low-stock / reorder alerts.

3. **Multi-Medication Prescriptions**:
   - Unique prescription references (`RX-YYYYMMDD-XXXX`).
   - Add multiple medicines with dosage instructions and duration in days.

4. **Real-Time Medicine Availability Check**:
   - Checks prescription items against current stock before dispensing.
   - Flags shortages with calculated stock deficit numbers.

5. **Strict Over-Dispensing Prevention**:
   - Enforces inventory checks inside database transactions.
   - Raises `InsufficientStockError` and blocks dispensing if any item lacks sufficient quantity.
   - Atomically updates inventory counts upon confirmation.

6. **Dispensing Records & Receipt Generation**:
   - Generates unique dispense references (`DSP-YYYYMMDD-XXXX`).
   - Records dispensing pharmacist, timestamp, line items, and billed totals.
   - Prevents re-dispensing of already dispensed or cancelled prescriptions.

7. **Dispensing Analytics & Audit Reports**:
   - Daily dispensing volume and total pharmacy revenue.
   - Itemized unit quantities dispensed.
   - Real-time low-stock and reorder threshold alerts.

---

## How to Run the Application

```bash
cd 51-hospital-pharmacy-prescription-management
python3 main.py
```

---

## Running Automated Tests

Run the test suite using Python's standard `unittest` runner:

```bash
python3 -m unittest test_pharmacy.py -v
```
