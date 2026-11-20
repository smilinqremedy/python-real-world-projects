"""
SMTP client and MIME message builder.
Reads email credentials securely from environment variables.
"""
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import re
import smtplib


class EmailSender:
    def __init__(self):
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.example.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.sender_email = os.environ.get("SENDER_EMAIL", "applicant@example.com")
        self.sender_name = os.environ.get("SENDER_NAME", "Job Applicant")

    @staticmethod
    def validate_email(email_str: str):
        if not email_str or not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email_str.strip()):
            raise ValueError(f"Invalid email address: '{email_str}'")

    def build_message(self, recipient_email: str, subject: str, body: str, attachment_path: str = None) -> MIMEMultipart:
        self.validate_email(recipient_email)
        self.validate_email(self.sender_email)

        msg = MIMEMultipart()
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = recipient_email.strip()
        msg["Subject"] = subject.strip()

        msg.attach(MIMEText(body, "plain", "utf-8"))

        if attachment_path:
            if not os.path.exists(attachment_path):
                raise FileNotFoundError(f"CV attachment file not found at: {attachment_path}")

            filename = os.path.basename(attachment_path)
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)
            part["Content-Disposition"] = f'attachment; filename="{filename}"'
            msg.attach(part)

        return msg

    def send(self, recipient_email: str, subject: str, body: str, attachment_path: str = None, dry_run: bool = False) -> dict:
        """
        Send application email via SMTP.
        If dry_run is True or mock environment detected, performs full validation without actual network transmission.
        """
        msg = self.build_message(recipient_email, subject, body, attachment_path)

        # Check if dry run or credentials not set
        is_live_smtp = bool(self.smtp_user and self.smtp_password and not dry_run)

        if not is_live_smtp:
            return {
                "success": True,
                "mode": "Dry Run / Simulation",
                "recipient": recipient_email,
                "subject": subject,
                "attachment": os.path.basename(attachment_path) if attachment_path else None,
                "message": "Validated and prepared message successfully. SMTP dispatch simulated.",
            }

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return {
                "success": True,
                "mode": "Live SMTP",
                "recipient": recipient_email,
                "subject": subject,
                "attachment": os.path.basename(attachment_path) if attachment_path else None,
                "message": "Email transmitted successfully.",
            }
        except Exception as e:
            raise RuntimeError(f"Failed to transmit email via SMTP: {e}")
