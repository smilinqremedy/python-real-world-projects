#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Vehicle Maintenance Tracking System.
"""

import sys
from maintenance_service import MaintenanceService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = MaintenanceService()

    while True:
        print("\n" + "#" * 65)
        print("  VEHICLE MAINTENANCE TRACKING SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Vehicle")
        print(" 2. Update Vehicle Current Mileage")
        print(" 3. Record Maintenance Activity (Oil, Brakes, Servicing)")
        print(" 4. View Overdue Maintenance Activities")
        print(" 5. Search Vehicle & View Service History")
        print(" 6. Generate Maintenance Expense Report")
        print(" 7. List All Vehicles")
        print(" 8. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            print_header("REGISTER VEHICLE")
            reg = input("Enter vehicle registration number (e.g. ABC-1234): ").strip()
            make = input("Enter vehicle make (e.g. Toyota, Ford): ").strip()
            model = input("Enter vehicle model (e.g. Camry, F-150): ").strip()
            try:
                year = int(input("Enter vehicle year: ").strip())
                mileage = int(input("Enter current odometer mileage (miles): ").strip() or "0")
                v = service.register_vehicle(reg, make, model, year, mileage)
                print(f"\n[Success] Vehicle '{v['reg_number']}' ({v['year']} {v['make']} {v['model']}) registered!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("UPDATE MILEAGE")
            reg = input("Enter registration number: ").strip()
            try:
                miles = int(input("Enter updated odometer mileage: ").strip())
                v = service.update_mileage(reg, miles)
                print(f"\n[Success] Mileage updated for '{v['reg_number']}' to {v['current_mileage']} miles.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD MAINTENANCE ACTIVITY")
            reg = input("Enter vehicle registration number: ").strip()
            stype = input("Enter service type (e.g. Oil Change, Brake Service, Tire Rotation, Full Inspection): ").strip()
            try:
                cost = float(input("Enter maintenance cost ($): ").strip())
                serv_miles = int(input("Enter mileage at time of service: ").strip())
                s_date = input("Enter service date (YYYY-MM-DD or Enter for today): ").strip()
                due_date = input("Enter next due date (YYYY-MM-DD or Enter to skip): ").strip()
                due_miles_input = input("Enter next due mileage (or Enter to skip): ").strip()
                due_miles = int(due_miles_input) if due_miles_input else None
                provider = input("Enter service provider / mechanic shop: ").strip()
                notes = input("Enter service notes: ").strip()

                rec = service.record_maintenance(
                    reg, stype, cost, serv_miles, s_date or None,
                    due_date or None, due_miles, provider, notes
                )
                print(f"\n[Success] Maintenance record #{rec['id']} logged for '{rec['reg_number']}'! Cost: ${rec['cost']:.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("OVERDUE MAINTENANCE ALERT")
            as_of = input("Check as-of date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                overdue = service.get_overdue_maintenance(as_of or None)
                if not overdue:
                    print("All vehicles are up to date! No overdue maintenance found.")
                else:
                    print(f"Found {len(overdue)} overdue maintenance item(s):\n")
                    for item in overdue:
                        print(f"  * Vehicle: {item['reg_number']} ({item['vehicle']}) | Odometer: {item['current_mileage']} mi")
                        print(f"    Service: {item['service_type']} (Last performed: {item['last_service_date']})")
                        print(f"    Alert:   {item['overdue_reasons']}\n")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("SEARCH VEHICLE & SERVICE HISTORY")
            reg = input("Enter registration number: ").strip()
            try:
                v = service.get_vehicle_by_reg(reg)
                print(f"\n--- Vehicle Details: {v['reg_number']} ---")
                print(f"Make & Model:    {v['year']} {v['make']} {v['model']}")
                print(f"Current Mileage: {v['current_mileage']:,} miles")
                print(f"Total Spent:     ${v['total_maintenance_cost']:,.2f}")
                print(f"Service Records: {len(v['history'])}")

                if v["history"]:
                    print("\nMaintenance Log:")
                    print(f"{'Date':<12} {'Service Type':<20} {'Mileage':>9} {'Cost':>10} {'Next Due':<12}")
                    print("-" * 68)
                    for h in v["history"]:
                        n_due = h['next_due_date'] or (f"{h['next_due_mileage']} mi" if h['next_due_mileage'] else "--")
                        print(f"{h['service_date']:<12} {h['service_type'][:19]:<20} {h['mileage_at_service']:>9} ${h['cost']:>9.2f} {n_due:<12}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("MAINTENANCE EXPENSE REPORT")
            rep = service.generate_expense_report()
            print(f"Total Fleet Vehicles:   {rep['total_vehicles']}")
            print(f"Total Services Logged:  {rep['total_services_logged']}")
            print(f"Total Fleet Expenses:  ${rep['total_spent']:>12,.2f}")

            if rep["expenses_by_service_type"]:
                print("\nBreakdown by Service Type:")
                print(f"{'Category':<24} {'Count':>7} {'Expenditure':>14}")
                print("-" * 48)
                for cat in rep["expenses_by_service_type"]:
                    print(f"{cat['service_type'][:23]:<24} {cat['service_count']:>7} ${cat['category_spent']:>13,.2f}")

            if rep["expenses_by_vehicle"]:
                print("\nBreakdown by Vehicle:")
                print(f"{'Reg #':<12} {'Make/Model':<20} {'Services':>9} {'Expenditure':>14}")
                print("-" * 58)
                for veh in rep["expenses_by_vehicle"]:
                    v_name = f"{veh['make']} {veh['model']}"
                    print(f"{veh['reg_number']:<12} {v_name[:19]:<20} {veh['services_count']:>9} ${veh['vehicle_spent']:>13,.2f}")

        elif choice == "7":
            print_header("FLEET VEHICLE DIRECTORY")
            vehicles = service.search_vehicles("")
            if not vehicles:
                print("No vehicles registered.")
            else:
                print(f"{'Reg #':<12} {'Make':<15} {'Model':<15} {'Year':<6} {'Mileage':>10}")
                print("-" * 62)
                for v in vehicles:
                    print(f"{v['reg_number']:<12} {v['make'][:14]:<15} {v['model'][:14]:<15} {v['year']:<6} {v['current_mileage']:>9} mi")

        elif choice == "8":
            print("\nExiting Vehicle Maintenance Tracking System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
