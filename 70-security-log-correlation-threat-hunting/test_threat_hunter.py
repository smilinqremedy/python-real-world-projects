"""
Automated unit tests for Security Log Correlation & Threat Hunting Tool.
"""
import unittest
import os
import tempfile
from normalizer import LogNormalizer
from threat_hunter import ThreatHunter
from synthetic_soc_data import SYNTHETIC_AUTH_LOGS, SYNTHETIC_WEB_LOGS, SYNTHETIC_FIREWALL_LOGS


class TestThreatHunter(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.hunter = ThreatHunter(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_timestamp_normalization(self):
        iso1, epoch1 = LogNormalizer.parse_timestamp("2026-11-23 09:12:00")
        self.assertEqual(iso1, "2026-11-23 09:12:00")

        iso2, epoch2 = LogNormalizer.parse_timestamp("2026-11-23T09:12:00Z")
        self.assertEqual(iso2, "2026-11-23 09:12:00")

    def test_multi_source_ingestion_and_correlation(self):
        # Ingest all 3 sources
        c_auth = self.hunter.ingest_logs(SYNTHETIC_AUTH_LOGS, "Auth")
        c_web = self.hunter.ingest_logs(SYNTHETIC_WEB_LOGS, "Web")
        c_fw = self.hunter.ingest_logs(SYNTHETIC_FIREWALL_LOGS, "Firewall")

        self.assertEqual(c_auth, len(SYNTHETIC_AUTH_LOGS))
        self.assertEqual(c_web, len(SYNTHETIC_WEB_LOGS))
        self.assertEqual(c_fw, len(SYNTHETIC_FIREWALL_LOGS))

        findings = self.hunter.run_correlation()
        self.assertGreaterEqual(len(findings), 3)

        rule_ids = [f["rule_id"] for f in findings]
        self.assertIn("BRUTE_FORCE_01", rule_ids)
        self.assertIn("RECON_TO_ACCESS_02", rule_ids)
        self.assertIn("EXFILTRATION_03", rule_ids)

    def test_brute_force_spraying_rule(self):
        self.hunter.ingest_logs(SYNTHETIC_AUTH_LOGS, "Auth")
        findings = self.hunter.run_correlation()

        bf = next(f for f in findings if f["rule_id"] == "BRUTE_FORCE_01")
        self.assertEqual(bf["ip_address"], "198.51.100.77")
        self.assertGreaterEqual(bf["event_count"], 5)
        self.assertEqual(bf["severity"], "High")

    def test_recon_to_access_rule(self):
        self.hunter.ingest_logs(SYNTHETIC_AUTH_LOGS, "Auth")
        self.hunter.ingest_logs(SYNTHETIC_WEB_LOGS, "Web")
        findings = self.hunter.run_correlation()

        recon = next(f for f in findings if f["rule_id"] == "RECON_TO_ACCESS_02")
        self.assertEqual(recon["ip_address"], "203.0.113.50")
        self.assertEqual(recon["severity"], "Critical")
        self.assertEqual(recon["username"], "dev_operator")

    def test_threat_filtering_and_timeline(self):
        self.hunter.ingest_logs(SYNTHETIC_AUTH_LOGS, "Auth")
        self.hunter.ingest_logs(SYNTHETIC_WEB_LOGS, "Web")
        self.hunter.ingest_logs(SYNTHETIC_FIREWALL_LOGS, "Firewall")
        self.hunter.run_correlation()

        # Search by IP
        ip_threats = self.hunter.search_threats(ip_address="203.0.113.50")
        self.assertGreaterEqual(len(ip_threats), 1)

        # Reconstruct timeline for IP
        timeline = self.hunter.get_timeline_for_ip("203.0.113.50")
        self.assertGreaterEqual(len(timeline), 3)
        sources = [e["source_type"] for e in timeline]
        self.assertIn("Web", sources)
        self.assertIn("Auth", sources)
        self.assertIn("Firewall", sources)


if __name__ == "__main__":
    unittest.main()
