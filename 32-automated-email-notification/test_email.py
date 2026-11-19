"""
Automated unit tests for Automated Email Notification System.
"""
import unittest
import os
from datetime import datetime, timedelta
from email_service import EmailService

TEST_DB = "test_notifications.db"


class TestEmailNotificationSystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.service = EmailService(TEST_DB, test_mode=True)

        # Standard recipients
        self.service.register_recipient("John Doe", "john.doe@example.com")
        self.service.register_recipient("Jane Smith", "jane.smith@example.com")

        # Standard template
        self.service.create_template(
            name="appointment_reminder",
            subject_template="Reminder: Your appointment on {date}",
            body_template="Hello {name},\n\nThis is a reminder that your appointment is scheduled for {date}.\nLocation: {location}.\n\nThank you!"
        )

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_recipient_and_email_validation(self):
        # Invalid email syntax
        with self.assertRaises(ValueError):
            self.service.validate_email("plainaddress")

        with self.assertRaises(ValueError):
            self.service.validate_email("@missingusername.com")

        with self.assertRaises(ValueError):
            self.service.validate_email("user@.com")

        # Valid email normalization
        norm = self.service.validate_email("  Test.User@Example.COM  ")
        self.assertEqual(norm, "test.user@example.com")

        # Duplicate recipient
        with self.assertRaises(ValueError):
            self.service.register_recipient("Duplicate John", "john.doe@example.com")

        recipients = self.service.list_recipients()
        self.assertEqual(len(recipients), 2)

    def test_template_rendering(self):
        rendered = self.service.render_template(
            "appointment_reminder",
            {"name": "John Doe", "date": "2026-12-01 10:00 AM", "location": "Clinic Suite 4"}
        )
        self.assertIn("Reminder: Your appointment on 2026-12-01 10:00 AM", rendered["subject"])
        self.assertIn("Hello John Doe,", rendered["body"])
        self.assertIn("Location: Clinic Suite 4.", rendered["body"])

        # Missing placeholder error
        with self.assertRaises(ValueError):
            self.service.render_template("appointment_reminder", {"name": "John"})

    def test_scheduling_and_dispatch(self):
        t0 = datetime(2026, 11, 19, 12, 0, 0)
        t_future = t0 + timedelta(hours=2)

        # Queue a future scheduled reminder
        qid = self.service.queue_email(
            recipient_email="john.doe@example.com",
            subject="Upcoming Bill",
            body="Your bill is due soon.",
            scheduled_at=t_future
        )
        self.assertIsNotNone(qid)

        # Process at t0 -> should not send yet
        summary_early = self.service.process_queue(current_time=t0)
        self.assertEqual(summary_early["processed"], 0)

        # Process at future -> dispatches successfully
        summary_due = self.service.process_queue(current_time=t_future + timedelta(minutes=5))
        self.assertEqual(summary_due["processed"], 1)
        self.assertEqual(summary_due["succeeded"], 1)

        # Check logs
        logs = self.service.get_history("john.doe@example.com")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["status"], "simulated")

    def test_duplicate_prevention_idempotency(self):
        t0 = datetime(2026, 11, 19, 14, 0, 0)
        # First queue call
        self.service.queue_email(
            recipient_email="jane.smith@example.com",
            subject="Monthly Statement",
            body="Here is your statement",
            scheduled_at=t0,
            idempotency_key="stmt-jane-2026-11"
        )

        # Second identical queue call with same idempotency key must be blocked
        with self.assertRaises(ValueError):
            self.service.queue_email(
                recipient_email="jane.smith@example.com",
                subject="Monthly Statement",
                body="Here is your statement",
                scheduled_at=t0,
                idempotency_key="stmt-jane-2026-11"
            )

    def test_retry_mechanism_on_network_failure(self):
        t0 = datetime(2026, 11, 19, 15, 0, 0)
        # Enable failure simulation
        self.service.simulate_network_failure = True

        qid = self.service.queue_email(
            recipient_email="john.doe@example.com",
            subject="Network Test",
            body="Testing network error retries",
            scheduled_at=t0,
            max_retries=2
        )

        # Attempt 1: failure, retry_count becomes 1, status remains 'pending'
        res1 = self.service.process_queue(current_time=t0)
        self.assertEqual(res1["failed"], 1)

        # Attempt 2: failure, retry_count reaches max_retries (2), status becomes 'failed'
        res2 = self.service.process_queue(current_time=t0)
        self.assertEqual(res2["failed"], 1)

        # Attempt 3: no longer pending
        res3 = self.service.process_queue(current_time=t0)
        self.assertEqual(res3["processed"], 0)

        # History should reflect 2 attempts
        history = self.service.get_history("john.doe@example.com")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["attempt_number"], 2)
        self.assertEqual(history[1]["attempt_number"], 1)

    def test_recipient_consent_enforcement(self):
        # Unsubscribe Jane
        self.service.update_consent("jane.smith@example.com", "unsubscribed")

        # Attempting to queue should raise ValueError
        with self.assertRaises(ValueError):
            self.service.queue_email(
                recipient_email="jane.smith@example.com",
                subject="Marketing Offer",
                body="Special discount!"
            )

    def test_activity_report(self):
        # Send instant email
        self.service.send_instant("john.doe@example.com", "Hello John", "Welcome!")
        report = self.service.generate_activity_report()
        self.assertEqual(report["total_recipients"], 2)
        self.assertEqual(report["queue_sent"], 1)
        self.assertEqual(report["successful_deliveries"], 1)
        self.assertEqual(report["failed_deliveries"], 0)
        self.assertEqual(report["deliverability_rate_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
