"""
Generator for safe synthetic .eml test emails.
Includes benign corporate communications and simulated phishing scenarios.
"""
from email.message import EmailMessage


def create_benign_email() -> bytes:
    msg = EmailMessage()
    msg["From"] = "Engineering Team <newsletter@company.internal>"
    msg["To"] = "employee@company.internal"
    msg["Subject"] = "Weekly Engineering Digest - November 2026"
    msg["Date"] = "Mon, 23 Nov 2026 08:30:00 +0000"
    msg["Message-ID"] = "<digest-101@company.internal>"

    body = """Hello Team,

Here is our weekly summary of completed platform updates and upcoming maintenance schedules:
- Python 3.12 runtime migration completed.
- Database maintenance scheduled for Sunday at 02:00 UTC.

Visit our internal wiki at https://wiki.company.internal/updates for full details.

Best regards,
Engineering Team
"""
    msg.set_content(body)
    return msg.as_bytes()


def create_credential_phish_email() -> bytes:
    msg = EmailMessage()
    # Display name says 'PayPal Security Dept', but actual address is from suspicious domain
    msg["From"] = "PayPal Security Support <security-alert@service-paypal-verify.xyz>"
    msg["To"] = "victim@company.internal"
    msg["Reply-To"] = "harvest@phish-collector.top"
    msg["Subject"] = "URGENT: Your Account Has Been Suspended - Action Required Immediately!"
    msg["Date"] = "Mon, 23 Nov 2026 09:12:00 +0000"
    msg["Message-ID"] = "<fraud-alert-999@service-paypal-verify.xyz>"

    html_body = """<html>
<body>
    <h2>Dear Valued Customer,</h2>
    <p>We detected unauthorized login attempts from IP 185.220.101.5. Your account has been temporarily restricted.</p>
    <p>You must confirm your identity within 24 hours to prevent permanent account suspension.</p>
    <p>Please click here to verify your account:
       <a href="http://198.51.100.22/paypal-login.php">https://www.paypal.com/security/login-verify</a>
    </p>
    <p>Alternatively, open the attached verification form.</p>
</body>
</html>"""
    msg.set_content("Please enable HTML to view this message.")
    msg.add_alternative(html_body, subtype="html")

    # Add dangerous double extension attachment
    msg.add_attachment(
        b"Simulated non-executable payload buffer",
        maintype="application",
        subtype="octet-stream",
        filename="Security_Verification_Form.pdf.exe"
    )
    return msg.as_bytes()


def create_macro_invoice_phish() -> bytes:
    msg = EmailMessage()
    msg["From"] = "Accounts Receivable <billing@global-suppliers-billing.biz>"
    msg["To"] = "finance@company.internal"
    msg["Subject"] = "OVERDUE PAYMENT NOTICE: Invoice #INV-88912 Overdue for Wire Transfer"
    msg["Date"] = "Mon, 23 Nov 2026 09:45:00 +0000"

    body = """Dear Accounts Payable,

Please find attached overdue invoice #INV-88912. Payment is past due.
Kindly remit payment via wire transfer immediately to avoid legal escalation.

Review the attached macro-enabled invoice spreadsheet for remittance details.
"""
    msg.set_content(body)
    msg.add_attachment(
        b"Simulated harmless macro spreadsheet data",
        maintype="application",
        subtype="vnd.ms-excel.sheet.macroEnabled.12",
        filename="Overdue_Invoice_88912.xlsm"
    )
    return msg.as_bytes()
