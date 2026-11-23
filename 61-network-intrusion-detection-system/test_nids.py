"""
Automated unit tests for Network Intrusion Detection System (NIDS).
"""
import unittest
import os
import tempfile
import time
from detector import NIDSEngine, DetectionRules
from traffic_simulator import generate_synthetic_stream


class TestNIDS(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.rules = DetectionRules(
            port_scan_threshold=5,
            scan_window_seconds=5.0,
            packet_burst_threshold=10,
            burst_window_seconds=3.0,
            suspicious_ports={4444: "Metasploit", 31337: "Back Orifice"},
            blocked_ips={"198.51.100.45"}
        )
        self.engine = NIDSEngine(rules=self.rules, db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_normal_traffic_does_not_trigger_alerts(self):
        now = time.time()
        for i in range(3):
            alerts = self.engine.process_packet(
                src_ip="192.168.1.50",
                dst_ip="93.184.216.34",
                protocol="TCP",
                src_port=50000 + i,
                dst_port=443,
                packet_size=120,
                timestamp=now + (i * 0.1)
            )
            self.assertEqual(len(alerts), 0)

        db_alerts = self.engine.get_alerts()
        self.assertEqual(len(db_alerts), 0)

    def test_port_scan_detection(self):
        now = time.time()
        target_ports = [21, 22, 23, 25, 80, 443]  # 6 ports > threshold of 5
        detected = False
        for idx, port in enumerate(target_ports):
            alerts = self.engine.process_packet(
                src_ip="192.168.1.199",
                dst_ip="192.168.1.10",
                protocol="TCP",
                src_port=40000 + idx,
                dst_port=port,
                packet_size=60,
                flags="S",
                timestamp=now + (idx * 0.1)
            )
            if any(a["type"] == "Port Scanning Detected" for a in alerts):
                detected = True

        self.assertTrue(detected)
        alerts = self.engine.get_alerts()
        self.assertTrue(any(a["alert_type"] == "Port Scanning Detected" for a in alerts))

    def test_suspicious_port_alert(self):
        alerts = self.engine.process_packet(
            src_ip="192.168.1.77",
            dst_ip="192.168.1.10",
            protocol="TCP",
            src_port=49152,
            dst_port=4444,
            packet_size=74,
            flags="S"
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], "Suspicious Port Connection")

        db_alerts = self.engine.get_alerts(severity="High")
        self.assertEqual(len(db_alerts), 1)
        self.assertEqual(db_alerts[0]["src_ip"], "192.168.1.77")

    def test_connection_burst_detection(self):
        now = time.time()
        # Send 12 packets (threshold is 10 within 3s)
        detected = False
        for i in range(12):
            alerts = self.engine.process_packet(
                src_ip="192.168.1.88",
                dst_ip="192.168.1.10",
                protocol="TCP",
                src_port=30000 + i,
                dst_port=80,
                packet_size=60,
                timestamp=now + (i * 0.05)
            )
            if any(a["type"] == "Connection Burst / DoS Pattern" for a in alerts):
                detected = True

        self.assertTrue(detected)

    def test_blocked_threat_intel_ip(self):
        alerts = self.engine.process_packet(
            src_ip="198.51.100.45",
            dst_ip="192.168.1.10",
            protocol="TCP",
            src_port=12345,
            dst_port=80,
            packet_size=60
        )
        self.assertTrue(any(a["type"] == "Known Malicious Source IP" for a in alerts))
        critical_alerts = self.engine.get_alerts(severity="Critical")
        self.assertEqual(len(critical_alerts), 1)

    def test_scapy_stream_processing_and_summary(self):
        packets = generate_synthetic_stream()
        for pkt in packets:
            self.engine.process_scapy_packet(pkt)

        summary = self.engine.get_traffic_summary()
        self.assertGreater(summary["total_packets_inspected"], 25)
        self.assertGreater(summary["total_alerts_generated"], 3)
        self.assertIn("High", summary["alerts_by_severity"])


if __name__ == "__main__":
    unittest.main()
