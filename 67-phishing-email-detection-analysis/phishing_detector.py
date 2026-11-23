"""
Phishing Email Detection & Threat Analysis Engine.
Parses RFC 822 .eml emails, evaluates sender brand impersonation, deceptive hyperlinks,
urgency cues, and dangerous attachments to assign phishing risk scores.
"""
import os
import re
from urllib.parse import urlparse
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from typing import Dict, List, Optional, Any
from database import get_connection, init_db


class PhishingDetector:
    URGENCY_PATTERN = re.compile(
        r"\b(urgent|immediate|suspended|restricted|action required|verify your account|overdue|wire transfer|security notice|unauthorized access|password expires?)\b",
        re.IGNORECASE
    )
    SUSPICIOUS_TLDS = {".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".buzz", ".work", ".click"}
    DANGEROUS_ATTACHMENT_EXTENSIONS = {
        ".exe", ".scr", ".vbs", ".bat", ".cmd", ".ps1", ".iso", ".hta", ".pif", ".dll"
    }
    MACRO_ATTACHMENT_EXTENSIONS = {".docm", ".xlsm", ".pptm", ".dotm", ".xltm"}
    COMMON_SPOOFED_BRANDS = [
        "paypal", "microsoft", "office365", "apple", "google", "amazon", "netflix",
        "dhl", "fedex", "bank", "it support", "security dept", "helpdesk"
    ]

    URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
    HTML_LINK_REGEX = re.compile(r'<a\s+(?:[^>]*?\s+)?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.IGNORECASE)

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    def analyze_eml_bytes(self, raw_bytes: bytes, filename: str = "uploaded_email.eml") -> Dict[str, Any]:
        """Parse raw email bytes and run phishing threat analysis."""
        msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
        return self._evaluate_message(msg, filename)

    def analyze_eml_file(self, file_path: str) -> Dict[str, Any]:
        """Read and analyze a local .eml file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Email file not found: {file_path}")
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
        return self.analyze_eml_bytes(raw_bytes, os.path.basename(file_path))

    def _evaluate_message(self, msg, filename: str) -> Dict[str, Any]:
        subject = str(msg.get("Subject", "")).strip()
        from_raw = str(msg.get("From", "")).strip()
        reply_to_raw = str(msg.get("Reply-To", "")).strip()
        date_header = str(msg.get("Date", "")).strip()

        display_name, sender_email = parseaddr(from_raw)
        _, reply_to_email = parseaddr(reply_to_raw)

        indicators = []
        risk_score = 0

        # ---------------- 1. Sender & Brand Spoofing Check ----------------
        display_lower = display_name.lower()
        sender_lower = sender_email.lower()
        sender_domain = sender_lower.split("@")[-1] if "@" in sender_lower else ""

        for brand in self.COMMON_SPOOFED_BRANDS:
            if brand in display_lower and brand not in sender_domain:
                risk_score += 35
                indicators.append({
                    "category": "Sender Spoofing",
                    "severity": "High",
                    "description": f"Display name invokes brand '{brand.title()}', but actual sending domain is '{sender_domain}'."
                })
                break

        # Check Reply-To divergence
        if reply_to_email and sender_email and reply_to_email.lower() != sender_lower:
            risk_score += 20
            indicators.append({
                "category": "Sender Spoofing",
                "severity": "Medium",
                "description": f"Reply-To address '{reply_to_email}' diverges from From address '{sender_email}'."
            })

        # Check Suspicious Sender TLD
        for tld in self.SUSPICIOUS_TLDS:
            if sender_domain.endswith(tld):
                risk_score += 15
                indicators.append({
                    "category": "Sender Spoofing",
                    "severity": "Medium",
                    "description": f"Sender domain '{sender_domain}' uses high-risk or commonly abused TLD '{tld}'."
                })
                break

        # ---------------- 2. Subject Urgency / Coercion Analysis ----------------
        if self.URGENCY_PATTERN.search(subject):
            risk_score += 15
            indicators.append({
                "category": "Urgency Manipulation",
                "severity": "Medium",
                "description": f"Subject line contains psychological urgency or coercion keywords ('{subject}')."
            })

        # ---------------- 3. Body Text & Deceptive URL Extraction ----------------
        body_text = ""
        html_text = ""

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    try:
                        body_text += part.get_content()
                    except Exception:
                        pass
                elif ctype == "text/html":
                    try:
                        html_text += part.get_content()
                    except Exception:
                        pass
        else:
            ctype = msg.get_content_type()
            if ctype == "text/html":
                html_text = msg.get_content()
            else:
                body_text = msg.get_content()

        # Check Deceptive HTML Hyperlinks
        found_links = []
        if html_text:
            for match in self.HTML_LINK_REGEX.finditer(html_text):
                href = match.group(1).strip()
                visible_text = match.group(2).strip()
                found_links.append(href)

                # Deceptive anchor: visible text looks like https://company.com but href goes elsewhere
                if visible_text.startswith("http://") or visible_text.startswith("https://"):
                    vis_parsed = urlparse(visible_text)
                    href_parsed = urlparse(href)
                    if vis_parsed.netloc and href_parsed.netloc and vis_parsed.netloc != href_parsed.netloc:
                        risk_score += 35
                        indicators.append({
                            "category": "Suspicious Link",
                            "severity": "Critical",
                            "description": f"Deceptive hyperlink detected! Displayed text points to '{vis_parsed.netloc}', but actual href destination redirects to '{href_parsed.netloc}'."
                        })

        # Search plaintext links
        for m in self.URL_REGEX.finditer(body_text):
            found_links.append(m.group(0))

        # Inspect all URLs for IP hosts and suspicious TLDs
        for link in set(found_links):
            parsed = urlparse(link)
            host = parsed.netloc.split(":")[0]

            # IP host check (e.g. http://198.51.100.22/...)
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host):
                risk_score += 25
                indicators.append({
                    "category": "Suspicious Link",
                    "severity": "High",
                    "description": f"URL uses raw numeric IP address '{host}' instead of a registered domain name."
                })

            for tld in self.SUSPICIOUS_TLDS:
                if host.endswith(tld):
                    risk_score += 15
                    indicators.append({
                        "category": "Suspicious Link",
                        "severity": "Medium",
                        "description": f"URL destination domain '{host}' uses high-risk TLD '{tld}'."
                    })

        # ---------------- 4. Attachment Analysis ----------------
        attachments_found = []
        for part in msg.iter_attachments():
            att_name = part.get_filename() or "unnamed_attachment"
            attachments_found.append(att_name)
            name_lower = att_name.lower()
            ext = os.path.splitext(name_lower)[1]

            # Double extension check (e.g. invoice.pdf.exe)
            if re.search(r"\.(pdf|docx?|xlsx?)\.(exe|scr|vbs|bat|ps1|hta)$", name_lower):
                risk_score += 45
                indicators.append({
                    "category": "Dangerous Attachment",
                    "severity": "Critical",
                    "description": f"Attachment '{att_name}' utilizes deceptive double extension masking executable code as a document."
                })
            elif ext in self.DANGEROUS_ATTACHMENT_EXTENSIONS:
                risk_score += 40
                indicators.append({
                    "category": "Dangerous Attachment",
                    "severity": "Critical",
                    "description": f"Attachment '{att_name}' has dangerous executable or script format ('{ext}')."
                })
            elif ext in self.MACRO_ATTACHMENT_EXTENSIONS:
                risk_score += 25
                indicators.append({
                    "category": "Dangerous Attachment",
                    "severity": "High",
                    "description": f"Attachment '{att_name}' is a macro-enabled Office file ('{ext}') frequently used in weaponized email campaigns."
                })

        final_score = min(100, risk_score)

        if final_score >= 60:
            verdict = "Phishing"
        elif final_score >= 25:
            verdict = "Suspicious"
        else:
            verdict = "Low Risk"

        # ---------------- 5. Store in SQLite Database ----------------
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO email_analyses (filename, subject, sender_display, sender_email, reply_to, date_header, risk_score, verdict)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (filename, subject, display_name, sender_email, reply_to_email, date_header, final_score, verdict)
                )
                analysis_id = cursor.lastrowid

                for ind in indicators:
                    conn.execute(
                        """
                        INSERT INTO phishing_indicators (analysis_id, category, severity, description)
                        VALUES (?, ?, ?, ?)
                        """,
                        (analysis_id, ind["category"], ind["severity"], ind["description"])
                    )

            return {
                "analysis_id": analysis_id,
                "filename": filename,
                "subject": subject,
                "sender_display": display_name,
                "sender_email": sender_email,
                "reply_to": reply_to_email,
                "risk_score": final_score,
                "verdict": verdict,
                "attachments_found": attachments_found,
                "indicators": indicators,
                "recommendation": self._get_recommendation(verdict)
            }
        finally:
            conn.close()

    @staticmethod
    def _get_recommendation(verdict: str) -> str:
        if verdict == "Phishing":
            return "BLOCK & PURGE: High probability of targeted social engineering. Quarantine email, block sender domain/IP at gateway, and reset compromised credentials if links were clicked."
        elif verdict == "Suspicious":
            return "CAUTION / INVESTIGATE: Email exhibits multiple risk signals. Do not open attachments or click links until verified via out-of-band communication with sender."
        return "LOW RISK: No blatant phishing characteristics detected. Standard email hygiene still applies."

    def get_analysis_history(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM email_analyses ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
