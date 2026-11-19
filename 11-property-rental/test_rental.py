"""
Automated unit and integration tests for Property Rental Management System.
"""

import os
import tempfile
import unittest
from rental_service import RentalService


class TestPropertyRentalManagement(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.service = RentalService(db_path=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_property_registration(self):
        prop = self.service.register_property("PROP-101", "Sunrise Apt 1A", "124 Main St", 1200.0)
        self.assertEqual(prop["property_code"], "PROP-101")
        self.assertEqual(prop["status"], "Vacant")

        # Duplicate property code
        with self.assertRaises(ValueError):
            self.service.register_property("PROP-101", "Sunrise Apt 1A", "124 Main St", 1300.0)

        # Invalid rent
        with self.assertRaises(ValueError):
            self.service.register_property("PROP-102", "Sunset Villa", "456 Oak St", -50.0)

    def test_tenant_registration_and_assignment(self):
        self.service.register_property("PROP-201", "Oak Studio", "789 Pine Rd", 950.0)

        tenant = self.service.add_tenant(
            code="TEN-01",
            name="Alice Smith",
            email="alice@example.com",
            phone="555-0101",
            lease_start_date="2026-01-01",
            property_code="PROP-201"
        )
        self.assertEqual(tenant["name"], "Alice Smith")

        # Verify property is now occupied
        props = self.service.list_properties("Occupied")
        self.assertEqual(len(props), 1)
        self.assertEqual(props[0]["property_code"], "PROP-201")

        # Attempting to assign another tenant to the same occupied property
        with self.assertRaises(ValueError):
            self.service.add_tenant(
                code="TEN-02",
                name="Bob Jones",
                email="bob@example.com",
                phone="555-0202",
                lease_start_date="2026-02-01",
                property_code="PROP-201"
            )

    def test_rent_payment_and_balances(self):
        self.service.register_property("PROP-301", "Maple Flat", "10 Elm St", 1000.0)
        self.service.add_tenant(
            code="TEN-03",
            name="Charlie Brown",
            email="charlie@example.com",
            phone="555-0303",
            lease_start_date="2026-01-01",
            property_code="PROP-301"
        )

        # Check balance as of 2026-03-15 (3 months: Jan, Feb, Mar = $3,000)
        balances = self.service.get_tenant_balances(as_of_date="2026-03-15")
        self.assertEqual(len(balances), 1)
        self.assertEqual(balances[0]["months_due"], 3)
        self.assertEqual(balances[0]["total_expected"], 3000.0)
        self.assertEqual(balances[0]["outstanding_balance"], 3000.0)

        # Make payment for Jan & Feb ($2,000)
        pay = self.service.record_rent_payment(
            tenant_code="TEN-03",
            amount=2000.0,
            period_month="2026-01",
            payment_date="2026-01-05"
        )
        self.assertTrue(pay["payment_ref"].startswith("PAY-"))

        # Re-check balances
        balances = self.service.get_tenant_balances(as_of_date="2026-03-15")
        self.assertEqual(balances[0]["total_paid"], 2000.0)
        self.assertEqual(balances[0]["outstanding_balance"], 1000.0)

    def test_property_listing_filters(self):
        self.service.register_property("P-1", "Unit 1", "Addr 1", 800.0)
        self.service.register_property("P-2", "Unit 2", "Addr 2", 900.0)
        self.service.add_tenant("T-1", "David", "d@ex.com", "123", "2026-01-01", "P-1")

        all_props = self.service.list_properties()
        self.assertEqual(len(all_props), 2)

        vacant = self.service.list_properties("Vacant")
        self.assertEqual(len(vacant), 1)
        self.assertEqual(vacant[0]["property_code"], "P-2")

        occupied = self.service.list_properties("Occupied")
        self.assertEqual(len(occupied), 1)
        self.assertEqual(occupied[0]["property_code"], "P-1")

    def test_search_tenants(self):
        self.service.register_property("P-SEARCH", "Search Condo", "Downtown", 1500.0)
        self.service.add_tenant("T-SRCH", "Eleanor Vance", "eleanor@hill.com", "999-8888", "2026-01-01", "P-SEARCH")

        res_name = self.service.search_tenants("Eleanor")
        self.assertEqual(len(res_name), 1)

        res_prop = self.service.search_tenants("Search Condo")
        self.assertEqual(len(res_prop), 1)

        res_empty = self.service.search_tenants("Nonexistent")
        self.assertEqual(len(res_empty), 0)

    def test_monthly_collection_report(self):
        self.service.register_property("PROP-REP1", "Villa 1", "North Way", 2000.0)
        self.service.add_tenant("T-REP1", "George", "g@ex.com", "555-9090", "2026-01-01", "PROP-REP1")

        self.service.record_rent_payment("T-REP1", 1500.0, "2026-11", "2026-11-03")

        report = self.service.generate_monthly_report("2026-11")
        self.assertEqual(report["expected_rent"], 2000.0)
        self.assertEqual(report["collected_rent"], 1500.0)
        self.assertEqual(report["outstanding_deficit"], 500.0)
        self.assertEqual(report["collection_rate_percent"], 75.0)
        self.assertEqual(report["payments_count"], 1)


if __name__ == "__main__":
    unittest.main()
