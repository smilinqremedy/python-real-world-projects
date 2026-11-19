# Hospital Appointment Management System

A robust, relational command-line appointment booking and patient record management system developed in Python and SQLite for medical clinics.

---

## 📌 Problem the Project Solves

Small medical clinics and healthcare practices frequently rely on paper logbooks, phone registers, or unindexed spreadsheets to book patient appointments. This causes critical operational issues:
- **Overlapping Bookings (Double Booking)**: Multiple patients are scheduled with the same doctor at the same time, leading to crowded waiting rooms, prolonged delays, and patient frustration.
- **Lost & Disorganized Medical Records**: Inability to quickly access a patient's historical consultations, diagnoses, and cancellation patterns.
- **Inefficient Schedule Visibility**: Clinic staff cannot determine at a glance which time slots remain open for a physician on a given date.
- **Untracked Appointment Lifecycle**: Lack of clear status transitions (Scheduled $\rightarrow$ Completed $\rightarrow$ Cancelled) leads to missed follow-ups and unutilized clinic capacity.

The **Hospital Appointment Management System** eliminates scheduling collisions using relational database constraints, dynamic availability computations, and structured lifecycle tracking.

---

## 🎯 Project Objectives

- **Eliminate Double-Booking**: Enforce partial unique indexing at the SQLite database layer and application pre-checks to guarantee that no two patients can book the same doctor at the same time.
- **Streamline Scheduling & Rescheduling**: Provide real-time availability checks where booked slots are dynamically subtracted from the clinic's standard consultation hours.
- **Maintain Patient Appointment Histories**: Deliver centralized, relational lookups for all past, present, and cancelled visits by Patient ID.
- **Clean Architecture & Separation of Concerns**: Structure the codebase into decoupled layers (Database, Service/Business Logic, Models/Exceptions, and CLI Interface).
- **Zero-Configuration Deployment**: Automatically initialize database schemas, relational foreign keys, and default fictional clinic staff on initial startup.

---

## 🗄 Database Design & Entity Relationships

The system utilizes SQLite with foreign key enforcement (`PRAGMA foreign_keys = ON;`) across three core relational tables:

```
┌────────────────────────────────┐       ┌────────────────────────────────┐
│            PATIENTS            │       │            DOCTORS             │
├────────────────────────────────┤       ├────────────────────────────────┤
│ PK  patient_id   TEXT          │       │ PK  doctor_id    INTEGER AUTO  │
│     full_name    TEXT NOT NULL │       │     full_name    TEXT NOT NULL │
│     date_of_birth TEXT NOT NULL│       │     specialty    TEXT NOT NULL │
│     gender       TEXT NOT NULL │       │     phone_number TEXT          │
│     phone_number TEXT NOT NULL │       │     email        TEXT          │
│     email        TEXT          │       │     is_active    INTEGER (1)   │
│     created_at   TEXT NOT NULL │       └──────────────┬─────────────────┘
└──────────────┬─────────────────┘                      │
               │                                        │
               │ 1                                      │ 1
               │                                        │
               │         ┌──────────────────────┐       │
               └───────► │     APPOINTMENTS     │ ◄─────┘
                       N ├──────────────────────┤ N
                         │ PK  appointment_id   │
                         │ FK  patient_id  TEXT │
                         │ FK  doctor_id   INT  │
                         │     appointment_date │
                         │     time_slot        │
                         │     reason           │
                         │     status           │
                         │     created_at       │
                         │     updated_at       │
                         └──────────────────────┘
```

### Conflict Prevention via Partial Unique Index
To guarantee that active appointments never overlap while allowing cancelled slots to be reused by other patients, SQLite enforces a partial unique index:

```sql
CREATE UNIQUE INDEX idx_unique_active_doctor_slot
ON appointments(doctor_id, appointment_date, time_slot)
WHERE status = 'scheduled';
```

---

## ⚙️ Appointment Scheduling Algorithm

1. **Doctor Availability Algorithm**:
   - Given `doctor_id` and `appointment_date`:
   - Query all appointments where `status = 'scheduled'`.
   - $\text{Available Slots} = \text{Standard Slots} \setminus \text{Booked Slots}$.
2. **Scheduling Collision Avoidance**:
   - Verify `patient_id` exists in `patients` table.
   - Verify `doctor_id` exists in `doctors` table.
   - Verify requested `time_slot` belongs to standard clinic consultation hours.
   - Check if doctor already has an active appointment at `(doctor_id, date, time_slot)` $\rightarrow$ raise `DoctorUnavailableError`.
   - Check if patient already has another active appointment at `(patient_id, date, time_slot)` $\rightarrow$ raise `PatientConflictError`.
   - Insert record with `status = 'scheduled'`.
3. **Rescheduling & Cancellation**:
   - Rescheduling atomically updates `date` and `time_slot` after verifying the new slot's availability.
   - Cancellation transitions status to `'cancelled'`, automatically freeing up the time slot for other patients.

---

## ✨ Features

