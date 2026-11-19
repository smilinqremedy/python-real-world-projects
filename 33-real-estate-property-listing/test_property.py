"""
Automated unit tests for Real Estate Property Listing and Search System.
"""
import unittest
import os
from property_service import PropertyService

TEST_DB = "test_real_estate.db"


class TestPropertySystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.service = PropertyService(TEST_DB)

        # Standard seed data
        self.service.register_owner("OWN-01", "Robert Vance", "robert@vancerefrigeration.com", "555-0101")
        self.service.register_agent("AGT-01", "Dwight Schrute", "dwight@schrute-realty.com", "555-0102", commission_rate=3.0)
        self.service.register_client("CLI-01", "Jim Halpert", "jim@halpert.com", "555-0103", budget_max=450000.0, preferred_type="house")
        self.service.register_client("CLI-02", "Pam Beesly", "pam@beesly.com", "555-0104", budget_max=2500.0, preferred_type="apartment")

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_stakeholder_registration(self):
        # Invalid email
        with self.assertRaises(ValueError):
            self.service.register_owner("OWN-02", "Bad Email", "not-an-email", "555-9999")

        # Duplicate owner code
        with self.assertRaises(ValueError):
            self.service.register_owner("OWN-01", "Duplicate Code", "dup@email.com", "555-9999")

        # Invalid commission rate
        with self.assertRaises(ValueError):
            self.service.register_agent("AGT-02", "Bad Agent", "bad@agent.com", "555-8888", commission_rate=150.0)

        # Retrieve and verify
        agent = self.service.get_agent("AGT-01")
        self.assertEqual(agent["name"], "Dwight Schrute")
        self.assertEqual(agent["commission_rate"], 3.0)

    def test_property_creation_and_search(self):
        # Add property
        pid = self.service.add_property(
            listing_code="PROP-101",
            owner_code="OWN-01",
            title="Suburban Family Home",
            property_type="house",
            listing_type="sale",
            price=350000.0,
            address="42 Elm Street",
            city="Scranton",
            area_sqft=2200.0,
            bedrooms=3,
            bathrooms=2.5,
            agent_code="AGT-01"
        )
        self.assertIsNotNone(pid)

        # Add second property (apartment for rent)
        self.service.add_property(
            listing_code="PROP-102",
            owner_code="OWN-01",
            title="Downtown Modern Loft",
            property_type="apartment",
            listing_type="rent",
            price=1800.0,
            address="100 Main St, Apt 4B",
            city="Scranton",
            area_sqft=950.0,
            bedrooms=1,
            bathrooms=1.0,
            agent_code="AGT-01"
        )

        # Invalid property type
        with self.assertRaises(ValueError):
            self.service.add_property(
                listing_code="PROP-ERR",
                owner_code="OWN-01",
                title="Invalid Type",
                property_type="spaceship",
                listing_type="sale",
                price=500000.0,
                address="Road 1",
                city="Scranton",
                area_sqft=1000.0
            )

        # Search by city and type
        results = self.service.search_properties(city="Scranton", listing_type="sale")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["listing_code"], "PROP-101")
        self.assertEqual(results[0]["price"], 350000.0)

        # Search rentals under $2000
        rentals = self.service.search_properties(listing_type="rent", max_price=2000.0)
        self.assertEqual(len(rentals), 1)
        self.assertEqual(rentals[0]["listing_code"], "PROP-102")

    def test_inquiries_and_viewings(self):
        self.service.add_property(
            listing_code="PROP-201",
            owner_code="OWN-01",
            title="Cozy Cottage",
            property_type="house",
            listing_type="sale",
            price=280000.0,
            address="12 Lake Rd",
            city="Carbondale",
            area_sqft=1500.0,
            bedrooms=2,
            bathrooms=1.0,
            agent_code="AGT-01"
        )

        # Create inquiry
        inq_id = self.service.create_inquiry("PROP-201", "CLI-01", "Is the backyard fenced?")
        self.assertIsNotNone(inq_id)
        inquiries = self.service.list_inquiries("PROP-201")
        self.assertEqual(len(inquiries), 1)
        self.assertEqual(inquiries[0]["client_name"], "Jim Halpert")

        # Schedule viewing
        v_id = self.service.schedule_viewing("PROP-201", "CLI-01", "2026-11-25 14:00:00")
        self.assertIsNotNone(v_id)

        # Complete viewing
        self.service.complete_viewing(v_id, feedback="Client loved the natural lighting.")
        viewings = self.service.list_viewings("PROP-201")
        self.assertEqual(viewings[0]["status"], "completed")
        self.assertIn("natural lighting", viewings[0]["feedback"])

    def test_offers_and_commission_calculation(self):
        self.service.add_property(
            listing_code="PROP-301",
            owner_code="OWN-01",
            title="Executive Villa",
            property_type="villa",
            listing_type="sale",
            price=500000.0,
            address="1 Estate Way",
            city="Dunmore",
            area_sqft=4000.0,
            bedrooms=4,
            bathrooms=3.5,
            agent_code="AGT-01"  # 3.0% commission
        )

        # Two competing offers
        offer1 = self.service.make_offer("PROP-301", "CLI-01", 480000.0)
        offer2 = self.service.make_offer("PROP-301", "CLI-02", 495000.0)

        # Accept offer 2 ($495,000 at 3% = $14,850.00 commission)
        res = self.service.respond_to_offer(offer2, "accepted")
        self.assertEqual(res["status"], "accepted")
        self.assertEqual(res["property_status"], "sold")
        self.assertEqual(res["commission_earned"], 14850.0)

        # Verify property is marked sold
        prop = self.service.get_property("PROP-301")
        self.assertEqual(prop["status"], "sold")

        # Verify offer 1 was automatically rejected
        conn = self.service._get_connection()
        try:
            o1_status = conn.execute("SELECT status FROM offers WHERE id = ?", (offer1,)).fetchone()["status"]
            self.assertEqual(o1_status, "rejected")
        finally:
            conn.close()

    def test_market_and_agent_performance_reports(self):
        # Property 1: Sale closed
        self.service.add_property(
            listing_code="PROP-401",
            owner_code="OWN-01",
            title="Commercial Storefront",
            property_type="commercial",
            listing_type="sale",
            price=200000.0,
            address="50 Lackawanna Ave",
            city="Scranton",
            area_sqft=1800.0,
            agent_code="AGT-01"
        )
        off_sale = self.service.make_offer("PROP-401", "CLI-01", 200000.0)
        self.service.respond_to_offer(off_sale, "accepted")

        # Property 2: Rental closed ($1,500/month at 3% = $45 commission)
        self.service.add_property(
            listing_code="PROP-402",
            owner_code="OWN-01",
            title="City Flat",
            property_type="apartment",
            listing_type="rent",
            price=1500.0,
            address="88 Spruce St",
            city="Scranton",
            area_sqft=750.0,
            agent_code="AGT-01"
        )
        off_rent = self.service.make_offer("PROP-402", "CLI-02", 1500.0)
        self.service.respond_to_offer(off_rent, "accepted")

        # Property 3: Still available
        self.service.add_property(
            listing_code="PROP-403",
            owner_code="OWN-01",
            title="Open Acre Lot",
            property_type="land",
            listing_type="sale",
            price=75000.0,
            address="Rural Route 9",
            city="Scranton",
            area_sqft=43560.0,
            agent_code="AGT-01"
        )

        market = self.service.generate_market_report()
        self.assertEqual(market["total_properties"], 3)
        self.assertEqual(market["sold_count"], 1)
        self.assertEqual(market["rented_count"], 1)
        self.assertEqual(market["available_count"], 1)
        self.assertEqual(market["total_sales_volume"], 200000.0)
        self.assertEqual(market["total_rental_volume"], 1500.0)
        self.assertEqual(market["total_commissions_earned"], 6045.0)  # 6000 + 45

        agent_rep = self.service.generate_agent_performance_report()
        dwight = next(a for a in agent_rep if a["agent_code"] == "AGT-01")
        self.assertEqual(dwight["deals_closed"], 2)
        self.assertEqual(dwight["commissions_earned"], 6045.0)


if __name__ == "__main__":
    unittest.main()
