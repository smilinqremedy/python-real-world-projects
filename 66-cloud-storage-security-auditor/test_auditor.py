"""
Automated unit tests for Cloud Storage Security Configuration Auditor.
"""
import unittest
import os
import tempfile
import json
import yaml
from auditor import CloudStorageSecurityAuditor
from sample_configs import INSECURE_PUBLIC_BUCKET, HARDENED_ENTERPRISE_BUCKET, PARTIAL_RISK_BUCKET


class TestCloudStorageAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = CloudStorageSecurityAuditor()

    def test_hardened_bucket_passes_all_checks(self):
        result = self.auditor.audit_bucket(HARDENED_ENTERPRISE_BUCKET)
        self.assertEqual(result["failed_checks"], 0)
        self.assertEqual(result["passed_checks"], 6)
        self.assertEqual(result["compliance_percentage"], 100.0)
        self.assertIn("STRONG", result["security_posture"])
        self.assertEqual(len(result["findings"]), 0)

    def test_insecure_bucket_flags_critical_exposure(self):
        result = self.auditor.audit_bucket(INSECURE_PUBLIC_BUCKET)
        self.assertGreaterEqual(result["severity_summary"]["Critical"], 1)
        self.assertGreaterEqual(result["severity_summary"]["High"], 1)
        self.assertIn("CRITICAL EXPOSURE", result["security_posture"])

        finding_ids = [f["check_id"] for f in result["findings"]]
        self.assertIn("S3.1", finding_ids)  # Public Access Block
        self.assertIn("S3.2", finding_ids)  # Wildcard Principal
        self.assertIn("S3.3", finding_ids)  # Missing SSE
        self.assertIn("S3.4", finding_ids)  # Missing logging
        self.assertIn("S3.5", finding_ids)  # Versioning suspended
        self.assertIn("S3.6", finding_ids)  # Missing TLS enforcement

    def test_partial_risk_bucket_findings(self):
        result = self.auditor.audit_bucket(PARTIAL_RISK_BUCKET)
        # Has encryption and versioning, but missing logging and TLS and open public policy
        self.assertEqual(result["severity_summary"]["Critical"], 0)
        self.assertGreaterEqual(result["severity_summary"]["High"], 1)

    def test_json_and_yaml_file_loading(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "bucket.json")
            yaml_path = os.path.join(tmpdir, "bucket.yaml")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(INSECURE_PUBLIC_BUCKET, f)
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(HARDENED_ENTERPRISE_BUCKET, f)

            loaded_json = CloudStorageSecurityAuditor.load_config_file(json_path)
            loaded_yaml = CloudStorageSecurityAuditor.load_config_file(yaml_path)

            self.assertEqual(loaded_json["BucketName"], INSECURE_PUBLIC_BUCKET["BucketName"])
            self.assertEqual(loaded_yaml["BucketName"], HARDENED_ENTERPRISE_BUCKET["BucketName"])

    def test_export_report(self):
        result = self.auditor.audit_bucket(INSECURE_PUBLIC_BUCKET)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = os.path.join(tmpdir, "audit_report.json")
            saved = self.auditor.export_report(result, output_path=out_file)
            self.assertTrue(os.path.exists(saved))
            with open(saved, "r") as f:
                data = json.load(f)
            self.assertEqual(data["bucket_name"], INSECURE_PUBLIC_BUCKET["BucketName"])


if __name__ == "__main__":
    unittest.main()
