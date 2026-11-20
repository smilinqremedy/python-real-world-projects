# Digital Asset & Equipment Assignment Tracker

A robust, relational IT asset management and equipment allocation tracking system built in Python and SQLite for companies, startups, and enterprise operations.

---

## The Problem

Organizations frequently struggle to maintain an accurate inventory of corporate hardware (laptops, monitors, mobile devices, networking gear) and assign items to employees across departments. Without strict lifecycle tracking, equipment is misplaced, double-assigned, damaged without accountability, or lost during employee offboarding.

This system provides a structured platform to register assets, track physical conditions, enforce business rules preventing double-assignment, record returns, log damage, and generate audit-ready asset allocation reports.

---

## Architectural Principles & Business Rules

1. **Strict Duplicate Assignment Prevention**:
   - Assets possess a state machine: `Available` $\to$ `Assigned` $\to$ `Returned` $\to$ `Available` (or `Damaged` / `Under Repair`).
   - If an asset's status is `Assigned`, any attempt to assign it to another employee is strictly blocked by the service layer.
2. **Immutable Lifecycle History**:
   - Every assignment, return, condition inspection, and repair status transition is logged in `asset_condition_logs`.
3. **Comprehensive Hardware Metadata**:
   - Unique asset tags, serial number uniqueness constraints, purchase date, cost, and condition classification (`New`, `Good`, `Fair`, `Damaged`, `Broken`).
4. **Allocation & Audit Reporting**:
   - Departmental breakdown of assigned assets, available inventory counts, and an active audit alert list of damaged, missing, or under-repair equipment.

---

## Running the Application

```bash
cd 53-digital-asset-assignment-tracker
python3 main.py
```

---

## Running Automated Tests

```bash
python3 -m unittest test_asset_tracker.py -v
```
