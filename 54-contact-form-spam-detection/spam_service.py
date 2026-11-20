"""
Service layer for Website Contact Form Spam Detection System.
"""
from datetime import datetime
import json
import secrets
from database import get_connection, init_db
from spam_detector import SpamDetector


class SpamDetectionService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    def submit_contact_form(self, sender_name: str, email: str, subject: str, message: str,
                            ip_address: str = "127.0.0.1") -> dict:
        """
        Ingest, validate, classify, and store a contact form submission.
        Does NOT delete flagged messages; records them for admin audit.
        """
        SpamDetector.validate_inputs(sender_name, email, subject, message)

        ip_hash = SpamDetector.hash_ip(ip_address)
        masked_ip = SpamDetector.mask_ip(ip_address)

        conn = self._get_connection()
        try:
            with conn:
                score, classification, triggered = SpamDetector.analyze_submission(
                    subject, message, email, ip_hash, conn
                )

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                submission_ref = f"SUB-{today_str}-{seq}"

                cursor = conn.execute(
                    """
                    INSERT INTO form_submissions (
                        submission_ref, sender_name, email, subject, message,
                        ip_hash, masked_ip, spam_score, classification,
                        triggered_rules, admin_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending Review')
                    """,
                    (
                        submission_ref, sender_name.strip(), email.strip().lower(),
                        subject.strip(), message.strip(), ip_hash, masked_ip,
                        score, classification, json.dumps(triggered),
                    ),
                )

                return {
                    "submission_ref": submission_ref,
                    "sender_name": sender_name.strip(),
                    "email": email.strip().lower(),
                    "masked_ip": masked_ip,
                    "spam_score": score,
                    "classification": classification,
                    "triggered_rules": triggered,
                    "admin_status": "Pending Review",
                }
        finally:
            conn.close()

    def review_submission(self, submission_ref: str, decision: str) -> bool:
        """
        Admin review: update status to 'Confirmed Genuine' or 'Confirmed Spam'.
        """
        valid_decisions = ("Confirmed Genuine", "Confirmed Spam")
        if decision not in valid_decisions:
            raise ValueError(f"Decision must be one of: {', '.join(valid_decisions)}")

        conn = self._get_connection()
        try:
            with conn:
                res = conn.execute(
                    """
                    UPDATE form_submissions
                    SET admin_status = ?, reviewed_at = CURRENT_TIMESTAMP
                    WHERE submission_ref = ?
                    """,
                    (decision, submission_ref.strip().upper()),
                )
                if res.rowcount == 0:
                    raise ValueError(f"Submission '{submission_ref}' not found.")
                return True
        finally:
            conn.close()

    def get_submission(self, submission_ref: str) -> dict:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM form_submissions WHERE submission_ref = ?",
                (submission_ref.strip().upper(),),
            ).fetchone()
            if not row:
                raise ValueError(f"Submission '{submission_ref}' not found.")
            data = dict(row)
            data["triggered_rules"] = json.loads(data["triggered_rules"]) if data.get("triggered_rules") else []
            return data
        finally:
            conn.close()

    def list_submissions(self, classification: str = None, admin_status: str = None) -> list[dict]:
        conn = self._get_connection()
        try:
            clauses = []
            params = []
            if classification:
                clauses.append("classification = ?")
                params.append(classification)
            if admin_status:
                clauses.append("admin_status = ?")
                params.append(admin_status)

            where_str = f"WHERE {' AND '.join(clauses)}" if clauses else ""
            rows = conn.execute(
                f"SELECT * FROM form_submissions {where_str} ORDER BY submitted_at DESC LIMIT 50",
                params,
            ).fetchall()

            results = []
            for r in rows:
                item = dict(r)
                item["triggered_rules"] = json.loads(item["triggered_rules"]) if item.get("triggered_rules") else []
                results.append(item)
            return results
        finally:
            conn.close()

    def get_spam_statistics(self) -> dict:
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT count(*) FROM form_submissions").fetchone()[0]
            genuine = conn.execute("SELECT count(*) FROM form_submissions WHERE classification = 'Genuine'").fetchone()[0]
            suspicious = conn.execute("SELECT count(*) FROM form_submissions WHERE classification = 'Suspicious'").fetchone()[0]

            pending_review = conn.execute("SELECT count(*) FROM form_submissions WHERE admin_status = 'Pending Review'").fetchone()[0]
            confirmed_spam = conn.execute("SELECT count(*) FROM form_submissions WHERE admin_status = 'Confirmed Spam'").fetchone()[0]

            avg_score = conn.execute("SELECT coalesce(avg(spam_score), 0.0) FROM form_submissions").fetchone()[0]

            return {
                "total_submissions": total,
                "genuine_count": genuine,
                "suspicious_count": suspicious,
                "spam_rate_percent": round((suspicious / total) * 100, 1) if total > 0 else 0.0,
                "pending_review_count": pending_review,
                "confirmed_spam_count": confirmed_spam,
                "average_spam_score": round(avg_score, 1),
            }
        finally:
            conn.close()
