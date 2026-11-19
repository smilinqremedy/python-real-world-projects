"""
Automated Unit Tests for Queue Management System
Validates ticket issuance, FIFO queue ordering, customer calling, serving transitions,
cancellations, waiting time calculations, and SQLite persistence.
"""

import os
import unittest
import tempfile
import time
from database import initialize_database
from queue_manager import QueueManager


class TestQueueManagementSystem(unittest.TestCase):

    def setUp(self):
        # Create a temporary file database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        initialize_database(self.db_path)
        self.manager = QueueManager(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_initialization(self):
        """Test default service categories and counters are seeded."""
        categories = self.manager.list_categories()
        counters = self.manager.list_counters()
        self.assertGreaterEqual(len(categories), 4)
        self.assertGreaterEqual(len(counters), 3)

    def test_register_and_enqueue_customer(self):
        """Features 1, 2, 3, 4: Register customer, assign category, generate unique ticket, enqueue."""
        t1 = self.manager.register_and_enqueue_customer("Alice Cooper", "TX", "+1-555-1001")
        self.assertEqual(t1["ticket_number"], "TX-101")
        self.assertEqual(t1["queue_position"], 1)

        t2 = self.manager.register_and_enqueue_customer("Bob Marley", "TX", "+1-555-1002")
        self.assertEqual(t2["ticket_number"], "TX-102")
        self.assertEqual(t2["queue_position"], 2)

        t3 = self.manager.register_and_enqueue_customer("Charlie Chaplin", "CS", "+1-555-1003")
        self.assertEqual(t3["ticket_number"], "CS-101")
        self.assertEqual(t3["queue_position"], 1)

    def test_fifo_calling_next_customer(self):
        """Feature 5: FIFO queue order when calling next customer."""
        self.manager.register_and_enqueue_customer("First Person", "TX")
        self.manager.register_and_enqueue_customer("Second Person", "TX")

        # Call to Counter 1
        called_ticket = self.manager.call_next_customer(counter_id=1)
        self.assertEqual(called_ticket["ticket_number"], "TX-101")
        self.assertEqual(called_ticket["customer_name"], "First Person")
        self.assertEqual(called_ticket["status"], "serving")
        self.assertEqual(called_ticket["counter_id"], 1)

        # Counter 1 is now busy, calling again should raise error
        with self.assertRaises(ValueError):
            self.manager.call_next_customer(counter_id=1)

        # Call to Counter 2 should get the second person in FIFO order
        called_ticket2 = self.manager.call_next_customer(counter_id=2)
        self.assertEqual(called_ticket2["ticket_number"], "TX-102")
        self.assertEqual(called_ticket2["customer_name"], "Second Person")

    def test_tracking_currently_serving(self):
        """Feature 6: Tracking customers currently being served."""
        self.manager.register_and_enqueue_customer("David Bowie", "LN")
        self.manager.call_next_customer(counter_id=3)

        serving = self.manager.get_currently_serving()
        self.assertEqual(len(serving), 1)
        self.assertEqual(serving[0]["customer_name"], "David Bowie")
        self.assertEqual(serving[0]["counter_id"], 3)

    def test_mark_as_served(self):
        """Feature 7: Mark service as completed and free counter."""
        self.manager.register_and_enqueue_customer("Emma Stone", "CS")
        self.manager.call_next_customer(counter_id=2)

        # Mark served
        completed = self.manager.mark_as_served(counter_id=2)
        self.assertEqual(completed["status"], "completed")
        self.assertIsNotNone(completed["completed_at"])

        # Counter 2 should now be free
        counters = self.manager.list_counters()
        c2 = next(c for c in counters if c["counter_id"] == 2)
        self.assertIsNone(c2["current_ticket_id"])

    def test_cancel_queue_ticket(self):
        """Feature 8: Cancelling waiting tickets removes them from queue."""
        self.manager.register_and_enqueue_customer("Frank Sinatra", "AC")
        self.manager.register_and_enqueue_customer("Grace Kelly", "AC")

        # Cancel Frank
        cancelled = self.manager.cancel_ticket("AC-101", reason="No show")
        self.assertEqual(cancelled["status"], "cancelled")

        # Next customer called should be Grace (AC-102)
        called = self.manager.call_next_customer(counter_id=1)
        self.assertEqual(called["ticket_number"], "AC-102")

    def test_display_waiting_and_completed_lists(self):
        """Features 9 & 10: Display waiting customers and completed services."""
        self.manager.register_and_enqueue_customer("Harry Potter", "TX")
        self.manager.register_and_enqueue_customer("Hermione Granger", "TX")

        waiting = self.manager.get_waiting_customers()
        self.assertEqual(len(waiting), 2)

        # Serve Harry
        self.manager.call_next_customer(counter_id=1)
        self.manager.mark_as_served(counter_id=1)

        completed = self.manager.get_completed_services()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["ticket_number"], "TX-101")

        waiting_now = self.manager.get_waiting_customers()
        self.assertEqual(len(waiting_now), 1)
        self.assertEqual(waiting_now[0]["ticket_number"], "TX-102")

    def test_calculate_average_waiting_time(self):
        """Feature 11: Calculate average waiting time for completed services."""
        t1 = self.manager.register_and_enqueue_customer("Cust 1", "TX")
        t2 = self.manager.register_and_enqueue_customer("Cust 2", "TX")

        self.manager.call_next_customer(counter_id=1)
        self.manager.mark_as_served(counter_id=1)

        self.manager.call_next_customer(counter_id=2)
        self.manager.mark_as_served(counter_id=2)

        stats = self.manager.calculate_average_waiting_time()
        self.assertEqual(stats["served_count"], 2)
        self.assertIsInstance(stats["avg_wait_seconds"], float)
        self.assertIsInstance(stats["avg_wait_minutes"], float)


if __name__ == "__main__":
    unittest.main()
