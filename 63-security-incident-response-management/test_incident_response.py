"""
Unit tests for Security Incident Response Management System.
"""
import unittest
import os
import tempfile
from incident_service import IncidentResponseService, RBACPermissionError, IncidentWorkflowError


class TestIncidentResponseService(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.service = IncidentResponseService(self.db_path)

        # Seed roles
        self.admin_id = self.service.create_user("ciso_admin", "Alice Admin", "Admin", "admin@corp.sec")
        self.lead_id = self.service.create_user("lead_bob", "Bob Lead", "Lead", "bob@corp.sec")
        self.analyst_id = self.service.create_user("analyst_charlie", "Charlie Analyst", "Analyst", "charlie@corp.sec")

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_user_creation_and_role_validation(self):
        with self.assertRaises(ValueError):
            self.service.create_user("bad_role", "Bad Role", "Manager", "bad@corp.sec")
        with self.assertRaises(ValueError):
            self.service.create_user("ciso_admin", "Duplicate", "Admin", "other@corp.sec")

    def test_incident_creation_and_audit(self):
        ref = self.service.create_incident(
            title="Suspicious Outbound Beaconing",
            description="High frequency traffic detected towards unknown C2 IP.",
            severity="High",
            category="Malware",
            created_by_id=self.analyst_id
        )
        inc = self.service.get_incident_details(ref)
        self.assertEqual(inc["status"], "Reported")
        self.assertEqual(inc["severity"], "High")
        self.assertEqual(len(inc["timeline"]), 1)
        self.assertEqual(inc["timeline"][0]["action"], "INCIDENT_CREATED")

    def test_rbac_lead_assignment(self):
        ref = self.service.create_incident(
            "Phishing Campaign Target", "Finance execs received deceptive credential harvest link.",
            "Critical", "Phishing", self.analyst_id
        )

        # Analyst cannot assign lead
        with self.assertRaises(RBACPermissionError):
            self.service.assign_lead_investigator(ref, lead_user_id=self.lead_id, acting_user_id=self.analyst_id)

        # Lead or Admin can assign lead
        self.service.assign_lead_investigator(ref, lead_user_id=self.lead_id, acting_user_id=self.admin_id)
        inc = self.service.get_incident_details(ref)
        self.assertEqual(inc["lead_analyst_name"], "Bob Lead")

    def test_valid_lifecycle_progression(self):
        ref = self.service.create_incident(
            "Ransomware Canary Alert", "File extension changes observed in file share.",
            "Critical", "Malware", self.analyst_id
        )

        self.service.transition_status(ref, "Investigating", self.analyst_id, "Host isolated from LAN.")
        self.service.transition_status(ref, "Contained", self.analyst_id, "Process terminated, credentials rotated.")
        self.service.transition_status(ref, "Eradicated", self.analyst_id, "Malware artifacts scrubbed.")
        self.service.transition_status(ref, "Recovered", self.analyst_id, "Clean backup restored and verified.")
        self.service.transition_status(ref, "Closed", self.lead_id, "Post-mortem completed.")

        inc = self.service.get_incident_details(ref)
        self.assertEqual(inc["status"], "Closed")
        self.assertIsNotNone(inc["closed_at"])

    def test_invalid_status_transition_prevented(self):
        ref = self.service.create_incident(
            "DDoS Volumetric Burst", "Web tier saturated.",
            "Medium", "DDoS", self.analyst_id
        )

        # Cannot jump from Reported directly to Closed without containment steps
        with self.assertRaises(IncidentWorkflowError):
            self.service.transition_status(ref, "Closed", self.admin_id)

    def test_rbac_analyst_cannot_close_incident(self):
        ref = self.service.create_incident(
            "Unauthorized S3 Bucket Access", "Public read policy detected.",
            "High", "Unauthorized Access", self.analyst_id
        )
        self.service.transition_status(ref, "Investigating", self.analyst_id)
        self.service.transition_status(ref, "Contained", self.analyst_id)
        self.service.transition_status(ref, "Recovered", self.analyst_id)

        # Analyst tries to close -> RBAC error
        with self.assertRaises(RBACPermissionError):
            self.service.transition_status(ref, "Closed", self.analyst_id)

        # Lead closes successfully
        self.service.transition_status(ref, "Closed", self.lead_id)
        self.assertEqual(self.service.get_incident_details(ref)["status"], "Closed")

    def test_notes_evidence_and_metrics(self):
        ref = self.service.create_incident(
            "Data Exfiltration Attempt", "DLP alert triggered on outbound email.",
            "High", "Data Breach", self.analyst_id
        )
        self.service.add_note(ref, self.analyst_id, "Correlated endpoint logs with firewall telemetry.")
        self.service.add_evidence(
            ref, self.analyst_id, "Log", "s3://sec-logs/dlp-20261123.json",
            "DLP alert export", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

        inc = self.service.get_incident_details(ref)
        self.assertEqual(len(inc["notes"]), 1)
        self.assertEqual(len(inc["evidence"]), 1)
        self.assertEqual(inc["evidence"][0]["evidence_type"], "Log")

        metrics = self.service.get_incident_metrics()
        self.assertEqual(metrics["total_incidents"], 1)
        self.assertEqual(metrics["by_category"]["Data Breach"], 1)


if __name__ == "__main__":
    unittest.main()
