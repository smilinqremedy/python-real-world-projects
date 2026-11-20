"""
Unit tests for Website Contact Form Spam Detection System.
"""
import unittest
import os
from spam_service import SpamDetectionService
from spam_detector import SpamDetector

TEST_DB = "test_spam_detector.db"


class TestSpamDetection(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = SpamDetectionService(TEST_DB)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_input_validation(self):
        # Invalid email
        with self.assertRaises(ValueError):
            self.service.submit_contact_form("Alice", "not-an-email", "Hello", "Sample message body")

        # Short name
        with self.assertRaises(ValueError):
            self.service.submit_contact_form("A", "alice@example.com", "Hello", "Sample message body")

        # Short message
        with self.assertRaises(ValueError):
            self.service.submit_contact_form("Alice", "alice@example.com", "Hello", "Hi")

    def test_genuine_message_classification(self):
        res = self.service.submit_contact_form(
            "David Mark", "david.mark@hospital.org",
            "Inquiry regarding medical equipment procurement",
            "Good afternoon, we are reviewing your catalog of diagnostic machines and would like a quote for five units.",
            "197.210.64.12"
        )
        self.assertEqual(res["classification"], "Genuine")
        self.assertLess(res["spam_score"], 40)
        self.assertEqual(len(res["triggered_rules"]), 0)

    def test_spam_keyword_detection(self):
        res = self.service.submit_contact_form(
            "Crypto Spammer", "spammer@fastmail.com",
            "Exclusive bitcoin investment opportunity",
            "Dear friend, join our crypto giveaway and claim your prize today through our bitcoin investment portal.",
            "185.10.20.30"
        )
        self.assertEqual(res["classification"], "Suspicious")
        self.assertGreaterEqual(res["spam_score"], 40)
        self.assertTrue(any("keyword match" in r for r in res["triggered_rules"]))

    def test_excessive_links_detection(self):
        msg = "Check these links: https://link1.com/a and http://link2.com/b and https://link3.com/c for updates."
        res = self.service.submit_contact_form(
            "Link Bot", "bot@webcrawler.com", "Check links", msg, "192.168.1.50"
        )
        self.assertEqual(res["classification"], "Suspicious")
        self.assertTrue(any("hyperlinks" in r for r in res["triggered_rules"]))

    def test_privacy_conscious_ip_masking(self):
        masked = SpamDetector.mask_ip("192.168.10.42")
        self.assertEqual(masked, "192.168.10.***")

        res = self.service.submit_contact_form(
            "Jane", "jane@example.com", "General question", "Hello team, what are your opening hours on Friday?", "10.0.0.123"
        )
        self.assertEqual(res["masked_ip"], "10.0.0.***")

    def test_admin_review_workflow(self):
        res = self.service.submit_contact_form(
            "Ambiguous Sender", "user@company.com", "Urgent notice",
            "Claim your prize money now from inheritance fund", "127.0.0.1"
        )
        ref = res["submission_ref"]

        # Admin approves
        self.service.review_submission(ref, "Confirmed Spam")
        sub = self.service.get_submission(ref)
        self.assertEqual(sub["admin_status"], "Confirmed Spam")
        self.assertIsNotNone(sub["reviewed_at"])

    def test_spam_statistics_calculation(self):
        self.service.submit_contact_form("User 1", "u1@test.com", "Genuine", "Legitimate query about support hours.", "1.1.1.1")
        self.service.submit_contact_form("Bot", "bot@test.com", "Prize", "Claim your prize in our crypto giveaway right now.", "2.2.2.2")

        stats = self.service.get_spam_statistics()
        self.assertEqual(stats["total_submissions"], 2)
        self.assertEqual(stats["genuine_count"], 1)
        self.assertEqual(stats["suspicious_count"], 1)
        self.assertEqual(stats["spam_rate_percent"], 50.0)


if __name__ == "__main__":
    unittest.main()
