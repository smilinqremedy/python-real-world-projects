# Project 63: Security Incident Response Management System

An incident response tracking and coordination platform built with Python OOP and SQLite, adhering to NIST SP 800-61 incident handling lifecycle standards. Manages role-based access control (RBAC), security analyst assignment, evidence locker management, audit logs, and post-mortem reporting.

## Incident Lifecycle (NIST SP 800-61 Aligned)

Incidents progress through controlled sequential containment and remediation phases:
1. **Reported**: Initial triage and classification of threat vector and severity (`Low`, `Medium`, `High`, `Critical`).
2. **Investigating**: Active forensic inquiry, scoping of affected assets, and root-cause analysis.
3. **Contained**: Short-term containment measures implemented (e.g. host isolation, credential resets, firewall blocks).
4. **Eradicated**: Threat components identified, backdoors removed, malware scrubbed.
5. **Recovered**: Systems restored to normal production operations and monitored for recurrence.
6. **Closed**: Final post-mortem lessons learned documented.

## Role-Based Access Control (RBAC)

- **Analyst**: Can log incidents, conduct investigations, append timeline notes, attach evidence items, and advance status through containment.
- **Lead**: Can assign lead investigators, advance all lifecycle stages, and authorize incident closure.
- **Admin**: Full administrative authority over users, incidents, and audit trails.

## Database Schema

- `users`: User profiles with roles (`Analyst`, `Lead`, `Admin`).
- `incidents`: Unique incident reference, title, severity, threat category, lifecycle status, assigned lead, and timestamps.
- `incident_notes`: Timestamped collaborative investigator notes.
- `evidence_records`: Artifact repository tracking logs, PCAPs, file hashes, disk images, and SHA-256 fingerprints.
- `audit_logs`: Immutable security audit log recording every transition, actor, and state delta.

## Running the Application

Launch the interactive CLI:

```bash
cd 63-security-incident-response-management
python3 main.py
```

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_incident_response.py -v
```
