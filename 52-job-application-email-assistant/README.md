# Automated Job Application Email Assistant

A modular Python and SQLite application to organize job vacancies, compile customized cover letter application emails from reusable templates, attach CV documents, and track application outcomes with a strict preview-and-confirmation safety gate.

---

## Key Features

1. **Company & Vacancy Directory**:
   - Store target employers, recruitment contact emails, job listing links, and salary ranges.
2. **Template Compilation**:
   - Dynamic variable substitution (`{company}`, `{job_title}`, `{recruiter_name}`, `{candidate_name}`, `{candidate_skills}`, `{years_experience}`).
3. **MIME Attachments**:
   - Attach PDF/DOCX resume files securely with file existence validation.
4. **Mandatory Preview & Confirmation**:
   - Displays rendered subject, recipient, body, and attachment before sending.
   - **Safety Enforcement**: Enforces an affirmative confirmation check; never transmits emails without explicit user authorization.
5. **Environment-Based SMTP Security**:
   - SMTP host, port, credentials, and sender info configured via environment variables (`.env.example`).
   - Supports dry-run simulation mode when credentials are not configured.
6. **Application Tracking**:
   - Logs sent emails, updates vacancy statuses (`Saved` -> `Applied` -> `Interviewing`), and provides funnel activity reports.

---

## Running the Application

```bash
cd 52-job-application-email-assistant
python3 main.py
```

---

## Running Automated Tests

```bash
python3 -m unittest test_assistant.py -v
```
