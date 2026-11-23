"""
NIDS Detection Engine & Rule Evaluator.
Performs passive network packet metadata extraction, anomaly detection,
sliding-window connection pattern analysis, and alert logging.
"""
import time
from datetime import datetime
from collections import defaultdict, deque
import logging
from typing import Optional, Dict, List, Any, Set
from database import get_connection, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NIDS")


class DetectionRules:
    def __init__(self,
                 port_scan_threshold: int = 6,
                 scan_window_seconds: float = 5.0,
                 packet_burst_threshold: int = 15,
                 burst_window_seconds: float = 3.0,
                 volume_threshold_bytes: int = 100_000,
                 volume_window_seconds: float = 5.0,
                 suspicious_ports: Optional[Dict[int, str]] = None,
                 blocked_ips: Optional[Set[str]] = None):
        self.port_scan_threshold = port_scan_threshold
        self.scan_window_seconds = scan_window_seconds
        self.packet_burst_threshold = packet_burst_threshold
        self.burst_window_seconds = burst_window_seconds
        self.volume_threshold_bytes = volume_threshold_bytes
        self.volume_window_seconds = volume_window_seconds
        self.suspicious_ports = suspicious_ports or {
            4444: "Metasploit / Reverse Shell Listener",
            31337: "Back Orifice Trojan Port",
            6667: "Suspicious IRC / C2 Traffic",
            1337: "Generic Threat Backdoor",
        }
        self.blocked_ips = blocked_ips or {"198.51.100.45", "203.0.113.99"}


