# Python Real-World Projects Portfolio

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Projects](https://img.shields.io/badge/Projects-20%20Complete-brightgreen.svg)](#portfolio-projects)

A curated collection of **20 production-grade, modular real-world applications** built in Python. Each project addresses a distinct operational, financial, logistics, or data management challenge using standard library tools (`sqlite3`, `json`, `datetime`, `unittest`) with clean architectural separation between presentation (CLI), business logic (service layer), and persistent data access.

---

## Architecture Principles

Every project in this repository adheres to consistent software engineering standards:
1. **Separation of Concerns**: Presentation (CLI interactive menus), business logic / analytics service layer, and data storage are strictly isolated.
2. **Defensive Programming**: Comprehensive input validation, boundary checking, and custom error handling across all user operations.
3. **Data Integrity & Immutability**: Relational integrity enforced via SQLite foreign key constraints, check constraints, and historical snapshotting for financial calculations.
4. **Standard Library Only**: High portability with zero third-party pip dependencies required.
5. **Independent Testability**: Each project contains a dedicated `unittest` test suite covering business rules, edge cases, and data persistence.

---

## Portfolio Projects

| # | Project Name | Directory | Storage | Domain | Status |
|---|--------------|-----------|---------|--------|--------|
| **01** | [Expense & Budget Tracker](01-expense-budget-tracker/) | `01-expense-budget-tracker/` | JSON | Personal Finance | :white_check_mark: Complete |
| **02** | [Inventory Management System](02-inventory-management/) | `02-inventory-management/` | JSON | Retail & Inventory | :white_check_mark: Complete |
| **03** | [Student Result Management System](03-student-result-management/) | `03-student-result-management/` | JSON | Academic Records | :white_check_mark: Complete |
| **04** | [Hospital Appointment Management System](04-hospital-appointment/) | `04-hospital-appointment/` | SQLite | Healthcare Scheduling | :white_check_mark: Complete |
| **05** | [Electricity & Household Power Tracker](05-electricity-tracker/) | `05-electricity-tracker/` | SQLite | Utility Management | :white_check_mark: Complete |
| **06** | [Job Application Tracking System](06-job-application-tracker/) | `06-job-application-tracker/` | JSON | Career & Recruitment | :white_check_mark: Complete |
| **07** | [Queue Management System](07-queue-management/) | `07-queue-management/` | SQLite | Operations & Queuing | :white_check_mark: Complete |
| **08** | [Personal Document Expiry Reminder](08-document-expiry-reminder/) | `08-document-expiry-reminder/` | JSON | Document Compliance | :white_check_mark: Complete |
| **09** | [Customer Support Ticket System](09-customer-support-tickets/) | `09-customer-support-tickets/` | SQLite | Customer Service CRM | :white_check_mark: Complete |
| **10** | [Sales & Profit Analysis System](10-sales-profit-analysis/) | `10-sales-profit-analysis/` | SQLite | Financial Analytics | :white_check_mark: Complete |
| **11** | [Property Rental Management System](11-property-rental/) | `11-property-rental/` | SQLite | Real Estate & Leasing | :white_check_mark: Complete |
| **12** | [Restaurant Order Management System](12-restaurant-order-management/) | `12-restaurant-order-management/` | SQLite | Food & Hospitality | :white_check_mark: Complete |
| **13** | [Employee Attendance Management System](13-employee-attendance/) | `13-employee-attendance/` | SQLite | Human Resources & Workforce | :white_check_mark: Complete |
| **14** | [Laundry Service Management System](14-laundry-management/) | `14-laundry-management/` | SQLite | Service & Operations | :white_check_mark: Complete |
| **15** | [Vehicle Maintenance Tracking System](15-vehicle-maintenance/) | `15-vehicle-maintenance/` | SQLite | Fleet & Automotive | :white_check_mark: Complete |
| **16** | [Water Delivery Management System](16-water-delivery/) | `16-water-delivery/` | SQLite | Logistics & Route Distribution | :white_check_mark: Complete |
| **17** | [Event Registration & Ticketing System](17-event-ticketing/) | `17-event-ticketing/` | SQLite | Events & Ticketing | :white_check_mark: Complete |
| **18** | [Agricultural Produce Trading System](18-agricultural-trading/) | `18-agricultural-trading/` | SQLite | Agribusiness & Supply Chain | :white_check_mark: Complete |
| **19** | [Technical Repair Service Management](19-technical-repair/) | `19-technical-repair/` | SQLite | Repair & Warranty Services | :white_check_mark: Complete |
| **20** | [Donation & Charity Management System](20-charity-management/) | `20-charity-management/` | SQLite | Non-Profit & Fundraising | :white_check_mark: Complete |

---

## How to Run Any Project

Navigate into any project directory and launch its entrypoint:

```bash
cd 01-expense-budget-tracker
python3 main.py
```

To run the automated test suite for any project:

```bash
python3 -m unittest discover -s . -p "test_*.py"
```
