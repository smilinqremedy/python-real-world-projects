# Personal Document Expiry Reminder System

A lightweight, dependable command-line utility developed in Python with JSON storage to track important document expiration dates, calculate days remaining, and alert users before documents expire.

---

## 📌 Problem the Project Solves

Individuals manage a growing collection of critical documents: passports, driver's licenses, national ID cards, auto and health insurance policies, lease agreements, work permits, certifications, and debit/credit cards. Due to busy schedules and long renewal intervals (1, 5, or 10 years), people frequently:
- **Forget Renewal Deadlines**: Discover that an essential document has expired only when trying to board a flight, renew a license, or file an insurance claim.
- **Incur Heavy Fines & Penalties**: Face late renewal penalties, impounded vehicles, or expired professional credentials.
- **Experience Emergency Delays**: Suffer expedited processing fees and prolonged administrative delays when scrambling for emergency document renewals.

The **Personal Document Expiry Reminder System** solves this by providing automated tracking, proactive 30-day and 7-day alerts, chronological urgency ordering, and comprehensive expiry audit reports.

---

## 🎯 Project Objectives

- **Eliminate Surprises from Expired Documents**: Continuously monitor expiration dates and compute real-time remaining day counts.
- **Two-Tier Warning Window**:
  - **Upcoming (Within 30 Days)**: Advance notification providing sufficient runway for standard renewals.
  - **Critical (Within 7 Days)**: High-urgency alert demanding immediate action.
- **Category-Based Organization**: Classify documents into standard domains (`Identification`, `Travel`, `Vehicle`, `Financial & Legal`, `Health & Insurance`, `Professional`).
- **Defensive Date Validation**: Reject inverted dates (where expiry precedes issue date), malformed inputs, and missing critical fields.
- **Privacy & Portability**: 100% offline JSON-backed persistence with zero third-party cloud data exposure.

---

## ⚙️ Core Algorithms & Date Math

Let $E$ be the parsed document expiry date (`datetime.date`), and $T$ be the reference date (default: `datetime.date.today()`):

$$\Delta = (E - T).\text{days}$$

### 1. Document Status Classification
The system deterministically tags each document into one of four operational states:

| Condition | Status Code | Badge | Action Required |
|---|---|---|---|
| $\Delta < 0$ | `EXPIRED` | `[EXPIRED]` | Overdue by $\vert\Delta\vert$ days — renew immediately |
| $0 \le \Delta \le 7$ | `CRITICAL` | `[CRITICAL (<=7d)]` | Urgent renewal required within the week |
| $7 < \Delta \le 30$ | `EXPIRING_SOON` | `[EXPIRING (<=30d)]` | Upcoming expiry — begin renewal preparations |
| $\Delta > 30$ | `VALID` | `[VALID]` | Healthy status |

### 2. Defensive Validation & Chronology Checks
- **Date Format Enforced**: Strict parsing via `datetime.strptime(date_str, "%Y-%m-%d")`.
- **Chronological Validity**:
  $$E_{\text{expiry}} > I_{\text{issue}}$$
  If $E \le I$, transaction is rejected with `ValueError("Expiry date must be after issue date")`.

---

## 🗄 Data Structure Design (JSON)

Documents are persisted in `documents.json` using structured documents:

```json
{
  "documents": [
    {
      "id": 1,
      "name": "International Passport",
      "category": "Travel",
      "document_number": "A12345678",
      "issue_date": "2017-06-15",
      "expiry_date": "2027-06-15",
      "issuing_authority": "Immigration Service",
      "notes": "10-year validity booklet",
      "created_at": "2026-11-19 11:30:00",
      "updated_at": "2026-11-19 11:30:00"
    }
  ]
}
```

---

## ✨ Features

1. **Document Registration**: Add documents with names, categories, numbers, issue dates, and expiry dates.
2. **Category Classification**: Organize records into Identification, Travel, Vehicle, Financial, Health, and Professional categories.
3. **Issue & Expiry Tracking**: Preserves complete validity timelines.
4. **Days Remaining Calculation**: Dynamic arithmetic computation of remaining days until expiration.
5. **Expired Document Detection**: Automatically isolates and highlights all past-due documents.
6. **30-Day Upcoming Window**: Lists all documents expiring within a month.
7. **7-Day Critical Alerts**: High-priority alert list for documents requiring emergency attention.
8. **Document Information Updating**: Edit document names, categories, numbers, or renewed dates.
9. **Search by Query**: Substring search across document names, categories, and reference numbers.
10. **Expiry Audit Report**: Consolidated executive summary with category breakdowns and urgent renewal action checklists.
11. **Fault-Tolerant JSON Storage**: Graceful recovery from missing, empty, or corrupted JSON files.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Standard Library Modules**:
  - `datetime`: Strict date parsing, `datetime.date` arithmetic, and delta formatting.
  - `json`: Data serialization and disk persistence.
  - `os`: File existence checks and path management.
  - `unittest`: Automated test suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Personal-Document-Expiry-Reminder/
