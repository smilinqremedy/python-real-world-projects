# Customer Complaint and Support Ticket Management System

A robust, relational command-line support operations platform developed in Python and SQLite for small businesses to manage customer complaints, enforce assignment business rules, and resolve service issues.

---

## 📌 Problem the Project Solves

Small and mid-sized businesses frequently handle customer support through unorganized inboxes, spreadsheets, or chat logs. This unstructured approach causes major operational breakdowns:
- **Lost and Overlooked Complaints**: Issues fall through the cracks without assigned ownership or due dates.
- **Unenforced Accountability**: Tickets are moved into active progress without an assigned support agent, obscuring who is responsible for resolution.
- **Poor SLA & Priority Management**: High-severity outages and critical payment failures are buried beneath low-priority inquiries.
- **Zero Visibility into Resolution Health**: Management cannot measure team resolution rates, recurring category bottlenecks, or open backlog volume.

The **Customer Complaint and Support Ticket Management System** resolves these issues by enforcing a strict state machine, automated unique ticket generation, agent assignment verification, and priority-driven queuing.

---

## 🎯 Project Objectives

- **Enforce Business Integrity Rules**: Block unassigned tickets from transitioning to `In Progress` status until an active support agent claims ownership.
- **Automate Incident Categorization**: Classify complaints into standard tiers (`Billing`, `Technical`, `Product Quality`, `Delivery`, `Security`, `General`) and four priority ratings (`Low`, `Medium`, `High`, `Critical`).
- **Priority-Driven Incident Queuing**: Order unresolved tickets by severity so support agents address critical business blockers first.
- **End-to-End Incident Lifecycle**: Model clear status state transitions:
  $$\text{Open} \longrightarrow \text{In Progress} \longrightarrow \text{Resolved} \longleftrightarrow \text{Reopened}$$
- **Operational Performance Reporting**: Generate real-time analytics covering resolution rates, status distribution, and priority breakdowns.

---

## 🏗 Architecture & System Design

The system implements a decoupled, 3-tier backend architecture:

```
┌────────────────────────────────────────────────────────┐
│            Presentation Layer (main.py - CLI)          │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│      Service Layer (ticket_service.py - Business Logic)│
│  - State Machine Transitions (Open -> In Progress, etc)│
│  - Business Rule: Unassigned cannot move to In Progress│
│  - Priority Matrix & Ordering                          │
│  - Funnel & Analytics Reporting                        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│          Database Layer (database.py - SQLite)         │
│  - Relational Schema, Foreign Keys & Check Constraints │
│  - Seed Initial Agents & Customer Profiles             │
└────────────────────────────────────────────────────────┘
```

---

## 🗄 Database Design & Schema (SQLite)

The system enforces foreign keys (`PRAGMA foreign_keys = ON;`) across three relational tables:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│            CUSTOMERS            │       │         SUPPORT_AGENTS          │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK  customer_id    INTEGER AUTO │       │ PK  agent_id     INTEGER AUTO │
│     full_name      TEXT NOT NULL│       │     full_name    TEXT NOT NULL│
│     email          TEXT UNIQUE  │       │     email        TEXT UNIQUE  │
│     phone          TEXT         │       │     department   TEXT NOT NULL│
│     company_name   TEXT         │       │     is_active    INTEGER (1)  │
│     created_at     TEXT NOT NULL│       └──────────────┬──────────────────┘
└──────────────┬──────────────────┘                      │
               │                                         │
               │ 1                                       │ 1
               │                                         │
               │         ┌───────────────────────┐       │
               └───────► │        TICKETS        │ ◄─────┘
                       N ├───────────────────────┤ N
                         │ PK  ticket_id   INT   │
                         │     ticket_code TEXT  │
                         │ FK  customer_id INT   │
                         │ FK  agent_id    INT   │
                         │     title       TEXT  │
                         │     description TEXT  │
                         │     category    TEXT  │
                         │     priority    TEXT  │
                         │     status      TEXT  │
                         │     resolution_notes  │
                         │     created_at  TEXT  │
                         │     updated_at  TEXT  │
                         │     resolved_at TEXT  │
                         └───────────────────────┘
```

---

## ⚙️ Core Business Rules & Workflow

1. **Unique Ticket ID Generation**:
   $$\text{Format} = \text{TICK-YYYY-NNN} \quad (\text{e.g. TICK-2026-001})$$
2. **Business Rule 9 (Strict Assignment Enforcement)**:
   $$\text{Status} \to \text{"In Progress"} \implies \text{agent\_id} \ne \text{NULL}$$
   Attempting to transition an unassigned ticket into `In Progress` raises:
   `ValueError: Business Rule Violation: Unassigned tickets cannot be moved to 'In Progress'.`
3. **Priority Hierarchy Sorting**:
   Unresolved tickets (`Open`, `In Progress`, `Reopened`) are displayed according to SLA severity:
   $$\text{Critical (Rank 1)} \prec \text{High (Rank 2)} \prec \text{Medium (Rank 3)} \prec \text{Low (Rank 4)}$$
4. **Resolution Tracking**:
   Transitioning to `Resolved` records resolution notes and timestamps `resolved_at`.

---

## ✨ Features

1. **Customer Registration**: Enrolls customers with contact info, organization, and unique emails.
2. **Support Ticket Creation**: Files complaints with categories, detailed descriptions, and priorities.
3. **Unique Ticket Codes**: Auto-increments standardized ticket identifiers (`TICK-YYYY-NNN`).
4. **Category Classification**: Classifies issues into Billing, Technical, Product Quality, Shipping, Security, and General Inquiry.
5. **Priority Assignment**: Assigns severity levels: `Low`, `Medium`, `High`, and `Critical`.
6. **Support Agent Assignment**: Allocates tickets to specialized agents and departments.
7. **Status Lifecycle Tracking**: Manages states: `Open`, `In Progress`, `Resolved`, and `Reopened`.
8. **Assignment Rule Guard**: Automatically prevents unassigned tickets from moving into progress.
9. **Unresolved Priority Queuing**: Displays unresolved backlogs sorted from Critical down to Low.
10. **Ticket Search**: Instant lookup by numeric ID (e.g., `1`) or formatted code (e.g., `TICK-2026-001`).
11. **Comprehensive Reporting**: Generates operational summaries with status, priority, and category breakdowns.
12. **Persistent SQLite Database**: Embedded relational storage requiring zero cloud setup.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Database**: SQLite 3 (Standard Library)
- **Standard Library Modules**:
  - `sqlite3`: Relational schema, foreign keys, and analytical queries.
  - `datetime`: Standardized timestamps (`YYYY-MM-DD HH:MM:SS`).
  - `unittest`: Automated unit and integration testing.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Customer-Complaint-Support-Ticket-System/
├── database.py       # SQLite connection, schema setup, check constraints, agent seeding
├── ticket_service.py # Business rules, state machine, assignment, priority matrix, reporting
├── main.py           # Interactive command-line interface
├── test_tickets.py   # Automated unit and integration test suite
├── .gitignore        # Git exclusion rules
└── README.md         # Project documentation and user manual
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
git clone https://github.com/smilinqremedy/Customer-Complaint-Support-Ticket-System.git
cd Customer-Complaint-Support-Ticket-System
```

