"""
Log Normalization Engine.
Parses multi-source logs (Authentication, Web Access, Firewall Telemetry)
into a unified schema with synchronized timestamps and extracted identifiers.
"""
from datetime import datetime
import re
from typing import Optional, Dict, List, Any


class LogNormalizer:
    IP_REGEX = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    USER_PATTERNS = [
        re.compile(r"user[=:]\s*([a-zA-Z0-9_.-]+)", re.IGNORECASE),
        re.compile(r"for\s+(?:invalid\s+user\s+)?([a-zA-Z0-9_.-]+)\s+from", re.IGNORECASE),
        re.compile(r"username[=:]\s*([a-zA-Z0-9_.-]+)", re.IGNORECASE)
    ]

    TIMESTAMP_FORMATS = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%d/%b/%Y:%H:%M:%S %z",
        "%b %d %H:%M:%S",
    ]

    @classmethod
    def parse_timestamp(cls, raw_ts: str) -> tuple[str, float]:
        """Convert arbitrary timestamp string into standard ISO 'YYYY-MM-DD HH:MM:SS' and epoch."""
        cleaned = raw_ts.strip()
        now = datetime.now()

        for fmt in cls.TIMESTAMP_FORMATS:
            try:
                dt = datetime.strptime(cleaned, fmt)
                # If format has no year (e.g. syslog Nov 23 09:12:00)
                if "%Y" not in fmt and "%y" not in fmt:
                    dt = dt.replace(year=now.year)
                iso_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                return iso_str, dt.timestamp()
            except ValueError:
                continue

        # Fallback to current time
        return now.strftime("%Y-%m-%d %H:%M:%S"), now.timestamp()

    @classmethod
    def extract_ip(cls, text: str) -> Optional[str]:
        match = cls.IP_REGEX.search(text)
        return match.group(0) if match else None

    @classmethod
    def extract_username(cls, text: str) -> Optional[str]:
        for pat in cls.USER_PATTERNS:
            match = pat.search(text)
            if match:
                return match.group(1).strip()
        return None

    @classmethod
    def normalize_auth_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        raw_ts = str(record.get("timestamp", ""))
        iso_str, epoch = cls.parse_timestamp(raw_ts)

        ip = record.get("ip_address") or cls.extract_ip(str(record))
        user = record.get("username") or cls.extract_username(str(record))

        action_raw = str(record.get("action", "")).upper()
        if "FAIL" in action_raw or "INVALID" in action_raw or not record.get("success", True):
            action = "LOGIN_FAIL"
        else:
            action = "LOGIN_SUCCESS"

        return {
            "timestamp": iso_str,
            "epoch_time": epoch,
            "source_type": "Auth",
            "ip_address": ip,
            "username": user,
            "action": action,
            "details": record.get("message") or record.get("details", ""),
            "status_code": 401 if action == "LOGIN_FAIL" else 200,
            "bytes_transferred": 0
        }

    @classmethod
    def normalize_web_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        raw_ts = str(record.get("timestamp", ""))
        iso_str, epoch = cls.parse_timestamp(raw_ts)

        ip = record.get("ip_address") or cls.extract_ip(str(record))
        user = record.get("username") or cls.extract_username(str(record))
        status_code = int(record.get("status_code", 200))
        bytes_tx = int(record.get("bytes_transferred", record.get("bytes", 0)))
        path = record.get("path") or record.get("endpoint", "")
        method = record.get("method", "GET")

        return {
            "timestamp": iso_str,
            "epoch_time": epoch,
            "source_type": "Web",
            "ip_address": ip,
            "username": user,
            "action": "WEB_REQUEST",
            "details": f"{method} {path}",
            "status_code": status_code,
            "bytes_transferred": bytes_tx
        }

    @classmethod
    def normalize_firewall_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        raw_ts = str(record.get("timestamp", ""))
        iso_str, epoch = cls.parse_timestamp(raw_ts)

        src_ip = record.get("src_ip") or record.get("ip_address")
        action_raw = str(record.get("action", "ACCEPT")).upper()
        action = "FW_DROP" if "DROP" in action_raw or "DENY" in action_raw else "FW_ACCEPT"
        bytes_tx = int(record.get("bytes_transferred", record.get("bytes", 0)))
        dst_ip = record.get("dst_ip", "external")
        dst_port = record.get("dst_port", "")

        return {
            "timestamp": iso_str,
            "epoch_time": epoch,
            "source_type": "Firewall",
            "ip_address": src_ip,
            "username": record.get("username"),
            "action": action,
            "details": f"Traffic to {dst_ip}:{dst_port}",
            "status_code": 0,
            "bytes_transferred": bytes_tx
        }
