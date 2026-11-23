# Project 60: Supplier Purchase Order Management System

A robust, enterprise-grade Python and SQLite purchasing and inventory replenishment system designed for wholesale, manufacturing, retail, and construction businesses to manage supplier records, order workflows, partial physical deliveries, atomic inventory balance updates, and supplier debt accounting.

## Features

- **Supplier Directory**: Register and manage vendor profiles, contact personnel, and addresses.
- **Product Catalog & Reorder Monitoring**:
  - Maintain SKUs, names, unit costs, physical inventory stock, and reorder levels.
  - Automatic low-stock detection whenever warehouse quantities fall to or below reorder levels.
- **Structured Purchase Order Workflow**:
  - Status lifecycle: `Draft` $\rightarrow$ `Approved` $\rightarrow$ `Partially Delivered` $\rightarrow$ `Completed` (or `Cancelled`).
  - **Draft Rule**: Line items can only be added or modified while the PO is in `Draft` state.
  - **Empty PO Prevention**: Cannot approve a PO without at least one line item.
  - **Approval Lock**: Once approved, orders are committed and cannot be reverted to draft.
- **Atomic Delivery & Inventory Synchronization**:
  - Uses transactional integrity (`with conn:`) to ensure warehouse inventory stock increments **only** upon confirmed physical arrival.
  - **Over-delivery Prevention**: Rejects delivery attempts that exceed remaining ordered quantities.
  - **Partial Delivery Tracking**: Automatically transitions PO status to `Partially Delivered` until all line items are fulfilled, at which point status automatically updates to `Completed`.
  - Maintains a full historical audit log of every physical delivery package received.
- **Supplier Financial Statements**:
  - Tracks total order values, disbursements/payments made, and net outstanding balance per vendor.
  - Supports recording partial or full payments mapped to supplier accounts.
- **Purchasing Analytics & Dashboards**:
  - Global overview of total committed spend, open vs completed orders, and low-stock alerts.

## Database Schema

- `suppliers`: Supplier code, company name, contact person, email, and phone.
- `products`: SKU, product name, category, unit cost, current stock quantity, and reorder level.
- `purchase_orders`: Unique PO reference, supplier ID, order date, status, and total amount.
- `po_items`: PO ID, product ID, quantity ordered, unit cost, quantity received, and line subtotal.
- `delivery_logs`: Detailed receipts of physical goods delivered, receiving staff, and timestamps.
- `supplier_payments`: Payment references, amounts, methods, dates, and account allocations.

## Installation & Requirements

Requires standard Python 3.10+. Built entirely on Python standard library modules (`sqlite3`, `datetime`, `secrets`). No external packages are required.

```bash
cd 60-supplier-purchase-order-management
```

## Running the Application

Launch the interactive CLI:

```bash
python3 main.py
```

## Running Automated Tests

Run the complete unit test suite:

```bash
python3 -m unittest test_po.py -v
```