├── document_manager.py     # Business logic: date validation, delta calculations, filtering, reports
├── main.py                 # Interactive command-line user interface
├── test_document_manager.py# Automated unit test suite
├── .gitignore              # Git exclusion rules
└── README.md               # Project documentation and user manual
```

---

## 🚀 Installation Instructions

### Prerequisites
- Python 3.8 or higher installed on your system. Verify with:
  ```bash
  python3 --version
  ```

### Clone the Repository
```bash
git clone https://github.com/smilinqremedy/Personal-Document-Expiry-Reminder.git
cd Personal-Document-Expiry-Reminder
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
python3 -m unittest test_document_manager.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
========================================================
   PERSONAL DOCUMENT EXPIRY REMINDER SYSTEM (CLI)   
========================================================
 1. Register New Document
 2. View All Registered Documents
 3. View Critical Expiries (Within 7 Days)
 4. View Upcoming Expiries (Within 30 Days)
 5. View Already Expired Documents
 6. Search Documents (Name, Category, Number)
 7. Update Document Information
 8. Generate Full Expiry Report
 9. Delete Document Record
 10. Exit Application
========================================================
Enter your choice (1-10):
```

### 2. Registering a Document
```text
--- [Register New Document] ---
Enter document name: Vehicle Insurance Policy
Select Category:
  1. Identification
  2. Travel
  3. Vehicle
  4. Financial & Legal
  5. Health & Insurance
Choose category (1-8): 3
Enter document number: POL-2026-991
Enter issue date (YYYY-MM-DD): 2025-11-25
Enter expiry date (YYYY-MM-DD): 2026-11-24

✓ Document 'Vehicle Insurance Policy' successfully registered! (ID: 1)
  Status: Expiring in 5 day(s) [CRITICAL (<=7d)]
```

### 3. All Documents Overview Table
```text
==========================================================================================
ID   | Document Name          | Category         | Expiry Date | Days Left  | Status
------------------------------------------------------------------------------------------
1    | Vehicle Insurance      | Vehicle          | 2026-11-24  | 5d         | [CRITICAL (<=7d)]
2    | Driver's License       | Identification   | 2026-12-10  | 21d        | [EXPIRING (<=30d)]
3    | International Passport | Travel           | 2030-01-01  | 1139d      | [VALID]
4    | Old Health Card        | Health & Ins     | 2026-11-09  | -10d (Past)| [EXPIRED]
==========================================================================================
```

### 4. Consolidated Expiry Audit Report
```text
============================================================
        PERSONAL DOCUMENT EXPIRY AUDIT REPORT
        Date: 2026-11-19
============================================================
 Total Registered Documents:            4
------------------------------------------------------------
 Valid & Active (> 30 days):            1  [HEALTHY]
 Expiring Soon (8 - 30 days):           1  [UPCOMING]
 Critical Expiries (<= 7 days):         1  [URGENT]
 Already Expired:                       1  [ACTION REQUIRED]
============================================================

--- Category Breakdown ---
  Vehicle                       :   1 document(s)
  Identification                :   1 document(s)
  Travel                        :   1 document(s)
  Health & Insurance            :   1 document(s)

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
          URGENT RENEWAL ACTION CHECKLIST
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 • [ID: 4  ] Old Health Card (Health & Insurance) -> EXPIRED [Due: 2026-11-09]
 • [ID: 1  ] Vehicle Insurance (Vehicle) -> Expires in 5d [Due: 2026-11-24]
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

---

## 🧪 Testing

The repository contains automated unit tests in `test_document_manager.py` validating:
- Document registration, field persistence, and ID incrementation
- Date parsing and chronology validation ($E_{\text{expiry}} > I_{\text{issue}}$)
- Accurate day calculations ($\Delta = E - T$)
- Automatic status classification (`EXPIRED`, `CRITICAL`, `EXPIRING_SOON`, `VALID`)
- Accurate 7-day and 30-day filtering
- Document updating and record deletion
- Expiry audit report generation
- Corrupted JSON auto-recovery

Run tests:
```bash
python3 -m unittest test_document_manager.py
```
Output:
```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.040s

OK
```