class NIDSEngine:
    def __init__(self, rules: Optional[DetectionRules] = None, db_path: Optional[str] = None):
        self.rules = rules or DetectionRules()
        self.db_path = db_path
        init_db(self.db_path)

        # Sliding window state: src_ip -> deque of (timestamp, dst_port, packet_size, flags)
        self._traffic_history: Dict[str, deque] = defaultdict(deque)
        self._alerted_scans: Set[str] = set()

    def _get_connection(self):
        return get_connection(self.db_path)

    def log_alert(self, alert_type: str, severity: str, src_ip: str, dst_ip: Optional[str],
                  rule_triggered: str, description: str, timestamp: Optional[float] = None) -> int:
        ts = timestamp or time.time()
        dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        logger.warning(f"[SECURITY ALERT - {severity.upper()}] {alert_type} from {src_ip}: {description}")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO security_alerts (timestamp, datetime_str, alert_type, severity, src_ip, dst_ip, rule_triggered, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ts, dt_str, alert_type, severity, src_ip, dst_ip, rule_triggered, description)
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def process_packet(self, src_ip: str, dst_ip: str, protocol: str,
                       src_port: Optional[int], dst_port: Optional[int],
                       packet_size: int, flags: str = "", timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Process packet metadata, record network event in SQLite, and run intrusion detection rules.
        """
        ts = timestamp or time.time()
        dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Record Network Event
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO network_events (timestamp, datetime_str, src_ip, dst_ip, protocol, src_port, dst_port, packet_size, flags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ts, dt_str, src_ip, dst_ip, protocol, src_port, dst_port, packet_size, flags)
                )
        finally:
            conn.close()

        # 2. Maintain Sliding Window for src_ip
        q = self._traffic_history[src_ip]
        q.append((ts, dst_port, packet_size, flags))

        # Evict records older than max evaluation window (10 seconds)
        cutoff = ts - 10.0
        while q and q[0][0] < cutoff:
            q.popleft()

        triggered_alerts = []

        # Rule 1: Known Blocked / Malicious Threat Intel IP
        if src_ip in self.rules.blocked_ips:
            aid = self.log_alert(
                alert_type="Known Malicious Source IP",
                severity="Critical",
                src_ip=src_ip,
                dst_ip=dst_ip,
                rule_triggered="RULE_BLOCKED_IP",
                description=f"Inbound traffic detected from known blacklisted IP address {src_ip}",
                timestamp=ts
            )
            triggered_alerts.append({"alert_id": aid, "type": "Known Malicious Source IP"})

        # Rule 2: Suspicious Target Port (Trojan / C2 / Backdoor)
        if dst_port and dst_port in self.rules.suspicious_ports:
            desc = self.rules.suspicious_ports[dst_port]
            aid = self.log_alert(
                alert_type="Suspicious Port Connection",
                severity="High",
                src_ip=src_ip,
                dst_ip=dst_ip,
                rule_triggered="RULE_SUSPICIOUS_PORT",
                description=f"Connection attempt to known risky port {dst_port} ({desc})",
                timestamp=ts
            )
            triggered_alerts.append({"alert_id": aid, "type": "Suspicious Port Connection"})

        # Rule 3: Port Scan Detection
        scan_cutoff = ts - self.rules.scan_window_seconds
        recent_ports = set()
        for p_ts, p_port, _, p_flags in q:
            if p_ts >= scan_cutoff and p_port is not None:
                recent_ports.add(p_port)

        if len(recent_ports) >= self.rules.port_scan_threshold:
            scan_key = f"{src_ip}_{int(ts // self.rules.scan_window_seconds)}"
            if scan_key not in self._alerted_scans:
                self._alerted_scans.add(scan_key)
                aid = self.log_alert(
                    alert_type="Port Scanning Detected",
                    severity="High",
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    rule_triggered="RULE_PORT_SCAN",
                    description=f"Host probed {len(recent_ports)} unique ports in <{self.rules.scan_window_seconds}s",
                    timestamp=ts
                )
                triggered_alerts.append({"alert_id": aid, "type": "Port Scanning Detected"})

        # Rule 4: Connection / Packet Burst Flooding
        burst_cutoff = ts - self.rules.burst_window_seconds
        recent_packets = [p for p in q if p[0] >= burst_cutoff]
        if len(recent_packets) >= self.rules.packet_burst_threshold:
            burst_key = f"burst_{src_ip}_{int(ts // self.rules.burst_window_seconds)}"
            if burst_key not in self._alerted_scans:
                self._alerted_scans.add(burst_key)
                aid = self.log_alert(
                    alert_type="Connection Burst / DoS Pattern",
                    severity="High",
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    rule_triggered="RULE_PACKET_BURST",
                    description=f"Abnormal burst of {len(recent_packets)} packets within {self.rules.burst_window_seconds}s",
                    timestamp=ts
                )
                triggered_alerts.append({"alert_id": aid, "type": "Connection Burst / DoS Pattern"})

        # Rule 5: Excessive Traffic Volume (Data exfiltration / bandwidth flood)
        vol_cutoff = ts - self.rules.volume_window_seconds
        total_vol = sum(p[2] for p in q if p[0] >= vol_cutoff)
        if total_vol >= self.rules.volume_threshold_bytes:
            vol_key = f"vol_{src_ip}_{int(ts // self.rules.volume_window_seconds)}"
            if vol_key not in self._alerted_scans:
                self._alerted_scans.add(vol_key)
                aid = self.log_alert(
                    alert_type="Suspicious High Volume Traffic",
                    severity="Medium",
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    rule_triggered="RULE_HIGH_VOLUME",
                    description=f"Transferred {total_vol:,} bytes in <{self.rules.volume_window_seconds}s",
                    timestamp=ts
                )
                triggered_alerts.append({"alert_id": aid, "type": "Suspicious High Volume Traffic"})

        return triggered_alerts

    def process_scapy_packet(self, scapy_pkt) -> List[Dict[str, Any]]:
        """Extract metadata from Scapy packet and pass to detection engine."""
        try:
            if not scapy_pkt.haslayer("IP"):
                return []

            ip_layer = scapy_pkt["IP"]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            size = len(scapy_pkt)
            protocol = "OTHER"
            src_port = None
            dst_port = None
            flags = ""

            if scapy_pkt.haslayer("TCP"):
                protocol = "TCP"
                tcp = scapy_pkt["TCP"]
                src_port = tcp.sport
                dst_port = tcp.dport
                flags = str(tcp.flags)
            elif scapy_pkt.haslayer("UDP"):
                protocol = "UDP"
                udp = scapy_pkt["UDP"]
                src_port = udp.sport
                dst_port = udp.dport
            elif scapy_pkt.haslayer("ICMP"):
                protocol = "ICMP"

            return self.process_packet(
                src_ip=src_ip,
                dst_ip=dst_ip,
                protocol=protocol,
                src_port=src_port,
                dst_port=dst_port,
                packet_size=size,
                flags=flags,
                timestamp=float(getattr(scapy_pkt, "time", time.time()))
            )
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
            return []

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            query = "SELECT * FROM security_alerts"
            params = []
            if severity:
                query += " WHERE severity = ?"
                params.append(severity)
            query += " ORDER BY timestamp DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_traffic_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total_events = conn.execute("SELECT count(*) FROM network_events").fetchone()[0]
            total_alerts = conn.execute("SELECT count(*) FROM security_alerts").fetchone()[0]
            sev_counts = conn.execute(
                "SELECT severity, count(*) as count FROM security_alerts GROUP BY severity"
            ).fetchall()

            top_src = conn.execute(
                "SELECT src_ip, count(*) as count FROM network_events GROUP BY src_ip ORDER BY count DESC LIMIT 5"
            ).fetchall()

            return {
                "total_packets_inspected": total_events,
                "total_alerts_generated": total_alerts,
                "alerts_by_severity": {r["severity"]: r["count"] for r in sev_counts},
                "top_active_ips": [dict(r) for r in top_src],
            }
        finally:
            conn.close()
