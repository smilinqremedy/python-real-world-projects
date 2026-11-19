# Bank & Service Centre Queue Management System

A high-performance command-line queue management and customer flow control system developed in Python and SQLite for commercial banks, government registries, and public service centres.

---

## 📌 Problem the Project Solves

High-traffic service centres (such as bank branches, postal offices, and municipal licensing centres) suffer from manual crowd handling issues:
- **Disorganized Waiting Lines**: Physical queues cause standing fatigue, disputes over service order, and lobby overcrowding.
- **Uncontrolled Waiting Times**: Lack of visibility into which service categories experience the highest bottlenecks.
- **Counter Idle Time vs. Overload**: Inability to efficiently route waiting customers to available service desks as soon as an officer becomes free.
- **No Operational Accountability**: Absence of automated tracking for average customer wait times, officer service speeds, and no-show/cancellation rates.

The **Queue Management System** replaces physical lines with a digital, FIFO queue architecture backed by categorized ticket numbering, live queue boards, counter assignment, and real-time wait time analytics.

---

## 🎯 Project Objectives

- **Automate FIFO Customer Dispatch**: Implement standard First-In, First-Out (FIFO) queue mechanics utilizing Python's `collections.deque` for $O(1)$ constant-time enqueue and dequeue operations.
- **Category-Based Queue Routing**: Route incoming customers to specialized service queues (`Teller`, `Customer Service`, `Loans`, `Account Opening`) while maintaining an overarching unified waiting queue.
- **End-to-End Service Lifecycle**: Track each customer's complete journey:
  $$\text{Arrival (Waiting)} \longrightarrow \text{Called to Counter (Serving)} \longrightarrow \text{Completed / Cancelled}$$
- **Operational Efficiency Analytics**: Measure exact wait times ($\text{Called} - \text{Created}$) and service durations ($\text{Completed} - \text{Called}$) to calculate average wait metrics.
- **Persistent State Management**: Back in-memory FIFO structures with SQLite to survive application restarts without losing queue order.

---

## ⚙️ How the Queue Data Structure Works

In computer science, a **Queue** is a linear data structure adhering strictly to the **First-In, First-Out (FIFO)** operational principle: the first customer to arrive is the first customer served.

```
Incoming Customer ──────► [ ENQUEUE: append() ]
                               │
                               ▼
                       ┌──────────────┐
                       │   TX - 103   │  Tail of Queue (Last In)
                       ├──────────────┤
                       │   TX - 102   │
                       ├──────────────┤
                       │   TX - 101   │  Head of Queue (First Out)
                       └───────┬──────┘
                               │
Service Counter Officer ◄──────┴── [ DEQUEUE: popleft() ]
```

### Why `collections.deque` over Python `list`?
In standard Python lists, calling `list.pop(0)` takes $O(n)$ linear time complexity because all remaining elements must be shifted in memory. Python's `collections.deque` (double-ended queue) is implemented internally as a doubly-linked list of memory blocks, offering **guaranteed $O(1)$ constant-time operations** for both `append()` (enqueue) and `popleft()` (dequeue).

---

## 🗄 Database Design & Schema (SQLite)

The system persists queue state in SQLite across three relational tables:

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       SERVICE_CATEGORIES        │       │        SERVICE_COUNTERS         │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ PK  category_id    INTEGER AUTO │       │ PK  counter_id    INTEGER       │
│     code           TEXT UNIQUE  │       │     officer_name  TEXT NOT NULL │
│     name           TEXT NOT NULL│       │     current_ticket_id INT       │
│     description    TEXT         │       └─────────────────────────────────┘
└─────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                               QUEUE_TICKETS                               │
├───────────────────────────────────────────────────────────────────────────┤
│ PK  ticket_id            INTEGER PRIMARY KEY AUTOINCREMENT                │
│     ticket_number        TEXT UNIQUE NOT NULL  (e.g., 'TX-101', 'CS-102') │
│     customer_name        TEXT NOT NULL                                    │
│     customer_phone       TEXT                                             │
│     category_code        TEXT NOT NULL REFERENCES service_categories(code)│
│     counter_id           INTEGER REFERENCES service_counters(counter_id)  │
│     status               TEXT CHECK(status IN ('waiting','serving',       │
│                                                'completed','cancelled'))  │
│     created_at           TEXT NOT NULL (Arrival timestamp)                │
│     called_at            TEXT (Timestamp called to desk)                  │
│     completed_at         TEXT (Timestamp service finished)                │
│     wait_time_seconds    INTEGER (called_at - created_at)                 │
│     service_time_seconds INTEGER (completed_at - called_at)              │
│     notes                TEXT                                             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

