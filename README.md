# Python Real-World Projects Portfolio

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Projects](https://img.shields.io/badge/Projects-41%20Complete-brightgreen.svg)](#portfolio-projects)

A curated collection of **25 production-grade, modular real-world applications** built in Python. Each project addresses a distinct operational, financial, logistics, or data management challenge using standard library tools (`sqlite3`, `json`, `datetime`, `unittest`) with clean architectural separation between presentation (CLI), business logic (service layer), and persistent data access.

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
| **21** | [Microfinance Loan Management System](21-microfinance-loan-management/) | `21-microfinance-loan-management/` | SQLite | Financial Credit & Lending | :white_check_mark: Complete |
| **22** | [Pharmacy Inventory & Sales System](22-pharmacy-inventory-management/) | `22-pharmacy-inventory-management/` | SQLite | Healthcare & Pharmaceuticals | :white_check_mark: Complete |
| **23** | [School Fee Payment Management System](23-school-fee-management/) | `23-school-fee-management/` | SQLite | Education & Tuition Billing | :white_check_mark: Complete |
| **24** | [Internet Cafe Management System](24-internet-cafe-management/) | `24-internet-cafe-management/` | SQLite | Hospitality & IT Terminals | :white_check_mark: Complete |
| **25** | [Logistics & Shipment Tracking System](25-logistics-shipment-tracking/) | `25-logistics-shipment-tracking/` | SQLite | Freight, Courier & Logistics | :white_check_mark: Complete |
| **31** | [Online Examination Management System](31-online-examination-system/) | `31-online-examination-system/` | SQLite | Education & Assessments | :white_check_mark: Complete |
| **32** | [Automated Email Notification System](32-automated-email-notification/) | `32-automated-email-notification/` | SQLite & smtplib | Communication & Automation | :white_check_mark: Complete |
| **33** | [Real Estate Property Listing & Search System](33-real-estate-property-listing/) | `33-real-estate-property-listing/` | SQLite | Real Estate & Brokerage | :white_check_mark: Complete |
| **41** | [Hospital Patient Records Management System](41-hospital-patient-records/) | `41-hospital-patient-records/` | SQLite | Healthcare & Clinical Records | :white_check_mark: Complete |
| **42** | [Nigerian Tax & Business Revenue Calculator](42-nigerian-business-finance-calculator/) | `42-nigerian-business-finance-calculator/` | SQLite & CSV/PDF | Financial Calculations & Tax | :white_check_mark: Complete |
| **43** | [Job Recruitment & Applicant Tracking System](43-job-recruitment-tracker/) | `43-job-recruitment-tracker/` | SQLite & Local File Storage | Career, HR & Recruitment | :white_check_mark: Complete |
| **51** | [Hospital Pharmacy Prescription Management](51-hospital-pharmacy-prescription-management/) | `51-hospital-pharmacy-prescription-management/` | SQLite | Healthcare & Pharmaceuticals | :white_check_mark: Complete |
| **52** | [Automated Job Application Email Assistant](52-job-application-email-assistant/) | `52-job-application-email-assistant/` | SQLite & smtplib | Communication & Automation | :white_check_mark: Complete |
| **53** | [Digital Asset & Equipment Assignment Tracker](53-digital-asset-assignment-tracker/) | `53-digital-asset-assignment-tracker/` | SQLite | IT Operations & Asset Tracking | :white_check_mark: Complete |
| **54** | [Website Contact Form Spam Detection](54-contact-form-spam-detection/) | `54-contact-form-spam-detection/` | SQLite | Web Security & Form Moderation | :white_check_mark: Complete |
| **55** | [Fuel Station Sales & Tank Monitoring](55-fuel-station-sales-monitoring/) | `55-fuel-station-sales-monitoring/` | SQLite & Decimal | Petroleum Retail & Inventory | :white_check_mark: Complete |
| **56** | [Personal Password Security Audit Tool](56-password-security-audit-tool/) | `56-password-security-audit-tool/` | Local In-Memory | Cybersecurity & Audit | :white_check_mark: Complete |
| **57** | [Customer Subscription & Renewal Management](57-customer-subscription-renewal-management/) | `57-customer-subscription-renewal-management/` | SQLite | SaaS & Recurring Subscriptions | :white_check_mark: Complete |
| **58** | [CSV Data Cleaning & Validation Tool](58-csv-data-cleaning-validation-tool/) | `58-csv-data-cleaning-validation-tool/` | Pandas & CSV | Data Engineering & Cleansing | :white_check_mark: Complete |
| **59** | [API Rate Limiting & Monitoring System](59-api-rate-limiting-monitoring/) | `59-api-rate-limiting-monitoring/` | FastAPI & SQLite | Web Security & API Traffic Control | :white_check_mark: Complete |
| **60** | [Supplier Purchase Order Management](60-supplier-purchase-order-management/) | `60-supplier-purchase-order-management/` | SQLite | Procurement, Inventory & Supply Chain | :white_check_mark: Complete |

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
