"""
Command-Line Interface for Real Estate Property Listing and Search System.
"""
import sys
from property_service import PropertyService


def print_header(title):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def seed_demo_data(service):
    try:
        # Stakeholders
        service.register_owner("OWN-101", "Eleanor Vance", "eleanor@vanceproperties.com", "555-1101")
        service.register_owner("OWN-102", "Marcus Sterling", "marcus@sterlingholdings.com", "555-1102")

        service.register_agent("AGT-201", "Dwight Schrute", "dwight@realtyhub.com", "555-2201", commission_rate=3.0)
        service.register_agent("AGT-202", "Angela Martin", "angela@realtyhub.com", "555-2202", commission_rate=2.5)

        service.register_client("CLI-301", "Jim Halpert", "jim@buyer.com", "555-3301", budget_max=500000.0, preferred_type="house")
        service.register_client("CLI-302", "Pam Beesly", "pam@buyer.com", "555-3302", budget_max=2200.0, preferred_type="apartment")

        # Listings
        service.add_property(
            "PROP-01", "OWN-101", "Oakwood Suburban Colonial", "house", "sale",
            425000.0, "14 Oakwood Lane", "Scranton", 2600.0, 4, 2.5,
            "Spacious colonial with finished basement and fenced backyard.", "AGT-201"
        )
        service.add_property(
            "PROP-02", "OWN-101", "Downtown Loft Apartment", "apartment", "rent",
            1750.0, "120 Lackawanna Ave #3C", "Scranton", 850.0, 1, 1.0,
            "Renovated loft with exposed brick and stainless appliances.", "AGT-201"
        )
        service.add_property(
            "PROP-03", "OWN-102", "Hilltop Luxury Villa", "villa", "sale",
            750000.0, "5 Summit Ridge", "Dunmore", 4200.0, 5, 4.0,
            "Panoramic mountain views, heated pool, gourmet kitchen.", "AGT-202"
        )
        service.add_property(
            "PROP-04", "OWN-102", "Commercial Retail Front", "commercial", "rent",
            3200.0, "400 Main Street", "Scranton", 2100.0, 0, 2.0,
            "High foot-traffic street-level commercial space.", "AGT-202"
        )
        print(" Demo owners, agents, clients, and property listings seeded successfully!")
    except Exception as e:
        print(f" Demo seeding notice: {e}")


def handle_search(service):
    print_header("Search & Filter Properties")
    print("Leave options blank to search without that filter.")
    city = input("City (e.g. Scranton): ").strip()
    ptype = input("Property Type (apartment/house/commercial/land/villa): ").strip().lower()
    ltype = input("Listing Type (sale/rent): ").strip().lower()

    min_p_str = input("Min Price ($): ").strip()
    max_p_str = input("Max Price ($): ").strip()
    min_bed_str = input("Min Bedrooms: ").strip()

    sort_choice = input("Sort by (1: Price Asc, 2: Price Desc, 3: Largest Area, 4: Newest): ").strip()
    sort_keys = {"1": "price_asc", "2": "price_desc", "3": "area_desc", "4": "newest"}
    sort_by = sort_keys.get(sort_choice, "price_asc")

    try:
        results = service.search_properties(
            city=city or None,
            property_type=ptype or None,
            listing_type=ltype or None,
            min_price=float(min_p_str) if min_p_str else None,
            max_price=float(max_p_str) if max_p_str else None,
            min_bedrooms=int(min_bed_str) if min_bed_str else None,
            status="available",
            sort_by=sort_by
        )

        print(f"\nFound {len(results)} matching properties:")
        print("-" * 65)
        for r in results:
            price_fmt = f"${r['price']:,.2f}" if r["listing_type"] == "sale" else f"${r['price']:,.2f}/mo"
            print(f"[{r['listing_code']}] {r['title']} - {price_fmt}")
            print(f"   {r['property_type'].title()} | {r['bedrooms']} Beds | {r['bathrooms']} Baths | {r['area_sqft']} sqft")
            print(f"   Location: {r['address']}, {r['city']} | Agent: {r['agent_name'] or 'Unassigned'}")
    except Exception as e:
        print(f" Error: {e}")


