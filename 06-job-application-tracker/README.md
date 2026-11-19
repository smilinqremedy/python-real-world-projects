# Job Application Tracker

A streamlined, command-line career management and interview pipeline tracker developed in Python with JSON storage to organize job hunts, schedule upcoming interviews, and visualize conversion funnel statistics.

---

## 📌 Problem the Project Solves

During an active job search, candidates submit tens or hundreds of applications across various job boards, portals, and company websites. Without a dedicated tracking system, job seekers experience:
- **Disorganized Pipelines**: Forgetting where and when applications were submitted, leading to unprepared initial phone screens.
- **Missed Interviews & Deadlines**: Overlooking scheduled technical screenings or online assessments.
- **Fragmented Context**: Scrambling to find original job descriptions and application URLs once recruiter outreach begins.
- **No Visibility into Conversion Rates**: Inability to identify whether drop-offs occur at the resume review, technical interview, or offer stage.

The **Job Application Tracker** provides a structured, lightweight, and offline CLI solution that organizes your job search into clear pipeline stages (`Applied`, `Assessment`, `Interview`, `Offered`, `Rejected`) with automated funnel analytics.

---

## 🎯 Project Objectives

- **Centralized Pipeline Management**: Consolidate company names, job titles, application dates, descriptions, and job URLs in one accessible local repository.
- **Stage Progression**: Effortlessly transition applications through standard hiring stages with timestamps.
- **Interview Accountability**: Track upcoming interviews and filter chronologically to ensure zero missed meetings.
- **Funnel Analytics**: Calculate interview rates, offer conversion rates, and rejection benchmarks to identify optimization areas in your search.
- **Data Privacy & Portability**: Completely offline, file-backed JSON persistence requiring zero cloud accounts or third-party tracking.

---

## 🗄 Data Structure Design (JSON)

Job applications are stored in `applications.json` using a clean, extensible document structure:

```json
{
  "applications": [
    {
      "id": 1,
      "company": "Stripe",
      "job_title": "Backend Software Engineer",
      "application_date": "2026-11-19",
      "job_description": "Building high-throughput payment infrastructure and distributed APIs.",
      "application_link": "https://stripe.com/jobs/12345",
      "status": "Interview",
      "interview_date": "2026-11-26 14:00",
      "notes": "Technical screening with the engineering hiring manager.",
      "created_at": "2026-11-19 09:30:00",
      "updated_at": "2026-11-21 16:45:00"
    }
  ]
}
```

---

## ⚙️ Core Algorithms & Pipeline Analytics

1. **Unique Incremental ID Assignment**:
   $$\text{Next ID} = \max(\{a.\text{id} \mid a \in \text{applications}\}) + 1 \quad (\text{or } 1 \text{ if empty})$$
2. **Upcoming Interviews Chronological Filter**:
   $$\text{Upcoming} = \{a \in \text{applications} \mid a.\text{status} = \text{'Interview'} \land a.\text{interview\_date} \ge \text{Today}\}$$
   Sorted in ascending chronological order ($\text{Earliest} \rightarrow \text{Latest}$).
3. **Funnel Conversion Rates**:
   $$\text{Interview Conversion Rate} = \frac{\text{Interviews} + \text{Offered}}{\text{Total Applications}} \times 100$$
   $$\text{Offer Rate} = \frac{\text{Offered}}{\text{Total Applications}} \times 100$$
   $$\text{Rejection Rate} = \frac{\text{Rejected}}{\text{Total Applications}} \times 100$$
   $$\text{Active Pipeline} = \text{Applied} + \text{Assessment} + \text{Interview}$$

---

## ✨ Features

1. **Add Job Applications**: Record company name, job title, application date, description, and link.
2. **Structured Stage Tracking**:
   - `Applied`: Application submitted.
   - `Assessment`: Take-home project or online assessment received.
   - `Interview`: Screening or technical loop scheduled.
   - `Offered`: Formal offer received.
   - `Rejected`: Application closed or passed on.
