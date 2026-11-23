"""
Threat Hunting & Security Log Correlation Engine.
Correlates events across authentication, web application, and firewall telemetry
to detect multi-stage attack patterns (Brute Force, Recon-to-Access, Data Exfiltration).
"""
import re
from typing import Optional, Dict, List, Any
from collections import defaultdict
from database import get_connection, init_db
from normalizer import LogNormalizer


class ThreatHunter:
    RECON_PATH_REGEX = re.compile(r"(\/admin|\/login|union\s+select|\/etc\/passwd|\.\.\/|cmd\.exe|wp-login|\/api\/v\d+\/auth)", re.IGNORECASE)

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    def ingest_logs(self, records: List[Dict[str, Any]], source_type: str) -> int:
        """
        Normalize and insert log records into SQLite.
        """
        conn = self._get_connection()
        count = 0
        try:
            with conn:
                for r in records:
                    if source_type == "Auth":
                        norm = LogNormalizer.normalize_auth_record(r)
                    elif source_type == "Web":
                        norm = LogNormalizer.normalize_web_record(r)
                    elif source_type == "Firewall":
                        norm = LogNormalizer.normalize_firewall_record(r)
                    else:
                        continue

                    conn.execute(
                        """
                        INSERT INTO normalized_logs (timestamp, epoch_time, source_type, ip_address, username, action, details, status_code, bytes_transferred)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (norm["timestamp"], norm["epoch_time"], norm["source_type"], norm["ip_address"],
                         norm["username"], norm["action"], norm["details"], norm["status_code"], norm["bytes_transferred"])
                    )
                    count += 1
            return count
        finally:
            conn.close()

    def run_correlation(self) -> List[Dict[str, Any]]:
        """
        Correlate normalized logs across sources to identify attack patterns.
        """
        conn = self._get_connection()
        findings = []

        try:
            with conn:
                all_logs = conn.execute(
                    "SELECT * FROM normalized_logs ORDER BY epoch_time ASC"
                ).fetchall()
                logs = [dict(r) for r in all_logs]

                # Group logs by IP address
                ip_events = defaultdict(list)
                for log in logs:
                    if log["ip_address"]:
                        ip_events[log["ip_address"]].append(log)

                # ==================== Rule 1: Brute Force Attacks ====================
                for ip, events in ip_events.items():
                    fail_events = [e for e in events if e["action"] == "LOGIN_FAIL"]
                    if len(fail_events) >= 5:
                        # Check window: <= 300 seconds
                        time_span = fail_events[-1]["epoch_time"] - fail_events[0]["epoch_time"]
                        if time_span <= 300 or len(fail_events) >= 5:
                            users_targeted = list(set(e["username"] for e in fail_events if e["username"]))
                            timeline = " -> ".join([f"[{e['timestamp']}] Fail: {e['username'] or 'unknown'}" for e in fail_events[:5]])

                            threat = {
                                "title": "Repeated Authentication Failure / Password Spraying",
                                "severity": "High",
                                "rule_id": "BRUTE_FORCE_01",
                                "ip_address": ip,
                                "username": ", ".join(users_targeted) if users_targeted else None,
                                "first_seen": fail_events[0]["timestamp"],
                                "last_seen": fail_events[-1]["timestamp"],
                                "event_count": len(fail_events),
                                "timeline_summary": timeline,
                                "investigation_notes": f"IP address generated {len(fail_events)} failed login attempts targeting account(s): {', '.join(users_targeted)}."
                            }
                            findings.append(threat)

                # ==================== Rule 2: Web Reconnaissance to Auth Compromise ====================
                for ip, events in ip_events.items():
                    recon_events = [e for e in events if e["source_type"] == "Web" and self.RECON_PATH_REGEX.search(e["details"])]
                    login_successes = [e for e in events if e["action"] == "LOGIN_SUCCESS"]

                    for r_ev in recon_events:
                        for l_ev in login_successes:
                            delta = l_ev["epoch_time"] - r_ev["epoch_time"]
                            if 0 <= delta <= 600:  # within 10 minutes
                                timeline = f"[{r_ev['timestamp']}] Web Probe: {r_ev['details']} -> [{l_ev['timestamp']}] Successful Auth as '{l_ev['username']}'"
                                threat = {
                                    "title": "Web Reconnaissance Followed by Successful Authentication",
                                    "severity": "Critical",
                                    "rule_id": "RECON_TO_ACCESS_02",
                                    "ip_address": ip,
                                    "username": l_ev["username"],
                                    "first_seen": r_ev["timestamp"],
                                    "last_seen": l_ev["timestamp"],
                                    "event_count": 2,
                                    "timeline_summary": timeline,
                                    "investigation_notes": f"Attacker probed administrative web endpoints from {ip} and successfully authenticated as '{l_ev['username']}' {int(delta)} seconds later."
                                }
                                findings.append(threat)
                                break

                # ==================== Rule 3: Compromise to High-Volume Exfiltration ====================
                for ip, events in ip_events.items():
                    login_successes = [e for e in events if e["action"] == "LOGIN_SUCCESS"]
                    large_egress = [e for e in events if e["source_type"] == "Firewall" and e["action"] == "FW_ACCEPT" and e["bytes_transferred"] >= 100_000]

                    for l_ev in login_successes:
                        for fw_ev in large_egress:
                            delta = fw_ev["epoch_time"] - l_ev["epoch_time"]
                            if 0 <= delta <= 900:  # within 15 minutes
                                timeline = f"[{l_ev['timestamp']}] Auth Success: {l_ev['username']} -> [{fw_ev['timestamp']}] Egress Transfer: {fw_ev['bytes_transferred']:,} bytes ({fw_ev['details']})"
                                threat = {
                                    "title": "Post-Authentication High-Volume Data Exfiltration",
                                    "severity": "Critical",
                                    "rule_id": "EXFILTRATION_03",
                                    "ip_address": ip,
                                    "username": l_ev["username"],
                                    "first_seen": l_ev["timestamp"],
                                    "last_seen": fw_ev["timestamp"],
                                    "event_count": 2,
                                    "timeline_summary": timeline,
                                    "investigation_notes": f"Host authenticated as '{l_ev['username']}' and initiated large egress transfer of {fw_ev['bytes_transferred']:,} bytes."
                                }
                                findings.append(threat)
                                break

                # Save findings into correlated_threats table
                for f in findings:
                    conn.execute(
                        """
                        INSERT INTO correlated_threats (title, severity, rule_id, ip_address, username, first_seen, last_seen, event_count, timeline_summary, investigation_notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (f["title"], f["severity"], f["rule_id"], f["ip_address"], f["username"],
                         f["first_seen"], f["last_seen"], f["event_count"], f["timeline_summary"], f["investigation_notes"])
                    )

            return findings
        finally:
            conn.close()

    def search_threats(self, ip_address: Optional[str] = None,
                       username: Optional[str] = None,
                       severity: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            query = "SELECT * FROM correlated_threats WHERE 1=1"
            params = []
            if ip_address:
                query += " AND ip_address = ?"
                params.append(ip_address.strip())
            if username:
                query += " AND username LIKE ?"
                params.append(f"%{username.strip()}%")
            if severity:
                query += " AND severity = ?"
                params.append(severity.strip().capitalize())

            query += " ORDER BY id DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_timeline_for_ip(self, ip_address: str) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM normalized_logs WHERE ip_address = ? ORDER BY epoch_time ASC",
                (ip_address.strip(),)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_threat_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total_logs = conn.execute("SELECT count(*) FROM normalized_logs").fetchone()[0]
            total_threats = conn.execute("SELECT count(*) FROM correlated_threats").fetchone()[0]
            sev_counts = conn.execute(
                "SELECT severity, count(*) as count FROM correlated_threats GROUP BY severity"
            ).fetchall()

            return {
                "total_normalized_logs": total_logs,
                "correlated_threats_identified": total_threats,
                "threats_by_severity": {r["severity"]: r["count"] for r in sev_counts}
            }
        finally:
            conn.close()