1. **Register Patients**: Assigns unique chronological IDs (`PAT-YYYY-NNN`) and stores demographics.
2. **Register Doctors**: Catalogs doctors alongside clinical specialties (Cardiology, Pediatrics, General Medicine, etc.).
3. **Check Doctor Availability**: Displays available and booked slots for any doctor on any date.
4. **Schedule Appointments**: Books consultations with automated collision checks.
5. **Conflict Prevention**: Rejects any booking that attempts to double-book a doctor or patient.
6. **Reschedule Appointments**: Transfers appointments to new dates and times while releasing prior slots.
7. **Cancel Appointments**: Marks bookings as cancelled, immediately releasing the slot.
8. **Track Appointment Status**: Manages appointment states (`scheduled`, `completed`, `cancelled`).
9. **Display Daily Schedule**: Displays all clinic consultations for a given calendar day.
10. **Patient Appointment History**: Comprehensive search displaying all past, upcoming, and cancelled visits.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Database**: SQLite 3 (Built into Python standard library)
- **Standard Library Modules**:
  - `sqlite3`: Relational database storage, queries, and constraints.
  - `datetime`: Date/time parsing and ISO timestamping.
  - `unittest`: Automated unit and integration test suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Hospital-Appointment-Management-System/
├── database.py       # SQLite connection manager, table schema creation, and seeding
├── exceptions.py     # Custom domain exceptions (DoctorUnavailableError, ValidationError, etc.)
├── service.py        # Business logic: scheduling algorithm, availability, conflict checks
├── main.py           # Interactive CLI interface
├── test_hospital.py  # Automated unit and integration test suite
├── .gitignore        # Git exclusion rules
└── README.md         # Project documentation and user manual
```

---

## 🚀 Installation Instructions

### Prerequisites
- Python 3.8 or higher installed. Verify with:
  ```bash
  python3 --version
  ```

### Clone the Repository
```bash
git clone https://github.com/smilinqremedy/Hospital-Appointment-Management-System.git
cd Hospital-Appointment-Management-System
```

*(No third-party packages or database servers required. SQLite runs embedded out of the box).*

---

## 💻 How to Run the Application

Launch the command-line application:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_hospital.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
========================================================
   HOSPITAL APPOINTMENT MANAGEMENT SYSTEM (CLI)   
========================================================
 1. Register New Patient
 2. Register New Doctor & Specialty
 3. View All Doctors & Specialties
 4. Check Doctor Availability
 5. Schedule New Appointment
 6. Reschedule Appointment
 7. Cancel Appointment
 8. Mark Appointment as Completed
 9. Display Clinic Appointments by Date
 10. Search Patient Appointment History
 11. View All Registered Patients
 12. Exit Application
========================================================
Enter your choice (1-12):
```

### 2. Checking Doctor Availability
```text
--- [Check Doctor Availability] ---
Enter Doctor ID: 1
Enter appointment date (YYYY-MM-DD): 2026-11-25

=======================================================
 AVAILABILITY FOR DR. SARAH JENKINS (Cardiology)
 Date: 2026-11-25
=======================================================
 Available Slots (13 free):
   09:30, 10:00, 10:30, 11:00, 11:30, 13:00, 13:30, 14:00, 14:30, 15:00, 15:30, 16:00, 16:30

 Already Booked (1 slots):
   09:00
=======================================================
```

### 3. Conflict Prevention Alert
When a patient tries to book a slot that is already taken:
```text
[Operation Failed] Conflict detected: Dr. Sarah Jenkins is already booked on 2026-11-25 at 09:00.
```

### 4. Appointment Confirmation
```text
=======================================================
            APPOINTMENT CONFIRMATION
=======================================================
 Appointment ID:   1
 Patient:          John Doe (PAT-2026-001)
 Doctor:           Dr. Sarah Jenkins (Cardiology)
 Date & Time:      2026-11-25 at 10:00
 Reason:           Routine Cardiac Follow-up
 Status:           SCHEDULED
=======================================================
```

### 5. Daily Clinic Appointments Schedule
```text
=====================================================================================
                  APPOINTMENTS SCHEDULE FOR 2026-11-25
=====================================================================================
ID    | Time    | Patient Name         | Doctor Name            | Specialty      | Status
-------------------------------------------------------------------------------------
1     | 09:00   | Jane Smith           | Dr. Sarah Jenkins      | Cardiology     | SCHEDULED
2     | 10:00   | John Doe             | Dr. Sarah Jenkins      | Cardiology     | SCHEDULED
3     | 10:30   | Robert Taylor        | Dr. Marcus Vance       | Pediatrics     | SCHEDULED
=====================================================================================
```

---

## 🧪 Testing

The repository contains automated unit and integration tests in `test_hospital.py` verifying:
- Schema initialization and seeding
- Patient and doctor registration
- Availability calculation
- Prevention of double-booking for doctors and patients
- Rescheduling workflow and slot recovery
- Cancellation lifecycle and slot release
- Appointment history query by patient ID

Run the test suite:
```bash
python3 -m unittest test_hospital.py
```
Output:
```text
...........
----------------------------------------------------------------------
Ran 11 tests in 0.892s

OK
```
