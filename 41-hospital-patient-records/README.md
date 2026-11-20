# Hospital Patient Records Management System

A secure, role-based healthcare information and patient records management application built in Python and SQLite for small hospitals, private clinics, and healthcare centers.

---

## The Problem

Small hospitals and clinics often struggle with fragmented paperwork, uncoordinated patient registration, appointment scheduling conflicts, disorganized clinical history, and insecure storage of patient information. Manual tracking risks medical errors, duplicate patient identifiers, unauthorized access to sensitive records, and lack of accountability.

This system provides a structured, role-based platform enforcing unique patient identification, audit logging, strict input validation, clinical notes documentation, appointment tracking, and administrative analytics while protecting sensitive patient health information.

---

## Architectural Principles & Security Design

1. **Role-Based Access Control (RBAC)**:
   - `Admin`: User account management, full system access, administrative reports, immutable security audit logs.
   - `Doctor`: Patient lookup, comprehensive medical chart review, clinical encounter documentation, vital sign reviews, consultation notes.
   - `Nurse`: Patient check-in, vital signs recording (with automatic BMI calculation), appointment schedule review.
   - `Receptionist`: Patient demographics registration, contact updates, appointment scheduling, conflict resolution, visit check-in.
   - `Billing Officer`: Patient demographic lookup, invoice generation, payment processing, financial collection tracking.

2. **Patient Privacy & Sensitive Data Protection**:
   - Application logs sanitize sensitive information, masking phone numbers (`***-***-1234`) and emails (`j***e@domain.com`).
   - Audit trail stores actions, timestamps, and resource identifiers without logging sensitive clinical text or cleartext credentials.
   - Passwords securely hashed with PBKDF2-HMAC-SHA256 and unique 16-byte random salts.

3. **Collision-Free Identification**:
   - Unique patient IDs formatted as `PAT-YYYYMMDD-XXXX` enforced with database-level `UNIQUE` constraints and collision checks.
   - Duplicate patient prevention based on combined first name, last name, date of birth, and phone number.

4. **Clinical Documentation Guardrails**:
   - Supports subjective complaints, objective physical findings, clinical assessment, and care plans.
   - **Explicit Policy**: Does not implement automated diagnosis or prescribe medication. All clinical assessment and care plans are direct human documentation by licensed medical professionals.

---

## Database Architecture

The system stores persistent data in `hospital_records.db` with strict foreign key constraints:

- `users`: Staff credentials, PBKDF2 hash + salt, RBAC role, active status.
- `patients`: Patient demographics, emergency contacts, blood group, allergies, chronic conditions.
- `appointments`: Scheduled consultations, doctor assignments, department, conflict prevention.
- `visits`: Inpatient, outpatient, emergency, and follow-up clinical encounter tracking.
- `vital_signs`: Blood pressure, heart rate, temperature, respiratory rate, SpO2, height, weight, automatic BMI.
- `clinical_notes`: Authorized SOAP documentation (Subjective, Objective, Assessment, Plan).
- `billing_invoices`: Invoicing, payments, and balance tracking.
- `audit_logs`: Immutable security audit trail recording user, action, target resource, and sanitized metadata.

---

## How to Run the Application

Navigate to the project directory and launch the interactive CLI:

```bash
cd 41-hospital-patient-records
python3 main.py
```

### Pre-seeded Demo Credentials

| Role | Username | Password | Full Name | Department |
|---|---|---|---|---|
| **Admin** | `admin` | `AdminPass123!` | Hospital Super Admin | Administration |
| **Doctor** | `dr.chidi` | `DoctorPass123!` | Dr. Chidi Okafor, MD | Cardiology |
| **Doctor** | `dr.aisha` | `DoctorPass123!` | Dr. Aisha Bello, MD | General Medicine |
| **Nurse** | `nurse.amaka` | `NursePass123!` | Nurse Amaka Okonkwo, RN | Outpatient Triage |
| **Receptionist** | `rec.fatima` | `RecepPass123!` | Fatima Aliyu | Front Desk |
| **Billing** | `bill.emeka` | `BillingPass123!` | Emeka Eze | Accounts |

---

## Running Automated Tests

Run the test suite using Python's standard `unittest` framework:

```bash
python3 -m unittest test_hospital.py -v
```