3. **Interview Scheduling**: Record interview dates and times (`YYYY-MM-DD` or `YYYY-MM-DD HH:MM`).
4. **Status Progression**: Transition applications between stages with note-taking support.
5. **Company Search**: Case-insensitive substring search to instantly locate specific opportunities.
6. **Upcoming Interviews Agenda**: Chronological calendar view of all forthcoming interviews.
7. **Total Applications Calculation**: Summary of total applications submitted and active pipeline volume.
8. **Success & Funnel Statistics**: Visual distribution bars, interview conversion rates, and offer ratios.
9. **Resilient JSON Persistence**: Automatic serialization with fault-tolerant recovery for missing or corrupted files.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Standard Library Modules**:
  - `json`: Data serialization and file persistence.
  - `datetime`: Date validation, parsing, and upcoming interview filtering.
  - `os`: File existence checks and path management.
  - `unittest`: Automated test suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Job-Application-Tracker/
├── tracker.py       # Core business logic: CRUD operations, validation, search, funnel metrics
├── main.py          # Interactive command-line interface
├── test_tracker.py  # Automated unit test suite
├── .gitignore       # Git exclusion rules
└── README.md        # Project documentation and user manual
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
git clone https://github.com/smilinqremedy/Job-Application-Tracker.git
cd Job-Application-Tracker
```

*(No third-party pip dependencies are required. Runs with standard Python).*

---

## 💻 How to Run the Application

Launch the command-line interface:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_tracker.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
======================================================
      JOB APPLICATION TRACKING SYSTEM (CLI)       
======================================================
 1. Add New Job Application
 2. View All Applications Roster
 3. Update Application Status (Stage)
 4. Search Applications by Company
 5. View Upcoming Interviews
 6. View Application Funnel & Success Statistics
 7. View Detailed Application Profile
 8. Exit Application
======================================================
Enter your choice (1-8):
```

### 2. Applications Roster Table
```text
========================================================================================
ID   | Company              | Job Title              | Applied    | Status       | Interview
----------------------------------------------------------------------------------------
1    | Stripe               | Backend Engineer       | 2026-11-19 | Interview    | 2026-11-26 14:00
2    | Google               | Software Engineer II   | 2026-11-10 | Assessment   | -
3    | Amazon               | SDE I                  | 2026-11-01 | Offered      | 2026-11-15 10:00
========================================================================================
```

### 3. Upcoming Interviews Agenda
```text
================================================================================
Interview Date    | Company              | Job Title              | Notes
--------------------------------------------------------------------------------
2026-11-26 14:00  | Stripe               | Backend Engineer       | System design round
2026-11-30 11:00  | Datadog              | Distributed Systems Eng| Hiring manager chat
================================================================================
```

### 4. Funnel Conversion & Success Statistics
```text
======================================================
        APPLICATION SUCCESS & FUNNEL STATISTICS
======================================================
 Total Applications Submitted:            15
 Active Pipeline:                         10
------------------------------------------------------
 STAGE BREAKDOWN:
   Applied       :    5 ( 33.3%) ######
   Assessment    :    2 ( 13.3%) ##
   Interview     :    3 ( 20.0%) ####
   Offered       :    2 ( 13.3%) ##
   Rejected      :    3 ( 20.0%) ####
------------------------------------------------------
 Interview Rate (Interview+Offer):   33.3%
 Job Offer Rate:                     13.3%
 Rejection Rate:                     20.0%
======================================================
```

---

## 🧪 Testing

The repository contains automated unit tests in `test_tracker.py` validating:
- Application creation and ID auto-increment
- Field validation and date parsing (`YYYY-MM-DD` and `YYYY-MM-DD HH:MM`)
- Status updating and interview date logging
- Substring company searches
- Chronological upcoming interview filtering
- Funnel metric calculations (interview rate, offer rate, rejection rate)
- JSON serialization and recovery from corrupted data

Run tests:
```bash
python3 -m unittest test_tracker.py
```
Output:
```text
........
----------------------------------------------------------------------
Ran 8 tests in 0.063s

OK
```
