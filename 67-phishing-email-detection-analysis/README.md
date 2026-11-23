# Project 67: Phishing Email Detection & Analysis Tool

A defensive email threat analysis and digital triage tool designed to parse RFC 822 `.eml` email files, extract headers, evaluate sender brand impersonation, detect deceptive hyperlinks, identify high-risk attachments, compute a weighted phishing risk score, and generate actionable investigation reports.

## Detection Rules & Indicators

- **Sender & Brand Spoofing**: Detects when the email display name mimics trusted brands ("PayPal", "Microsoft", "IT Support", "Bank") while the underlying RFC 822 address domain is hosted on unrelated, high-risk infrastructure.
- **Reply-To Mismatch**: Identifies situations where the `Reply-To` header directs responses to an unmonitored drop address different from the sender.
- **Urgency & Psychological Coercion**: Regex scanning across the subject line for panic-inducing keywords ("Account Suspended", "Action Required Immediately", "Wire Transfer Overdue").
- **Deceptive Hyperlink Parsing**:
  - Compares the visible anchor text with the underlying HTML `href` attribute to catch deceptive links (e.g. text displaying `https://paypal.com/verify` pointing to `http://198.51.100.22/phish`).
  - Detects raw IP address hosts in URLs.
  - Flags abused high-risk top-level domains (`.xyz`, `.top`, `.tk`, `.work`).
- **Dangerous & Weaponized Attachments**:
  - Double extensions (`.pdf.exe`, `.docx.vbs`).
  - Standalone executable binaries and scripts (`.exe`, `.scr`, `.vbs`, `.iso`, `.hta`).
  - Macro-enabled Office documents (`.docm`, `.xlsm`).

## Risk Verdicts

- **Low Risk** (Score 0–24): Standard email hygiene applies; no high-risk indicators detected.
- **Suspicious** (Score 25–59): Exhibits multiple risk factors; warrants out-of-band verification.
- **Phishing** (Score 60–100): High probability malicious social engineering attack; block and quarantine immediately.

## Database Schema

- `email_analyses`: Summary of parsed emails, subject lines, senders, risk scores, and verdicts.
- `phishing_indicators`: Granular threat indicators linked to each analysis with categories and severity levels.

## Running the Application

Launch the interactive CLI:

```bash
cd 67-phishing-email-detection-analysis
python3 main.py
```

Use options `2`, `3`, and `4` to test pre-packaged offline sample `.eml` emails (benign, credential phish, macro invoice).

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_phishing_detector.py -v
```
