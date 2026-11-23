# Project 57: Customer Subscription & Renewal Management System

A robust Python and SQLite solution for SaaS platforms and recurring-billing businesses to manage customer subscription plans, automated renewal schedules, overdue status transitions (Grace Period vs Suspended), strict renewal validation rules, and SaaS financial metrics (MRR, ARR).

## Features

- **Customer Management**: Register and store customer contact information and corporate entity details.
- **Subscription Plans**: Flexible plans supporting Monthly, Quarterly, and Yearly billing cycles.
- **Automated Expiry Calculation**: Dynamically computes future expiry dates based on plan cycle.
- **Strict Business Rule Enforcement**:
  - **Rejection of Cancelled Renewals**: Prevents renewing previously cancelled subscriptions; users must register a new subscription.
  - **Underpayment Rejection**: Rejects renewals where the amount paid is less than the plan price.
- **Overdue Expiration Handling**:
  - Automatically identifies overdue accounts.
  - Transitions subscriptions to **Grace Period** if 1-7 days past due.
  - Transitions subscriptions to **Suspended** if more than 7 days overdue.
- **Expiring Soon Detection**: Queries upcoming renewals within configurable day thresholds (e.g., 7 days) for proactive customer outreach.
- **SaaS Revenue Metrics**:
  - **MRR (Monthly Recurring Revenue)**: Normalized monthly earnings from active and grace period subscriptions.
  - **ARR (Annual Recurring Revenue)**: Annualized recurring revenue projection.
  - **Payment Cashflow**: Complete ledger of initial and renewal payments.

## Database Schema

- `customers`: Customer identifiers, contact details, and account status.
- `subscription_plans`: Plan codes, billing cycles, pricing, and active status.
- `subscriptions`: Reference code, customer ID, plan ID, start date, expiry date, status (`Active`, `Grace Period`, `Suspended`, `Cancelled`), and cancellation reasons.
- `subscription_payments`: Payment references, amounts, payment methods, and dates.
- `renewal_logs`: Historical audit trail of all subscription renewals showing previous vs new expiry dates.

## Installation & Requirements

Requires standard Python 3.10+. No third-party dependencies are required (built using the standard library `sqlite3`, `datetime`, and `secrets`).

```bash
cd 57-customer-subscription-renewal-management
```

## Running the Application

Launch the interactive CLI:

```bash
python3 main.py
```

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_subscription.py -v
```