*(No external pip packages are required. The project runs out of the box using standard Python).*

---

## 💻 How to Run the Application

Launch the command-line interface:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_tickets.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
==========================================================
   CUSTOMER COMPLAINT & SUPPORT TICKET SYSTEM (CLI)   
==========================================================
 1. Register New Customer
 2. Create Support Ticket (File Complaint)
 3. Assign Ticket to Support Agent
 4. Update Ticket Status (Open/In Progress/Resolved/Reopened)
 5. Display Unresolved Tickets (Priority Order)
 6. Search Ticket by ID or Code
 7. View All Tickets Roster
 8. Generate Support & Resolution Reports
 9. View Support Agents Directory
 10. Exit Application
==========================================================
Enter your choice (1-10):
```

### 2. Creating a Support Ticket
```text
--- [Create Support Ticket] ---
Enter Customer ID: 1
Enter ticket title / summary: Payment Double Billed
Enter detailed complaint description: Subscription charged twice for order #9988.
Select Ticket Category: 1 (Billing & Payments)
Select Priority Level: 4 (Critical)
Select agent ID: 0 (Leave unassigned)

****************************************************
           SUPPORT TICKET CREATED
****************************************************
 Ticket Code:      TICK-2026-001 (ID: #1)
 Customer:         Sarah Connor (s.connor@cyberdyne.com)
 Title:            Payment Double Billed
 Category:         Billing & Payments
 Priority:         [CRITICAL]
 Assigned Agent:   Unassigned
 Initial Status:   Open
****************************************************
```

### 3. Business Rule Enforcement
Attempting to move an unassigned ticket into `In Progress`:
```text
[Operation Failed] Business Rule Violation: Unassigned tickets cannot be moved to 'In Progress'. Please assign a support agent to the ticket first.
```

### 4. Unresolved Tickets Ordered by Priority
```text
================================================================================================
Code           | Priority  | Status       | Category           | Customer           | Agent
------------------------------------------------------------------------------------------------
TICK-2026-001  | [CRITICAL]| In Progress  | Billing & Payments | Sarah Connor       | Alex Rivera
TICK-2026-002  | [HIGH]    | Open         | Technical Support  | John Doe           | [UNASSIGNED]
TICK-2026-003  | [MEDIUM]  | Open         | Product Quality    | Bruce Wayne        | [UNASSIGNED]
TICK-2026-004  | [LOW]     | Open         | General Inquiry    | Clark Kent         | [UNASSIGNED]
================================================================================================
```

### 5. Support Metrics & Resolution Report
```text
==========================================================
         CUSTOMER SUPPORT & RESOLUTION REPORT
==========================================================
 Total Tickets Created:                   4
 Resolved Tickets:                        1
 Unresolved / In-Flight:                  3
 Resolution Rate:                     25.0%
----------------------------------------------------------
 STATUS BREAKDOWN:
   Open            :    2 ( 50.0%) ■■■■■■■■■■
   In Progress     :    1 ( 25.0%) ■■■■■
   Resolved        :    1 ( 25.0%) ■■■■■
   Reopened        :    0 (  0.0%) 
----------------------------------------------------------
 PRIORITY BREAKDOWN:
   Critical        :    1 ( 25.0%) ■■■■■
   High            :    1 ( 25.0%) ■■■■■
   Medium          :    1 ( 25.0%) ■■■■■
   Low             :    1 ( 25.0%) ■■■■■
==========================================================
```

---

## 🧪 Testing

The repository contains automated unit tests in `test_tickets.py` validating:
- Database schema setup and agent seeding
- Customer email uniqueness
- Ticket creation, category validation, and sequential code generation
- Agent assignment
- **Business Rule 9 enforcement**: blocking unassigned tickets from moving to `In Progress`
- Complete status lifecycle (`Open` $\rightarrow$ `In Progress` $\rightarrow$ `Resolved` $\rightarrow$ `Reopened`)
- Priority ordering (`Critical` $\rightarrow$ `High` $\rightarrow$ `Medium` $\rightarrow$ `Low`)
- Direct lookup by numeric ID and string code
- Resolution reporting calculations

Run tests:
```bash
python3 -m unittest test_tickets.py
```
Output:
```text
.........
----------------------------------------------------------------------
Ran 9 tests in 0.588s

OK
```
