"""
Core business logic and notification engine for the Automated Email Notification System.
"""
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import hashlib
from database import get_connection, init_db


class EmailService:
    def __init__(self, db_path=None, test_mode=None):
        self.db_path = db_path
        init_db(self.db_path)

        # Environment configuration
        if test_mode is not None:
            self.test_mode = test_mode
        else:
            env_test = os.getenv("EMAIL_TEST_MODE", "true").lower()
            self.test_mode = env_test in ("true", "1", "yes")

        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_from = os.getenv("SMTP_FROM", "noreply@business.com")
        self.smtp_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")

        # Configurable failure simulation hook for testing
        self.simulate_network_failure = False

    def _get_connection(self):
        return get_connection(self.db_path)

    @staticmethod
    def validate_email(email):
        """Strict email RFC-compliant format validation."""
        if not email or not isinstance(email, str):
            raise ValueError("Email address cannot be empty.")
        clean_email = email.strip()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$"
        if not re.match(pattern, clean_email):
            raise ValueError(f"Invalid email address format: '{email}'")
        return clean_email.lower()

    # ==================== Recipient Management ====================

    def register_recipient(self, name, email, consent_status="subscribed"):
        clean_name = name.strip()
        clean_email = self.validate_email(email)
        clean_consent = consent_status.strip().lower()

        if not clean_name:
            raise ValueError("Recipient name is required.")
        if clean_consent not in ("subscribed", "unsubscribed"):
            raise ValueError("Consent status must be 'subscribed' or 'unsubscribed'.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO recipients (name, email, consent_status) VALUES (?, ?, ?)",
                    (clean_name, clean_email, clean_consent)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Recipient with email '{clean_email}' already exists.")
            raise
        finally:
            conn.close()

    def update_consent(self, email, consent_status):
        clean_email = self.validate_email(email)
        clean_consent = consent_status.strip().lower()
        if clean_consent not in ("subscribed", "unsubscribed"):
            raise ValueError("Consent status must be 'subscribed' or 'unsubscribed'.")

        conn = self._get_connection()
        try:
            with conn:
                updated = conn.execute(
                    "UPDATE recipients SET consent_status = ? WHERE email = ?",
                    (clean_consent, clean_email)
                ).rowcount
                if updated == 0:
                    raise ValueError(f"Recipient '{clean_email}' not found.")
                return True
        finally:
            conn.close()

    def get_recipient(self, email):
        clean_email = self.validate_email(email)
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM recipients WHERE email = ?", (clean_email,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_recipients(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM recipients ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Reusable Email Templates ====================

    def create_template(self, name, subject_template, body_template, description=""):
        name = name.strip().lower().replace(" ", "_")
        subject = subject_template.strip()
        body = body_template.strip()

        if not name or not subject or not body:
            raise ValueError("Template name, subject template, and body template are required.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO templates (name, subject_template, body_template, description) VALUES (?, ?, ?, ?)",
                    (name, subject, body, description.strip())
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Template '{name}' already exists.")
            raise
        finally:
            conn.close()

    def get_template(self, name):
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM templates WHERE name = ?", (name.strip().lower(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_templates(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM templates ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def render_template(self, template_name, context):
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Email template '{template_name}' not found.")

        try:
            subject = template["subject_template"].format(**context)
            body = template["body_template"].format(**context)
            return {"subject": subject, "body": body}
        except KeyError as e:
            raise ValueError(f"Missing required placeholder value for template: {e}")

    # ==================== Notification Scheduling & Queue ====================

    def _generate_idempotency_key(self, email, subject, scheduled_at_str):
        raw = f"{email}|{subject}|{scheduled_at_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def queue_email(self, recipient_email, subject, body,
                    scheduled_at=None, template_name=None,
                    idempotency_key=None, max_retries=3):
        clean_email = self.validate_email(recipient_email)
        subject = subject.strip()
        body = body.strip()

        if not subject or not body:
            raise ValueError("Email subject and body are required.")

        # Consent and Subscription Check
        recipient = self.get_recipient(clean_email)
        recipient_name = recipient["name"] if recipient else clean_email
        if recipient and recipient["consent_status"] == "unsubscribed":
            raise ValueError(f"Recipient {clean_email} has opted out/unsubscribed from notifications.")

        sched_dt = scheduled_at or datetime.now()
        sched_str = sched_dt.isoformat()

        # Deduplication / Idempotency
        key = idempotency_key or self._generate_idempotency_key(clean_email, subject, sched_str)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("""
                    INSERT INTO email_queue (
                        recipient_email, recipient_name, template_name,
                        subject, body, scheduled_at, status,
                        idempotency_key, max_retries
                    ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                """, (
                    clean_email, recipient_name, template_name,
                    subject, body, sched_str, key, max_retries
                ))
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Duplicate email prevented by idempotency rule: key='{key}'")
            raise
        finally:
            conn.close()

    def send_templated_email(self, recipient_email, template_name, context, scheduled_at=None):
        rendered = self.render_template(template_name, context)
        return self.queue_email(
            recipient_email=recipient_email,
            subject=rendered["subject"],
            body=rendered["body"],
            scheduled_at=scheduled_at,
            template_name=template_name
        )

    # ==================== Dispatch Engine & Retry Mechanism ====================

    def _dispatch_single_email(self, recipient_email, subject, body):
        """Low-level dispatch handling SMTP transmission or mock test mode."""
        if self.simulate_network_failure:
            raise smtplib.SMTPConnectError(421, "Simulated network timeout connecting to SMTP server")

        if self.test_mode:
            # Test Mode: simulate delivery and return mock status
            return {
                "success": True,
                "mode": "mock_test",
                "message": f"[TEST MODE] Email simulated to {recipient_email}: '{subject}'"
            }

        # Real SMTP Transmission
        msg = MIMEMultipart()
        msg["From"] = self.smtp_from
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = None
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            if self.smtp_tls:
                server.starttls()
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            return {
                "success": True,
                "mode": "smtp",
                "message": f"Successfully delivered via SMTP to {recipient_email}"
            }
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def process_queue(self, current_time=None):
        """Process all pending emails whose scheduled time has arrived."""
        now = current_time or datetime.now()
        now_str = now.isoformat()

        conn = self._get_connection()
        try:
            pending_items = conn.execute("""
                SELECT * FROM email_queue
                WHERE status = 'pending' AND scheduled_at <= ?
                ORDER BY scheduled_at ASC
            """, (now_str,)).fetchall()

            processed = 0
            succeeded = 0
            failed = 0

            for item in pending_items:
                item_id = item["id"]
                recipient = item["recipient_email"]
                subject = item["subject"]
                body = item["body"]
                retry_count = item["retry_count"]
                max_retries = item["max_retries"]

                # Double check consent prior to dispatch
                recip_row = conn.execute("SELECT consent_status FROM recipients WHERE email = ?", (recipient,)).fetchone()
                if recip_row and recip_row["consent_status"] == "unsubscribed":
                    with conn:
                        conn.execute("UPDATE email_queue SET status = 'cancelled', last_error = 'Recipient unsubscribed' WHERE id = ?", (item_id,))
                        conn.execute("""
                            INSERT INTO email_logs (queue_id, recipient_email, subject, status, delivery_mode, error_message, attempt_number)
                            VALUES (?, ?, ?, 'failed', 'blocked', 'Consent revoked / unsubscribed', ?)
                        """, (item_id, recipient, subject, retry_count + 1))
                    failed += 1
                    continue

                processed += 1
                try:
                    res = self._dispatch_single_email(recipient, subject, body)
                    # Success
                    with conn:
                        status_val = "simulated" if res["mode"] == "mock_test" else "sent"
                        conn.execute("""
                            UPDATE email_queue
                            SET status = 'sent', sent_at = ?, last_error = NULL
                            WHERE id = ?
                        """, (now_str, item_id))

                        conn.execute("""
                            INSERT INTO email_logs (queue_id, recipient_email, subject, status, delivery_mode, error_message, attempt_number)
                            VALUES (?, ?, ?, ?, ?, NULL, ?)
                        """, (item_id, recipient, subject, status_val, res["mode"], retry_count + 1))
                    succeeded += 1
                except Exception as ex:
                    # Failure - trigger retry policy
                    new_retry = retry_count + 1
                    err_msg = str(ex)
                    new_status = "failed" if new_retry >= max_retries else "pending"

                    with conn:
                        conn.execute("""
                            UPDATE email_queue
                            SET status = ?, retry_count = ?, last_error = ?
                            WHERE id = ?
                        """, (new_status, new_retry, err_msg, item_id))

                        conn.execute("""
                            INSERT INTO email_logs (queue_id, recipient_email, subject, status, delivery_mode, error_message, attempt_number)
                            VALUES (?, ?, ?, 'failed', 'error', ?, ?)
                        """, (item_id, recipient, subject, err_msg, new_retry))
                    failed += 1

            return {
                "processed": processed,
                "succeeded": succeeded,
                "failed": failed
            }
        finally:
            conn.close()

    def send_instant(self, recipient_email, subject, body, template_name=None):
        qid = self.queue_email(recipient_email, subject, body, template_name=template_name)
        result = self.process_queue()
        return {"queue_id": qid, "dispatch_summary": result}

    # ==================== Reporting & Activity History ====================

    def get_history(self, recipient_email=None, limit=50):
        conn = self._get_connection()
        try:
            if recipient_email:
                clean_email = self.validate_email(recipient_email)
                rows = conn.execute("""
                    SELECT * FROM email_logs
                    WHERE recipient_email = ?
                    ORDER BY id DESC, sent_at DESC LIMIT ?
                """, (clean_email, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM email_logs
                    ORDER BY id DESC, sent_at DESC LIMIT ?
                """, (limit,)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def generate_activity_report(self):
        conn = self._get_connection()
        try:
            total_recipients = conn.execute("SELECT COUNT(*) as cnt FROM recipients").fetchone()["cnt"]
            unsubscribed = conn.execute("SELECT COUNT(*) as cnt FROM recipients WHERE consent_status = 'unsubscribed'").fetchone()["cnt"]

            queue_counts = conn.execute("""
                SELECT status, COUNT(*) as cnt
                FROM email_queue
                GROUP BY status
            """).fetchall()
            q_map = {r["status"]: r["cnt"] for r in queue_counts}

            log_counts = conn.execute("""
                SELECT status, COUNT(*) as cnt
                FROM email_logs
                GROUP BY status
            """).fetchall()
            l_map = {r["status"]: r["cnt"] for r in log_counts}

            total_attempts = sum(l_map.values())
            success_logs = l_map.get("sent", 0) + l_map.get("simulated", 0)
            deliverability = round((success_logs / total_attempts * 100) if total_attempts > 0 else 0.0, 2)

            return {
                "total_recipients": total_recipients,
                "unsubscribed_recipients": unsubscribed,
                "queue_pending": q_map.get("pending", 0),
                "queue_sent": q_map.get("sent", 0),
                "queue_failed": q_map.get("failed", 0),
                "queue_cancelled": q_map.get("cancelled", 0),
                "total_attempts": total_attempts,
                "successful_deliveries": success_logs,
                "failed_deliveries": l_map.get("failed", 0),
                "deliverability_rate_pct": deliverability,
                "test_mode_active": self.test_mode
            }
        finally:
            conn.close()
