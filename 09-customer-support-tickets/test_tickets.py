"""
Automated Unit Tests for Customer Complaint and Support Ticket Management System
Validates customer registration, ticket creation, unique IDs, agent assignment,
business rule enforcement (prevent unassigned from In Progress), priority ordering, search, and reports.
"""

import os
import unittest
import tempfile
from database import initialize_database
from ticket_service import TicketService


class TestSupportTicketSystem(unittest.TestCase):

    def setUp(self):
        # Create a temporary file database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

        initialize_database(self.db_path)
        self.service = TicketService(self.db_path)

        # Register a test customer
        self.customer = self.service.register_customer(
            full_name="Sarah Connor",
            email="sarah.connor@cyberdyne.com",
            phone="+1-555-8000",
            company_name="Cyberdyne Systems"
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_initial_seeds(self):
        """Verify agents are seeded properly."""
        agents = self.service.list_agents()
        self.assertGreaterEqual(len(agents), 4)

    def test_customer_registration_and_uniqueness(self):
        """Feature 1: Register customer and reject duplicate email."""
        c2 = self.service.register_customer("John Doe", "john.doe@test.com")
        self.assertEqual(c2["full_name"], "John Doe")

        # Duplicate email should fail
        with self.assertRaises(ValueError):
            self.service.register_customer("Duplicate John", "john.doe@test.com")

    def test_create_ticket_with_unique_code_and_categories(self):
        """Features 2, 3, 4, 5, 6: Ticket creation with unique ID, description, category, priority."""
        t1 = self.service.create_ticket(
            customer_id=self.customer["customer_id"],
            title="Unable to download monthly invoice",
            description="The PDF link returns error 404.",
            category="Billing & Payments",
            priority="High"
        )
        self.assertTrue(t1["ticket_code"].startswith("TICK-"))
        self.assertEqual(t1["priority"], "High")
        self.assertEqual(t1["category"], "Billing & Payments")
        self.assertEqual(t1["status"], "Open")
        self.assertIsNone(t1["agent_id"])

        t2 = self.service.create_ticket(
            customer_id=self.customer["customer_id"],
            title="API rate limit breached unexpectedly",
            description="Rate limit exceeded error received on production webhook.",
            category="Technical Support",
            priority="Critical"
        )
        self.assertTrue(t2["ticket_code"] > t1["ticket_code"])

    def test_assign_ticket_to_agent(self):
        """Feature 7: Assign ticket to support agent."""
        ticket = self.service.create_ticket(
            customer_id=self.customer["customer_id"],
            title="Broken checkout button",
            description="Cart button does not respond on mobile.",
            category="Technical Support",
            priority="Medium"
        )
        self.assertIsNone(ticket["agent_id"])

        assigned = self.service.assign_ticket(ticket["ticket_id"], agent_id=1)
        self.assertEqual(assigned["agent_id"], 1)
        self.assertIsNotNone(assigned["agent_name"])

    def test_business_rule_prevent_unassigned_moving_to_in_progress(self):
        """Feature 9 (CRITICAL): Prevent unassigned tickets from moving into progress."""
        ticket = self.service.create_ticket(
            customer_id=self.customer["customer_id"],
            title="Damaged package delivered",
            description="Package arrived torn and contents missing.",
            category="Delivery & Shipping",
            priority="High"
        )
        self.assertIsNone(ticket["agent_id"])

        # Attempt to move unassigned ticket to In Progress MUST fail
        with self.assertRaises(ValueError) as ctx:
            self.service.update_ticket_status(ticket["ticket_id"], "In Progress")
        self.assertIn("Business Rule Violation", str(ctx.exception))

        # Once assigned, moving to In Progress MUST succeed
        self.service.assign_ticket(ticket["ticket_id"], agent_id=2)
        in_progress = self.service.update_ticket_status(ticket["ticket_id"], "In Progress")
        self.assertEqual(in_progress["status"], "In Progress")

    def test_status_transitions_resolved_and_reopened(self):
        """Feature 8: Track ticket statuses: Open -> In Progress -> Resolved -> Reopened."""
        ticket = self.service.create_ticket(
            customer_id=self.customer["customer_id"],
            title="Two-factor authentication reset",
            description="Lost phone, cannot login.",
            category="Account Access & Security",
            priority="Critical",
            agent_id=1
        )
        # Move to In Progress
        t_prog = self.service.update_ticket_status(ticket["ticket_id"], "In Progress")
        self.assertEqual(t_prog["status"], "In Progress")

        # Move to Resolved
        t_res = self.service.update_ticket_status(ticket["ticket_id"], "Resolved", resolution_notes="Identity verified, 2FA reset.")
        self.assertEqual(t_res["status"], "Resolved")
        self.assertIsNotNone(t_res["resolved_at"])

        # Reopen
        t_reopen = self.service.update_ticket_status(ticket["ticket_id"], "Reopened")
        self.assertEqual(t_reopen["status"], "Reopened")

    def test_display_unresolved_tickets_by_priority(self):
        """Feature 10: Display unresolved tickets ordered by priority (Critical > High > Medium > Low)."""
        # Create tickets with different priorities
        self.service.create_ticket(self.customer["customer_id"], "Low issue", "desc", "General Inquiry", "Low")
        self.service.create_ticket(self.customer["customer_id"], "Critical issue", "desc", "Technical Support", "Critical")
        self.service.create_ticket(self.customer["customer_id"], "High issue", "desc", "Billing & Payments", "High")
        self.service.create_ticket(self.customer["customer_id"], "Medium issue", "desc", "Product Quality & Defects", "Medium")

        unresolved = self.service.get_unresolved_tickets_by_priority()
        self.assertEqual(len(unresolved), 4)
        self.assertEqual(unresolved[0]["priority"], "Critical")
        self.assertEqual(unresolved[1]["priority"], "High")
        self.assertEqual(unresolved[2]["priority"], "Medium")
        self.assertEqual(unresolved[3]["priority"], "Low")

    def test_search_ticket_by_id_and_code(self):
        """Feature 11: Search tickets by ID and code."""
        t = self.service.create_ticket(self.customer["customer_id"], "Refund request", "desc", "Billing & Payments", "High")

        by_id = self.service.find_ticket(t["ticket_id"])
        self.assertEqual(by_id["title"], "Refund request")

        by_code = self.service.find_ticket(t["ticket_code"])
        self.assertEqual(by_code["title"], "Refund request")

    def test_generate_ticket_reports(self):
        """Feature 12: Generate reports showing total, status breakdown, priority breakdown."""
        t1 = self.service.create_ticket(self.customer["customer_id"], "T1", "desc", "Billing & Payments", "Critical", agent_id=1)
        self.service.update_ticket_status(t1["ticket_id"], "In Progress")
        self.service.update_ticket_status(t1["ticket_id"], "Resolved")

        self.service.create_ticket(self.customer["customer_id"], "T2", "desc", "Technical Support", "High")

        reports = self.service.generate_ticket_reports()
        self.assertEqual(reports["total_tickets"], 2)
        self.assertEqual(reports["resolved_count"], 1)
        self.assertEqual(reports["unresolved_count"], 1)
        self.assertEqual(reports["resolution_rate_pct"], 50.0)
        self.assertEqual(reports["priority_breakdown"]["Critical"], 1)
        self.assertEqual(reports["priority_breakdown"]["High"], 1)


if __name__ == "__main__":
    unittest.main()
