"""
Automated unit tests for Web Security Header Scanner.
"""
import unittest
import os
import tempfile
import json
from scanner import WebSecurityHeaderScanner
from sample_responses import SECURE_HARDENED_SITE, VULNERABLE_LEGACY_SITE, MISCONFIGURED_SITE


class TestWebSecurityHeaderScanner(unittest.TestCase):
    def setUp(self):
        self.scanner = WebSecurityHeaderScanner()

    def test_url_validation(self):
        self.assertTrue(self.scanner.validate_url("https://example.com"))
        self.assertTrue(self.scanner.validate_url("http://localhost:8080/test"))
        self.assertFalse(self.scanner.validate_url("ftp://ftp.example.com"))
        self.assertFalse(self.scanner.validate_url("not-a-url"))
        self.assertFalse(self.scanner.validate_url(""))

    def test_hardened_site_grade_a(self):
        result = self.scanner.scan_headers_dict(SECURE_HARDENED_SITE, "https://secure.bank.com")
        self.assertGreaterEqual(result["score"], 90)
        self.assertEqual(result["grade"], "A+")
        self.assertEqual(result["summary"]["missing"], 0)
        self.assertEqual(result["summary"]["misconfigured"], 0)

    def test_vulnerable_legacy_site_fails(self):
        result = self.scanner.scan_headers_dict(VULNERABLE_LEGACY_SITE, "http://legacy.site.internal")
        self.assertLess(result["score"], 40)
        self.assertEqual(result["grade"], "F")
        self.assertGreaterEqual(result["summary"]["missing"], 5)
        self.assertGreaterEqual(len(result["information_leakage"]), 2)

    def test_misconfigured_site_issues_detected(self):
        result = self.scanner.scan_headers_dict(MISCONFIGURED_SITE, "https://misconfigured.app")
        self.assertIn("Misconfigured", [h["status"] for h in result["evaluated_headers"]])

        csp = next(h for h in result["evaluated_headers"] if h["header"] == "Content-Security-Policy")
        self.assertEqual(csp["status"], "Misconfigured")
        self.assertTrue(any("unsafe-inline" in iss for iss in csp["issues"]))

        hsts = next(h for h in result["evaluated_headers"] if h["header"] == "Strict-Transport-Security")
        self.assertEqual(hsts["status"], "Misconfigured")
        self.assertTrue(any("Short max-age" in iss for iss in hsts["issues"]))

    def test_export_json_and_html_reports(self):
        result = self.scanner.scan_headers_dict(SECURE_HARDENED_SITE)
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = os.path.join(tmpdir, "report.json")
            html_file = os.path.join(tmpdir, "report.html")

            saved_json = self.scanner.export_report(result, format="json", output_path=json_file)
            saved_html = self.scanner.export_report(result, format="html", output_path=html_file)

            self.assertTrue(os.path.exists(saved_json))
            self.assertTrue(os.path.exists(saved_html))

            with open(saved_json, "r") as f:
                loaded = json.load(f)
            self.assertEqual(loaded["grade"], "A+")


if __name__ == "__main__":
    unittest.main()
