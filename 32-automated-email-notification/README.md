# Automated Email Notification System

An automated, reliable email dispatch and scheduling platform built in Python and SQLite for managing customer notifications, reminders, payment receipts, and marketing communications.

## Problem Statement

Businesses frequently encounter challenges when managing automated customer communications:
- Manual emails are labor-intensive, error-prone, and inconsistent.
- Network timeouts, transient SMTP connection failures, and provider throttling drop critical customer communications.
- Accidental duplicate notifications annoy clients and damage sender reputation.
- Hardcoded SMTP credentials pose serious security vulnerabilities.
- Inability to verify recipient consent and honor unsubscribes leads to compliance violations.

This application provides a production-ready solution featuring template rendering, scheduled queuing, automatic retries with backoff, strict idempotency enforcement, recipient consent management, and a mock test mode.

---

## Features

1. **Strict Email Validation**: RFC-compliant regex validation of customer email syntax.
2. **Recipient Consent Management**: Opt-in/opt-out status tracking (`subscribed` vs. `unsubscribed`) with automatic dispatch blocking for unsubscribed contacts.
3. **Reusable Email Templates**: Dynamic templates with variable interpolation (e.g. `{name}`, `{date}`, `{amount}`).
4. **Instant & Scheduled Dispatch**: Send emails immediately or schedule them for future release.
5. **Deduplication & Idempotency**: SHA-256 fingerprinting prevents accidental duplicate notification sends.
6. **Resilient Retry Handling**: Automatic retry tracking on transient SMTP and network connection failures.
7. **Simulation & Test Mode**: Dry-run simulation mode allows end-to-end testing without external network dependencies or risk of spamming real users.
8. **Comprehensive Audit Logs**: Every delivery attempt, failure code, and dispatch latency is permanently audited.
9. **Deliverability Analytics**: Aggregate reporting detailing deliverability rates, queue statuses, and failure breakdowns.
10. **Environment Variable Configuration**: Zero hardcoded credentials, configured via environment variables and `.env`.

---

## Architecture & Database Schema

The system persists records in an SQLite database (`notifications.db`):
- `recipients`: Name, email (unique), consent status (`subscribed`, `unsubscribed`).
- `templates`: Name (unique), subject template, body template, description.
- `email_queue`: Pending and scheduled email queue with idempotency keys, retry counts, and status tracking (`pending`, `sent`, `failed`, `cancelled`).
- `email_logs`: Historical audit trail logging each delivery attempt, timestamp, delivery mode (`smtp` vs `mock_test`), and error diagnostics.

---

## Configuration & Environment Variables

Copy `.env.example` to `.env` and configure your SMTP provider:
```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | Hostname of SMTP server | `localhost` |
| `SMTP_PORT` | Port of SMTP server | `587` |
| `SMTP_USER` | SMTP authentication username | `""` |
| `SMTP_PASSWORD` | SMTP authentication password | `""` |
| `SMTP_FROM` | Sender email address | `noreply@business.com` |
| `SMTP_USE_TLS` | Enable STARTTLS encryption | `true` |
| `EMAIL_TEST_MODE`| Run in dry-run simulation mode | `true` |

> **Security Note**: `.env` is ignored by git in `.gitignore`. Never commit real SMTP credentials to version control.

---

## How to Run

### Interactive CLI
```bash
python3 main.py
```

### Automated Unit Tests
```bash
python3 -m unittest test_email.py
```
