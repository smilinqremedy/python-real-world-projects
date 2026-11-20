# Job Recruitment and Applicant Tracking System

A modular, relational Applicant Tracking System (ATS) and recruitment pipeline engine built in Python and SQLite for recruitment agencies, HR departments, and hiring managers.

---

## The Problem

Recruitment agencies and growing companies receive dozens of applications across diverse job openings and struggle to keep candidate resumes organized, avoid duplicate applications, track stages of the interview process, capture structured interviewer feedback, and analyze pipeline conversion metrics.

This system provides a structured ATS workflow supporting client company registrations, vacancy creation, candidate profiles, local CV document storage with type and size validation, interview scheduling, objective feedback scoring, and candidate search based on skills and experience.

---

## Key Features & Architecture

1. **Company & Vacancy Management**:
   - Register client companies and hiring organizations.
   - Post vacancies with salary ranges, required experience levels, and skill tags.

2. **Candidate Profiles & Skills Search**:
   - Candidate directory with contact info, current job title, verified experience, and skills.
   - Multi-token keyword search matching required skills and filtering by minimum years of experience.
   - **Ethical Recruitment Guarantee**: No automatic candidate rejections based on protected characteristics (gender, age, marital status, ethnicity). All advancement decisions are based strictly on objective skills, qualifications, and structured interview scores.

3. **Job Application Workflow & Duplicate Prevention**:
   - Unique application references formatted as `APP-YYYY-XXXX`.
   - Database-level unique constraint preventing duplicate applications by the same candidate for the same vacancy.

4. **CV Document Local Storage & Validation**:
   - Secure local document storage under `uploads/cvs/`.
   - File format whitelist: `.pdf`, `.docx`, `.doc`, `.txt`.
   - File size boundary checks: rejects empty files (0 bytes) and files larger than 5 MB.
   - SHA-256 integrity checksum verification.

5. **Mandatory Application Status Tracking**:
   - Tracks candidates strictly through the required stages:
     - `Submitted`
     - `Under Review`
     - `Shortlisted`
     - `Interview Scheduled`
     - `Accepted`
     - `Rejected`
   - Complete audit trail of all status transitions recorded in `application_history` with actor, timestamp, and notes.

6. **Interview Scheduling & Evaluation Feedback**:
   - Schedule interview rounds (`Phone Screen`, `Technical Interview`, `Behavioral Interview`, `Panel Interview`, `Final Round`).
   - Automatically moves candidate to `Interview Scheduled`.
   - Structured 1-5 evaluation scoring across Technical, Communication, and Problem Solving criteria with hiring recommendations (`Strong Hire`, `Hire`, `Hold`, `Reject`).

7. **Recruitment Analytics & Funnel Reporting**:
   - Full hiring funnel metrics from initial application to final acceptance.
   - Vacancy breakdown and interview performance analytics.

---

## How to Run the Application

Navigate to the project directory and launch the interactive CLI:

```bash
cd 43-job-recruitment-tracker
python3 main.py
```

### Pre-seeded Demo Credentials

| Role | Username | Password | Full Name | Organization |
|---|---|---|---|---|
| **Administrator** | `admin` | `AdminPass123!` | Agency Super Admin | Apex Recruitment |
| **Recruiter** | `recruiter.ngozi` | `RecruitPass123!` | Ngozi Okafor | Apex Recruitment |
| **Hiring Manager** | `hm.khalid` | `ManagerPass123!` | Khalid Danjuma | PayDirect Fintech |

---

## Running Automated Tests

Run the comprehensive unit test suite:

```bash
python3 -m unittest test_recruitment.py -v
```