1. **Customer Registration & Ticket Issuance**: Registers incoming visitors with names, phone numbers, and inquiry notes.
2. **Category Prefix Queue Numbers**: Auto-generates unique formatted ticket numbers (`TX-101` for Teller, `CS-101` for Customer Service, `LN-101` for Loans, `AC-101` for Account Opening).
3. **FIFO Queue Enqueueing**: Places customers in both specialized category queues and a unified service queue.
4. **Counter Officer Dispatch (Call Next)**: Dequeues the next waiting customer and assigns them to an open service desk.
5. **Live Counter Monitoring**: Real-time display showing which officer is serving which customer and current consultation duration.
6. **Mark Customer as Served**: Records completion timestamp, calculates exact service duration, and frees the counter desk for the next ticket.
7. **Ticket Cancellation**: Removes no-shows or early departures from the active line without disrupting queue ordering.
8. **Live Waiting Queue Board**: Displays all waiting tickets, arrival timestamps, and elapsed wait times so far.
9. **Completed Services Audit Log**: Complete history of served customers with wait times and service durations.
10. **Average Waiting Time Analytics**: Calculates overall and category-by-category average wait times and consultation speeds.
11. **Persistent SQLite Storage**: Embedded local storage ensures zero data loss during power outages or system restarts.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Data Structures**: `collections.deque` (FIFO Queue), `dict`, `list`
- **Database**: SQLite 3 (Native Python standard library)
- **Standard Library Modules**:
  - `sqlite3`: Relational database storage, foreign keys, and indexes.
  - `datetime`: Timestamping, duration arithmetic, and time formatting.
  - `unittest`: Automated unit and integration test suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Queue-Management-System/
├── database.py       # SQLite connection manager, schema migrations, and initial seeds
├── queue_manager.py  # Business logic: FIFO deques, ticket numbering, counter dispatch, analytics
├── main.py           # Interactive CLI interface and live waiting displays
├── test_queue.py     # Automated unit test suite
├── .gitignore        # Git exclusion rules
└── README.md         # Project documentation and user manual
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
git clone https://github.com/smilinqremedy/Queue-Management-System.git
cd Queue-Management-System
```

*(No external pip libraries are required. Everything runs out of the box using Python's standard library).*

---

## 💻 How to Run the Application

Launch the command-line interface:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_queue.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
========================================================
      BANK & SERVICE CENTRE QUEUE SYSTEM (CLI)     
========================================================
 1. Issue Queue Ticket (Register Customer)
 2. Call Next Customer to Service Counter
 3. View Currently Serving Desks
 4. Mark Customer Service as Completed
 5. View Live Waiting Queue Board
 6. Cancel Queue Ticket
 7. View Completed Services History
 8. View Average Waiting Time & Queue Analytics
 9. View Service Categories & Counters
 10. Exit System
========================================================
Enter your choice (1-10):
```

### 2. Issuing a Ticket
```text
--- [Issue New Queue Ticket] ---
Enter customer full name: Ada Lovelace
Enter phone number: +1-555-0101
Select Service Category:
  1. [TX] Teller / Cash Transactions
  2. [CS] Customer Service
  3. [LN] Loans & Credit Facilities
  4. [AC] Account Opening & KYC
Select category (1-4): 1

************************************************
               QUEUE TICKET ISSUED
************************************************
 Ticket Number:    TX-101
 Customer Name:    Ada Lovelace
 Service Category: [TX] Teller / Cash Transactions
 Position in Line: #1
 Issued At:        2026-11-19 11:24:00
************************************************
 Please take a seat. Your ticket will be called shortly.
```

### 3. Calling Next Customer to Counter
```text
--- [Call Next Customer] ---
Available Service Counters:
  Counter #1: Officer Alice Johnson (Counter 1 - General Teller) [FREE / READY]
  Counter #2: Officer Bob Smith (Counter 2 - Customer Service) [FREE / READY]

Enter your Counter # to call customer: 1
Select option: 1 (Call Next in Unified Queue)

======================================================
                 NOW CALLING...
======================================================
 TICKET NUMBER:    TX-101
 CUSTOMER:         Ada Lovelace
 SERVICE:          Teller / Cash Transactions
 PROCEED TO:       Counter #1 (Officer Alice Johnson)
 Customer Waited:  1m 45s
======================================================
```

### 4. Live Waiting Queue Board
```text
Total Customers in Queue: 3
============================================================================
Position  | Ticket     | Customer Name          | Category           | Waiting
----------------------------------------------------------------------------
#1        | TX-102     | Alan Turing            | Teller             | 2m 10s
#2        | CS-101     | Grace Hopper           | Customer Service   | 1m 30s
#3        | LN-101     | Katherine Johnson      | Loans & Credit     | 45s
============================================================================
```

### 5. Queue Analytics & Average Wait Time
```text
======================================================
             OVERALL QUEUE PERFORMANCE
======================================================
 Total Customers Served:                 24
 Average Waiting Time:                3m 12s (3.2 mins)
 Average Service Duration:            4m 45s (4.8 mins)
======================================================

--- Breakdown by Service Category ---
Category Code   | Served   | Avg Wait Time    | Avg Service Time
-----------------------------------------------------------------
[TX] Teller     |     14   |         1m 55s   |           3m 10s
[CS] Customer   |      6   |         4m 20s   |           6m 05s
[LN] Loans      |      4   |         6m 15s   |          10m 30s
-----------------------------------------------------------------
```

---

## 🧪 Testing

The repository includes automated unit tests in `test_queue.py`:
- Category and counter initial seeding
- Ticket issuance and incremental sequential numbering (`TX-101`, `TX-102`)
- FIFO queue ordering and counter assignment
- Busy counter collision prevention
- Service duration and wait time calculation
- Cancellation workflow and deque removal
- Live queue board and completed service queries
- Aggregate average waiting time analytics

Run tests:
```bash
python3 -m unittest test_queue.py
```
Output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.542s

OK
```
