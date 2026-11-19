"""
Automated unit tests for Event Registration and Ticketing System.
"""

import os
import tempfile
import unittest
from ticketing_service import TicketingService


class TestEventTicketing(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = TicketingService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_event_creation(self):
        ev = self.service.create_event("DEV-CONF", "Python Tech Summit", "2026-12-15", "Auditorium A", 50.0, 100)
        self.assertEqual(ev["event_code"], "DEV-CONF")
        self.assertEqual(ev["max_capacity"], 100)

        # Duplicate event code
        with self.assertRaises(ValueError):
            self.service.create_event("DEV-CONF", "Duplicate Summit", "2026-12-15", "Room B", 20.0, 50)

        # Negative price
        with self.assertRaises(ValueError):
            self.service.create_event("BAD-PRICE", "Bad Event", "2026-12-15", "Room B", -10.0, 50)

    def test_capacity_rejection(self):
        # Create event with capacity 2
        self.service.create_event("MICRO-EVT", "Exclusive Workshop", "2026-11-20", "Lab 1", 20.0, 2)

        # Attendee 1
        t1 = self.service.register_attendee("MICRO-EVT", "User 1", "u1@example.com", "111")
        self.assertTrue(t1["ticket_id"].startswith("TCK-"))

        # Attendee 2
        t2 = self.service.register_attendee("MICRO-EVT", "User 2", "u2@example.com", "222")

        # Attendee 3 should be rejected (Capacity reached)
        with self.assertRaises(ValueError):
            self.service.register_attendee("MICRO-EVT", "User 3", "u3@example.com", "333")

        # Check availability
        avail = self.service.get_event_availability("MICRO-EVT")
        self.assertEqual(avail["remaining_tickets"], 0)
        self.assertTrue(avail["is_sold_out"])

    def test_duplicate_registration_prevention(self):
        self.service.create_event("SEMINAR", "AI Ethics", "2026-11-25", "Hall B", 15.0, 50)

        self.service.register_attendee("SEMINAR", "Grace Hopper", "grace@navy.mil", "555-1212")

        # Duplicate email for same event
        with self.assertRaises(ValueError):
            self.service.register_attendee("SEMINAR", "Grace Duplicate", "grace@navy.mil", "555-9999")

    def test_payment_and_checkin_rules(self):
        self.service.create_event("CONCERT", "Jazz Night", "2026-12-01", "Jazz Club", 35.0, 200)

        t = self.service.register_attendee("CONCERT", "Miles Davis", "miles@jazz.com", "555-3333", is_paid=False)
        t_id = t["ticket_id"]
        self.assertEqual(t["payment_status"], "Unpaid")

        # Cannot check in unpaid ticket
        with self.assertRaises(ValueError):
            self.service.check_in_attendee(t_id)

        # Record payment
        paid_ticket = self.service.record_payment(t_id)
        self.assertEqual(paid_ticket["payment_status"], "Paid")

        # Check-in succeeds
        checked_ticket = self.service.check_in_attendee(t_id)
        self.assertTrue(checked_ticket["is_checked_in"])
        self.assertIsNotNone(checked_ticket["check_in_time"])

        # Second check-in fails (already checked in)
        with self.assertRaises(ValueError):
            self.service.check_in_attendee(t_id)

    def test_report_and_revenue(self):
        self.service.create_event("CHARITY-RUN", "5K Fun Run", "2026-11-30", "City Park", 25.0, 10)

        t1 = self.service.register_attendee("CHARITY-RUN", "Runner 1", "r1@test.com", "111", is_paid=True)
        t2 = self.service.register_attendee("CHARITY-RUN", "Runner 2", "r2@test.com", "222", is_paid=True)
        t3 = self.service.register_attendee("CHARITY-RUN", "Runner 3", "r3@test.com", "333", is_paid=False)

        # Check in Runner 1
        self.service.check_in_attendee(t1["ticket_id"])

        rep = self.service.generate_report("CHARITY-RUN")[0]
        self.assertEqual(rep["tickets_issued"], 3)
        self.assertEqual(rep["paid_tickets"], 2)
        self.assertEqual(rep["total_revenue"], 50.0)
        self.assertEqual(rep["checked_in_count"], 1)
        self.assertEqual(rep["occupancy_rate"], 30.0)


if __name__ == "__main__":
    unittest.main()
