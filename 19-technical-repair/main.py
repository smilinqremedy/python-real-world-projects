#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Technical Repair Service Management System.
"""

import sys
from repair_service import RepairService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_repair_docket(r: dict):
    print("\n" + "-" * 60)
    print(f"  REPAIR DOCKET #{r['reference_number']}")
    print(f"  Customer: {r['customer_name']} ({r['customer_code']}) | Phone: {r['customer_phone']}")
    print(f"  Device:   {r['brand']} {r['model']} ({r['device_type']})")
    if r.get("serial_number"):
        print(f"  Serial:   {r['serial_number']}")
    print(f"  Problem:  {r['problem_description']}")
    print("-" * 60)
    tech = f"{r['technician_name']} ({r['tech_specialty']})" if r.get("technician_name") else "Unassigned"
    print(f"  Technician:    {tech}")
    print(f"  Status:        {r['status']}")
    print(f"  Received Date: {r['received_date']}")
    if r.get("completed_date"):
        print(f"  Completed:     {r['completed_date']}")
    if r.get("collected_date"):
        print(f"  Collected:     {r['collected_date']}")
    print("-" * 60)
    print(f"  Parts Cost:    ${r['parts_cost']:>9.2f}")
    print(f"  Labor Cost:    ${r['labor_cost']:>9.2f}")
    print(f"  TOTAL CHARGE:  ${r['total_cost']:>9.2f}")
    print(f"  Amount Paid:   ${r['amount_paid']:>9.2f} [{'PAID' if r['is_paid'] else 'PENDING'}]")
    print(f"  Balance Due:   ${r['balance_due']:>9.2f}")
    print("-" * 60)


def main():
    service = RepairService()

    while True:
        print("\n" + "#" * 65)
        print("  TECHNICAL REPAIR SERVICE MANAGEMENT - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Customer")
        print(" 2. Register Technician")
        print(" 3. Check In Device for Repair")
        print(" 4. Assign Repair to Technician")
        print(" 5. Record / Update Repair Costs")
        print(" 6. Record Customer Payment")
        print(" 7. Update Repair Status")
        print(" 8. Search & View Repair Records")
        print(" 9. Generate Repair & Revenue Report")
        print(" 10. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-10): ").strip()

        if choice == "1":
            print_header("REGISTER CUSTOMER")
            code = input("Enter customer code (e.g. CUST-01): ").strip()
            name = input("Enter full name: ").strip()
            phone = input("Enter phone: ").strip()
            email = input("Enter email (optional): ").strip()
            try:
                c = service.register_customer(code, name, phone, email)
                print(f"\n[Success] Customer '{c['name']}' ({c['customer_code']}) registered successfully!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER TECHNICIAN")
            code = input("Enter technician code (e.g. TECH-01): ").strip()
            name = input("Enter technician name: ").strip()
            spec = input("Enter specialty (Smartphones, Laptops, Boards): ").strip()
            phone = input("Enter phone number: ").strip()
            try:
                t = service.register_technician(code, name, spec, phone)
                print(f"\n[Success] Technician '{t['name']}' ({t['tech_code']}) registered! Specialty: {t['specialty']}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("CHECK IN DEVICE FOR REPAIR")
            c_code = input("Enter customer code: ").strip()
            dtype = input("Enter device type (Smartphone, Laptop, Tablet, Console): ").strip()
            brand = input("Enter brand (Apple, Dell, Samsung, HP): ").strip()
            model = input("Enter model (e.g. iPhone 13, XPS 15): ").strip()
            serial = input("Enter serial number (optional): ").strip()
            problem = input("Describe fault / issue: ").strip()
            try:
                rep = service.check_in_device(c_code, dtype, brand, model, problem, serial)
                print(f"\n[Success] Device checked in! Reference Number: #{rep['reference_number']}")
                print_repair_docket(rep)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("ASSIGN TECHNICIAN")
            ref = input("Enter repair reference number: ").strip()
            tech = input("Enter technician code: ").strip()
            try:
                rep = service.assign_technician(ref, tech)
                print(f"\n[Success] Assigned to {rep['technician_name']}! Status: {rep['status']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("RECORD / UPDATE REPAIR COSTS")
            ref = input("Enter repair reference number: ").strip()
            try:
                parts = float(input("Enter replacement parts cost ($): ").strip())
                labor = float(input("Enter labor fee ($): ").strip())
                rep = service.set_repair_costs(ref, parts, labor)
                print(f"\n[Success] Cost recorded! Total Charge: ${rep['total_cost']:.2f}")
                print_repair_docket(rep)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("RECORD CUSTOMER PAYMENT")
            ref = input("Enter repair reference number: ").strip()
            try:
                amt = float(input("Enter payment amount ($): ").strip())
                rep = service.record_payment(ref, amt)
                paid_str = "PAID IN FULL" if rep['is_paid'] else f"PARTIAL (Balance: ${rep['balance_due']:.2f})"
                print(f"\n[Success] Payment of ${amt:.2f} logged! Status: {paid_str}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("UPDATE REPAIR STATUS")
            ref = input("Enter repair reference number: ").strip()
            print("Status Options: 1: Diagnosing, 2: Repairing, 3: Completed, 4: Collected")
            opt = input("Choice (1-4): ").strip()
            s_map = {"1": "Diagnosing", "2": "Repairing", "3": "Completed", "4": "Collected"}
            status = s_map.get(opt, "")
            try:
                rep = service.update_repair_status(ref, status)
                print(f"\n[Success] Status for #{ref} updated to '{rep['status']}'!")
                print_repair_docket(rep)
            except ValueError as e:
                print(f"\n[Status Update Blocked] {e}")

        elif choice == "8":
            print_header("SEARCH REPAIR RECORDS")
            query = input("Enter reference number, customer name, brand, or model: ").strip()
            results = service.search_repairs(query)
            if not results:
                print(f"No records matching '{query}'.")
            else:
                print(f"{'Ref #':<12} {'Customer':<16} {'Device':<18} {'Technician':<14} {'Cost':>8} {'Paid?':<6} {'Status':<12}")
                print("-" * 88)
                for r in results:
                    dev = f"{r['brand']} {r['model']}"
                    tech = r['technician_name'] or "Unassigned"
                    paid_flag = "Yes" if r['is_paid'] else "No"
                    print(f"{r['reference_number']:<12} {r['customer_name'][:15]:<16} {dev[:17]:<18} {tech[:13]:<14} ${r['total_cost']:>7.2f} {paid_flag:<6} {r['status']:<12}")

        elif choice == "9":
            print_header("REPAIR & REVENUE REPORT")
            rep = service.generate_report()
            print(f"Total Repairs Processed: {rep['total_repairs_logged']}")
            print("\nPipeline Status Breakdown:")
            for stat, cnt in rep["status_breakdown"].items():
                print(f"  - {stat:<15}: {cnt}")

            fin = rep["financials"]
            print(f"\nFinancial Summary:")
            print(f"  Parts Revenue:    ${fin['parts_revenue']:>10,.2f}")
            print(f"  Labor Revenue:    ${fin['labor_revenue']:>10,.2f}")
            print(f"  Total Invoiced:   ${fin['total_billed']:>10,.2f}")
            print(f"  Total Collected:  ${fin['total_collected']:>10,.2f}")
            print(f"  Outstanding Debt: ${fin['outstanding_debt']:>10,.2f}")

            if rep["technician_performance"]:
                print("\nTechnician Productivity:")
                for t in rep["technician_performance"]:
                    print(f"  * {t['tech_name']}: {t['jobs_completed']} jobs completed out of {t['jobs_assigned']} assigned")

        elif choice == "10":
            print("\nExiting Technical Repair Service Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 10.")


if __name__ == "__main__":
    main()
