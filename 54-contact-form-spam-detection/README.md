# Website Contact Form Spam Detection System

A rule-based spam detection and submission classification engine built in Python and SQLite to protect web contact forms from bot traffic, unsolicited commercial messages, phishing, and link-farming.

---

## Architectural Principles & Security Design

1. **Rule-Based Multi-Layer Scoring**:
   - Evaluates keyword patterns across financial fraud, crypto giveaways, SEO backlink services, phishing, and aggressive sales pitches.
   - Excessive hyperlink detection ($N \ge 3$ URLs or suspicious TLDs).
   - Aggressive capitalization / shouting ratios.
   - Duplicate message submission detection within rolling time windows.
   - IP request velocity tracking.

2. **No Automatic Deletion (Audit Safeguard)**:
   - High-scoring messages are **never automatically deleted** to prevent permanent loss of false positives.
   - Suspicious submissions are flagged and queued for human administrator review (`Pending Review` $\to$ `Confirmed Genuine` or `Confirmed Spam`).

3. **Privacy-Conscious IP Handling**:
   - Protects user privacy by masking IP octets (`192.168.1.***`) before display and database persistence.
   - Employs a one-way cryptographic salted hash (`ip_hash`) for frequency checks without storing cleartext IP addresses.

---

## Running the Application

```bash
cd 54-contact-form-spam-detection
python3 main.py
```

---

## Running Automated Tests

```bash
python3 -m unittest test_spam_detector.py -v
```
