"""
Automated unit tests for Phishing Email Detection & Analysis Tool.
"""
import unittest
import os
import tempfile
from phishing_detector import PhishingDetector
from sample_emails import create_benign_email, create_credential_phish_email, create_macro_invoice_phish


class TestPhishingDetector(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.detector = PhishingDetector(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_benign_email_scored_low_risk(self):
        raw_eml = create_benign_email()
        result = self.detector.analyze_eml_bytes(raw_eml, "benign_digest.eml")
        self.assertEqual(result["verdict"], "Low Risk")
        self.assertLess(result["risk_score"], 25)
        self.assertEqual(len(result["indicators"]), 0)

    def test_credential_phishing_email_detected(self):
        raw_eml = create_credential_phish_email()
        result = self.detector.analyze_eml_bytes(raw_eml, "paypal_phish.eml")
        self.assertEqual(result["verdict"], "Phishing")
        self.assertGreaterEqual(result["risk_score"], 80)

        categories = [ind["category"] for ind in result["indicators"]]
        self.assertIn("Sender Spoofing", categories)
        self.assertIn("Suspicious Link", categories)
        self.assertIn("Dangerous Attachment", categories)

        # Confirm deceptive link was specifically detected
        link_issues = [ind["description"] for ind in result["indicators"] if ind["category"] == "Suspicious Link"]
        self.assertTrue(any("Deceptive hyperlink" in desc for desc in link_issues))

    def test_macro_invoice_attachment_detected(self):
        raw_eml = create_macro_invoice_phish()
        result = self.detector.analyze_eml_bytes(raw_eml, "overdue_invoice.eml")
        self.assertIn(result["verdict"], ("Suspicious", "Phishing"))

        att_indicators = [ind["description"] for ind in result["indicators"] if ind["category"] == "Dangerous Attachment"]
        self.assertTrue(any(".xlsm" in desc for desc in att_indicators))

    def test_database_persistence(self):
        raw_eml = create_credential_phish_email()
        res = self.detector.analyze_eml_bytes(raw_eml, "stored_phish.eml")

        history = self.detector.get_analysis_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["verdict"], "Phishing")
        self.assertEqual(history[0]["id"], res["analysis_id"])


if __name__ == "__main__":
    unittest.main()
