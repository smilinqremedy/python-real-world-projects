"""
Rule-based spam detection engine with privacy-conscious IP logging.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta


class SpamDetector:
    SPAM_THRESHOLD = 40  # Scores >= 40 are flagged as Suspicious

    @staticmethod
    def mask_ip(ip: str) -> str:
        """Privacy-conscious IP masking (e.g. 192.168.1.42 -> 192.168.1.***)."""
        if not ip:
            return "0.0.0.***"
        parts = ip.strip().split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
        # IPv6 fallback
        return ip[:8] + ":****:****"

    @staticmethod
    def hash_ip(ip: str) -> str:
        """One-way salted cryptographic hash of IP address for anonymous rate tracking."""
        salt = "PrivacySpamSalt_2026"
        return hashlib.sha256(f"{salt}_{ip.strip()}".encode("utf-8")).hexdigest()

    @staticmethod
    def validate_inputs(name: str, email: str, subject: str, message: str):
        if not name or len(name.strip()) < 2:
            raise ValueError("Sender name must be at least 2 characters.")
        if not subject or len(subject.strip()) < 2:
            raise ValueError("Subject is required.")
        if not message or len(message.strip()) < 5:
            raise ValueError("Message must be at least 5 characters long.")

        email_clean = email.strip()
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email_clean):
            raise ValueError(f"Invalid email address: '{email}'")

    @classmethod
    def analyze_submission(cls, subject: str, message: str, email: str, ip_hash: str,
                           db_conn, custom_rules: list = None) -> tuple[int, str, list[str]]:
        """
        Analyze form content against deterministic rules and activity logs.
        Returns (spam_score, classification, triggered_rules).
        """
        score = 0
        triggered = []
        combined_text = f"{subject} {message}".lower()

        # 1. Keyword rule checks from database
        rules = custom_rules
        if rules is None and db_conn:
            rules = [dict(r) for r in db_conn.execute("SELECT pattern, weight, category FROM spam_keywords").fetchall()]

        if rules:
            for rule in rules:
                pattern = rule["pattern"].lower()
                if pattern in combined_text:
                    score += rule["weight"]
                    triggered.append(f"Spam keyword match: '{rule['pattern']}' (+{rule['weight']} pts)")

        # 2. Excessive Links / Hyperlinks detection
        url_matches = re.findall(r"https?://[^\s]+|www\.[^\s]+", combined_text)
        if len(url_matches) >= 3:
            score += 40
            triggered.append(f"Excessive hyperlinks detected ({len(url_matches)} URLs found) (+40 pts)")
        elif len(url_matches) >= 1 and any(bad in combined_text for bad in [".ru", ".xyz", ".top", ".biz", ".click"]):
            score += 30
            triggered.append("Suspicious Top-Level Domain (TLD) link detected (+30 pts)")

        # 3. Aggressive uppercase lettering (SHOUTING)
        letters = [c for c in message if c.isalpha()]
        if len(letters) >= 20:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio >= 0.65:
                score += 20
                triggered.append(f"Excessive capitalization ({upper_ratio*100:.0f}% uppercase) (+20 pts)")

        # 4. Duplicate Message Detection (identical message body submitted recently)
        if db_conn:
            recent_dup = db_conn.execute(
                """
                SELECT count(*) FROM form_submissions
                WHERE lower(message) = lower(?) AND submitted_at >= datetime('now', '-2 hour')
                """,
                (message.strip(),),
            ).fetchone()[0]
            if recent_dup > 0:
                score += 40
                triggered.append(f"Duplicate submission detected (sent {recent_dup} times in last 2 hours) (+40 pts)")

            # 5. IP Velocity Check (repeated submissions from same anonymized IP)
            ip_velocity = db_conn.execute(
                """
                SELECT count(*) FROM form_submissions
                WHERE ip_hash = ? AND submitted_at >= datetime('now', '-10 minute')
                """,
                (ip_hash,),
            ).fetchone()[0]
            if ip_velocity >= 3:
                score += 35
                triggered.append(f"High-frequency submission from same IP ({ip_velocity} requests in 10 mins) (+35 pts)")

        # Cap score between 0 and 100
        final_score = min(100, max(0, score))
        classification = "Suspicious" if final_score >= cls.SPAM_THRESHOLD else "Genuine"

        return final_score, classification, triggered
