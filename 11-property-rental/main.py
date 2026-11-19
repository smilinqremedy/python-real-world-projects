#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Property Rental Management System.
"""

import sys
from rental_service import RentalService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = RentalService()

    while True:
        print("\n" + "#" * 65)
        print("  PROPERTY RENTAL MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register New Property")
        print(" 2. Add Tenant & Assign to Property")
        print(" 3. Record Monthly Rent Payment")
        print(" 4. View Tenant Balances & Overdue Rent")
        print(" 5. Display Properties (All / Vacant / Occupied)")
        print(" 6. Search Tenants by Name or Property")
        print(" 7. Generate Monthly Rent Collection Report")
        print(" 8. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            print_header("REGISTER NEW PROPERTY")
            code = input("Enter property code (e.g. PROP-101): ").strip()
            name = input("Enter property name (e.g. Sunset Heights #4B): ").strip()
            address = input("Enter address: ").strip()
            try:
                rent = float(input("Enter monthly rent ($): ").strip())
                prop = service.register_property(code, name, address, rent)
                print(f"\n[Success] Property '{prop['property_code']}' registered successfully! Status: {prop['status']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("ADD TENANT & ASSIGN PROPERTY")
            code = input("Enter tenant code (e.g. TEN-001): ").strip()
            name = input("Enter tenant full name: ").strip()
            email = input("Enter tenant email: ").strip()
            phone = input("Enter tenant phone: ").strip()
            lease_date = input("Enter lease start date (YYYY-MM-DD): ").strip()
            prop_code = input("Enter property code to assign (or press Enter to skip): ").strip()
            try:
                tenant = service.add_tenant(code, name, email, phone, lease_date, prop_code or None)
                assigned = f"assigned to property '{prop_code.upper()}'" if prop_code else "unassigned"
                print(f"\n[Success] Tenant '{tenant['name']}' ({tenant['tenant_code']}) added and {assigned}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD MONTHLY RENT PAYMENT")
            t_code = input("Enter tenant code (e.g. TEN-001): ").strip()
            try:
                amt = float(input("Enter payment amount ($): ").strip())
                period = input("Enter rent period month (YYYY-MM, e.g. 2026-11): ").strip()
                p_date = input("Enter payment date (YYYY-MM-DD or press Enter for today): ").strip()
                notes = input("Enter payment notes (optional): ").strip()
                payment = service.record_rent_payment(t_code, amt, period, p_date or None, notes)
                print(f"\n[Success] Payment recorded! Ref: {payment['payment_ref']} | Amount: ${payment['amount']:,.2f} | Month: {payment['period_month']}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("TENANT BALANCES & OUTSTANDING RENT")
            as_of = input("Enter as-of date (YYYY-MM-DD or press Enter for today): ").strip()
            try:
                balances = service.get_tenant_balances(as_of or None)
                if not balances:
                    print("No active tenants found.")
                else:
                    print(f"{'Code':<9} {'Tenant Name':<18} {'Property':<10} {'Rent/Mo':>10} {'Total Due':>12} {'Total Paid':>12} {'Outstanding':>13} {'Status':<10}")
                    print("-" * 92)
                    for b in balances:
                        print(f"{b['tenant_code']:<9} {b['name'][:17]:<18} {b['property_code']:<10} ${b['monthly_rent']:>9.2f} ${b['total_expected']:>11.2f} ${b['total_paid']:>11.2f} ${b['outstanding_balance']:>12.2f} {b['status']:<10}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("DISPLAY PROPERTIES")
            filter_choice = input("Filter by status? (1: All, 2: Vacant, 3: Occupied) [Default 1]: ").strip()
            status_map = {"2": "Vacant", "3": "Occupied"}
            status = status_map.get(filter_choice, None)

            props = service.list_properties(status)
            if not props:
                print("No properties found.")
            else:
                print(f"{'Code':<10} {'Name':<22} {'Rent/Mo':>10} {'Status':<10} {'Current Tenant':<20}")
                print("-" * 76)
                for p in props:
                    tenant_info = f"{p['tenant_name']} ({p['tenant_code']})" if p['tenant_name'] else "None"
                    print(f"{p['property_code']:<10} {p['name'][:21]:<22} ${p['monthly_rent']:>9.2f} {p['status']:<10} {tenant_info:<20}")

        elif choice == "6":
            print_header("SEARCH TENANTS")
            query = input("Enter tenant name, tenant code, or property name/code: ").strip()
            if not query:
                print("Search query cannot be empty.")
                continue
            tenants = service.search_tenants(query)
            if not tenants:
                print(f"No tenants matching '{query}'.")
            else:
                print(f"{'Code':<9} {'Tenant Name':<18} {'Phone':<14} {'Property':<10} {'Monthly Rent':>12} {'Lease Start':<12}")
                print("-" * 80)
                for t in tenants:
                    p_code = t['property_code'] or "None"
                    rent_str = f"${t['monthly_rent']:,.2f}" if t['monthly_rent'] else "N/A"
                    print(f"{t['tenant_code']:<9} {t['name'][:17]:<18} {t['phone']:<14} {p_code:<10} {rent_str:>12} {t['lease_start_date']:<12}")

        elif choice == "7":
            print_header("MONTHLY RENT COLLECTION REPORT")
            month = input("Enter month (YYYY-MM, e.g. 2026-11): ").strip()
            try:
                report = service.generate_monthly_report(month)
                print(f"\n--- Rent Collection Report for {report['period_month']} ---")
                print(f"Total Expected Rent:     ${report['expected_rent']:>12,.2f}")
                print(f"Total Collected Rent:    ${report['collected_rent']:>12,.2f}")
                print(f"Outstanding Deficit:     ${report['outstanding_deficit']:>12,.2f}")
                print(f"Collection Rate:          {report['collection_rate_percent']:>11.1f}%")
                print(f"Payments Processed:       {report['payments_count']:>12}")

                if report["payments"]:
                    print("\nTransactions:")
                    print(f"{'Ref':<14} {'Tenant':<18} {'Property':<10} {'Amount':>10} {'Date':<12}")
                    print("-" * 68)
                    for pay in report["payments"]:
                        print(f"{pay['payment_ref']:<14} {pay['tenant_name'][:17]:<18} {pay['property_code']:<10} ${pay['amount']:>9.2f} {pay['payment_date']:<12}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "8":
            print("\nExiting Property Rental Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
