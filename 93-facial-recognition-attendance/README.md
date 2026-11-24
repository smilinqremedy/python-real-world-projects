# Project 93: AI-Powered Facial Recognition Attendance System

## Ethical Framework, Privacy Protection & Legal Compliance

> [!IMPORTANT]
> **BIOMETRIC DATA PROTECTION & ETHICAL ASSURANCES:**
> 1. **No Covert Surveillance:** Biometric verification is initiated solely with the explicit participation and knowledge of the subject.
> 2. **Zero Raw Image Storage:** Raw facial photos are NEVER permanently stored on disk or in the database. Only one-way, irreversible 128-dimensional mathematical feature embeddings are persisted.
> 3. **Mandatory Informed Consent:** Enrollment strictly requires authenticated informed consent.
> 4. **Equitable Manual Alternative:** Any participant who cannot or does not wish to use facial recognition is guaranteed an identical manual attendance alternative without penalty.
> 5. **Comprehensive Auditability:** All enrollment events, check-ins, manual corrections, and administrator overrides are logged to an immutable SQLite audit trail.

---

## Overview

The **AI-Powered Facial Recognition Attendance System** provides an enterprise-ready biometric check-in solution engineered with strict data protection and role-based access control.

Key capabilities include:
- **Biometric Matching Engine:** 128-dimensional normalized facial feature vectors compared via Cosine Similarity.
- **Duplicate Prevention:** Database-enforced `UNIQUE(session_id, participant_id)` prevents accidental or fraudulent multiple check-ins.
- **Manual Alternative Mode:** Full support for non-biometric participants using employee ID lookup.
- **Administrative Correction:** Documented status overrides with mandatory justification audit trails.
- **Reporting & Export:** Daily, weekly, and monthly attendance reports with one-click CSV export.

---

## Architecture

```text
93-facial-recognition-attendance/
├── app.py                     # Streamlit web portal (Check-in, registration, reports)
├── attendance_service.py      # Core service layer (matching, check-in, duplicate prevention)
├── auth.py                    # PBKDF2-HMAC-SHA256 password security & RBAC
├── biometrics.py              # 128-dim embedding extractor & cosine matcher
├── database.py                # SQLite schema, transactions & audit logging
├── main.py                    # Command-line interface
├── reporter.py                # Attendance aggregations & CSV export
├── requirements.txt           # Dependencies
├── test_facial_attendance.py  # Automated unit test suite
└── README.md                  # Documentation & privacy specification
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 93-facial-recognition-attendance
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Create Administrator User
```bash
python3 main.py --create-admin admin SecureAdmin@2026
```

### 2. Create an Attendance Session
```bash
python3 main.py --create-session MORNING_SHIFT "Morning Standup" "2026-11-24"
```

### 3. Register a Participant (With Informed Consent)
- **Biometric enrollment:**
  ```bash
  python3 main.py --register-participant EMP-101 "Alice Smith" "Engineering" "alice@example.com" --photo alice.jpg
  ```
- **Manual alternative (biometric opt-out):**
  ```bash
  python3 main.py --register-participant EMP-102 "Bob Jones" "Marketing" "bob@example.com" --opt-out-bio
  ```

### 4. Record Attendance
- **Via Face Verification:**
  ```bash
  python3 main.py --checkin-face MORNING_SHIFT alice_checkin.jpg
  ```
- **Via Manual Alternative:**
  ```bash
  python3 main.py --checkin-manual MORNING_SHIFT EMP-102
  ```

### 5. Generate Report & Export CSV
```bash
python3 main.py --report MORNING_SHIFT --export-csv morning_attendance.csv
```

### 6. Launch the Streamlit Portal
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_facial_attendance.py -v
```