def main():
    service = PropertyService()
    seed_demo_data(service)

    while True:
        print_header("Real Estate Property Listing & Search System")
        print("1. Register Property Owner")
        print("2. Register Real Estate Agent")
        print("3. Register Prospective Client / Buyer")
        print("4. Add New Property Listing")
        print("5. Search & Filter Properties")
        print("6. Record Customer Inquiry")
        print("7. Schedule Property Viewing")
        print("8. Complete Viewing with Feedback")
        print("9. Submit Price Offer")
        print("10. Review & Accept / Reject Offer (Close Deal)")
        print("11. Generate Real Estate Market Report")
        print("12. Generate Agent Performance Report")
        print("13. List All Properties")
        print("0. Exit")

        choice = input("\nEnter selection (0-13): ").strip()

        if choice == "1":
            code = input("Owner Code (e.g. OWN-103): ")
            name = input("Owner Name: ")
            email = input("Email Address: ")
            phone = input("Phone Number: ")
            try:
                service.register_owner(code, name, email, phone)
                print(f" Owner {code} registered successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "2":
            code = input("Agent Code (e.g. AGT-203): ")
            name = input("Agent Name: ")
            email = input("Email Address: ")
            phone = input("Phone Number: ")
            crate = float(input("Commission Rate % (e.g. 3.0): ") or "3.0")
            try:
                service.register_agent(code, name, email, phone, crate)
                print(f" Agent {code} registered successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "3":
            code = input("Client Code (e.g. CLI-303): ")
            name = input("Client Name: ")
            email = input("Email Address: ")
            phone = input("Phone Number: ")
            bmax = input("Max Budget ($ or Enter for none): ").strip()
            ptype = input("Preferred Property Type (or Enter for any): ").strip()
            try:
                service.register_client(code, name, email, phone, float(bmax) if bmax else None, ptype or None)
                print(f" Client {code} registered successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "4":
            lcode = input("Listing Code (e.g. PROP-05): ")
            ocode = input("Owner Code: ")
            title = input("Listing Title: ")
            ptype = input("Property Type (apartment/house/commercial/land/villa): ")
            ltype = input("Listing Type (sale/rent): ")
            try:
                price = float(input("Price ($): "))
                addr = input("Address: ")
                city = input("City: ")
                sqft = float(input("Area in Sqft: "))
                beds = int(input("Bedrooms (0 for commercial/land): ") or "0")
                baths = float(input("Bathrooms (0 for land): ") or "0.0")
                desc = input("Description: ")
                acode = input("Assigned Agent Code (optional): ").strip()
                service.add_property(lcode, ocode, title, ptype, ltype, price, addr, city, sqft, beds, baths, desc, acode or None)
                print(f" Property {lcode} added to inventory.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "5":
            handle_search(service)

        elif choice == "6":
            lcode = input("Property Listing Code: ")
            ccode = input("Client Code: ")
            msg = input("Inquiry Message: ")
            try:
                service.create_inquiry(lcode, ccode, msg)
                print(" Customer inquiry recorded.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "7":
            lcode = input("Property Listing Code: ")
            ccode = input("Client Code: ")
            vdate = input("Viewing Date & Time (YYYY-MM-DD HH:MM): ")
            acode = input("Agent Code (optional): ").strip()
            try:
                vid = service.schedule_viewing(lcode, ccode, vdate, acode or None)
                print(f" Viewing scheduled (ID #{vid}).")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "8":
            try:
                vid = int(input("Viewing ID: "))
                feed = input("Client Feedback: ")
                service.complete_viewing(vid, feed)
                print(f" Viewing #{vid} completed.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "9":
            lcode = input("Property Listing Code: ")
            ccode = input("Client Code: ")
            try:
                amt = float(input("Offer Amount ($): "))
                oid = service.make_offer(lcode, ccode, amt)
                print(f" Offer #{oid} submitted for ${amt:,.2f}.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "10":
            try:
                oid = int(input("Offer ID to respond to: "))
                decision = input("Decision (accepted / rejected / countered): ").strip().lower()
                res = service.respond_to_offer(oid, decision)
                print(f" Offer #{oid} decision recorded: {res['status'].upper()}")
                if res["status"] == "accepted":
                    print(f" Property status updated to '{res['property_status'].upper()}'.")
                    print(f" Agent Commission Earned: ${res['commission_earned']:,.2f}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "11":
            try:
                rep = service.generate_market_report()
                print_header("Real Estate Market & Inventory Report")
                print(f"Total Property Listings: {rep['total_properties']}")
                print(f"Available: {rep['available_count']} | Sold: {rep['sold_count']} | Rented: {rep['rented_count']}")
                print(f"Property Types: {rep['type_breakdown']}")
                print(f"Closed Sales Volume: ${rep['total_sales_volume']:,.2f} ({rep['sales_deals_closed']} deals)")
                print(f"Closed Rental Volume: ${rep['total_rental_volume']:,.2f} ({rep['rental_deals_closed']} deals)")
                print(f"Total Commissions Earned: ${rep['total_commissions_earned']:,.2f}")
                print(f"Avg Price / Sqft (Active Listings): ${rep['avg_price_per_sqft_available']:,.2f}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "12":
            try:
                perf = service.generate_agent_performance_report()
                print_header("Agent Performance & Commission Leaderboard")
                print(f"{'Code':<10} {'Name':<20} {'Listings':<10} {'Deals':<8} {'Volume Closed':<18} {'Commissions':<15}")
                print("-" * 75)
                for a in perf:
                    print(f"{a['agent_code']:<10} {a['name']:<20} {a['total_listings']:<10} {a['deals_closed']:<8} ${a['total_volume_closed']:<17,.2f} ${a['commissions_earned']:<14,.2f}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "13":
            props = service.search_properties(status=None)
            print(f"\nAll Properties in Inventory ({len(props)}):")
            print("-" * 65)
            for p in props:
                print(f"[{p['listing_code']}] {p['title']} - ${p['price']:,.2f} [{p['status'].upper()}] ({p['city']})")

        elif choice == "0":
            print("Exiting Real Estate Property System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice, please select 0-13.")


if __name__ == "__main__":
    main()
