#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Logistics and Shipment Tracking System.
"""

import sys
from logistics_service import LogisticsService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_waybill(s: dict):
    print("\n" + "-" * 60)
    print(f"  WAYBILL: #{s['tracking_number']}")
    print(f"  Tier:     {s['shipping_tier']} | Created: {s['created_date']}")
    print("-" * 60)
    print(f"  Sender:   {s['sender_name']} ({s['sender_code']}) | Tel: {s['sender_phone']}")
    print(f"  Origin:   {s['sender_address']}")
    print(f"  Receiver: {s['receiver_name']} | Tel: {s['receiver_phone']}")
    print(f"  Dest:     {s['receiver_address']}, {s['destination_city']}")
    print("-" * 60)
    print(f"  Parcel:   {s['parcel_description']} ({s['weight_kg']} kg)")
    print(f"  Freight:  ${s['delivery_fee']:.2f} [{s['payment_status']}]")
    courier = f"{s['courier_name']} ({s['courier_code']} - {s.get('vehicle_type', 'Vehicle')})" if s.get("courier_name") else "Unassigned"
    print(f"  Courier:  {courier}")
    print(f"  Status:   {s['status'].upper()}")
    if s.get("delivered_at"):
        print(f"  Delivered At: {s['delivered_at']}")
    print("-" * 60)
    if s.get("milestones"):
        print("  Milestone Audit Trail:")
        for m in s["milestones"]:
            print(f"    - [{m['timestamp']}] {m['status_update']} @ {m['location']}")
            print(f"      Remarks: {m['remarks']}")
    print("-" * 60)


def main():
    service = LogisticsService()

    while True:
        print("\n" + "#" * 65)
        print("  LOGISTICS & SHIPMENT TRACKING SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Customer")
        print(" 2. Register Courier")
        print(" 3. Create Shipment & Compute Delivery Fee")
        print(" 4. Assign Courier to Shipment")
        print(" 5. Update Shipment Status & Milestone Location")
        print(" 6. Record Freight Payment")
        print(" 7. Search & Track Shipment by Tracking #")
        print(" 8. View Shipments")
        print(" 9. Generate Logistics & Freight Report")
        print(" 10. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-10): ").strip()

        if choice == "1":
            print_header("REGISTER CUSTOMER")
            code = input("Enter customer code (e.g. C-101): ").strip()
            name = input("Enter customer full name: ").strip()
            phone = input("Enter phone number: ").strip()
            email = input("Enter email (optional): ").strip()
            addr = input("Enter sender primary address: ").strip()
            try:
                c = service.register_customer(code, name, phone, email, addr)
                print(f"\n[Success] Customer '{c['name']}' ({c['customer_code']}) registered successfully!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER COURIER")
            code = input("Enter courier code (e.g. CUR-01): ").strip()
            name = input("Enter courier full name: ").strip()
            phone = input("Enter phone number: ").strip()
            veh = input("Enter transport vehicle type (Motorcycle, Van, Truck): ").strip()
            try:
                cour = service.register_courier(code, name, phone, veh)
                print(f"\n[Success] Courier '{cour['name']}' ({cour['courier_code']}) registered! Vehicle: {cour['vehicle_type']}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("CREATE SHIPMENT")
            s_code = input("Enter sender customer code: ").strip()
            r_name = input("Enter receiver full name: ").strip()
            r_phone = input("Enter receiver phone: ").strip()
            r_addr = input("Enter receiver delivery address: ").strip()
            dest_city = input("Enter destination city / state: ").strip()
            desc = input("Enter parcel description (e.g. Electronics, Documents): ").strip()
            try:
                weight = float(input("Enter parcel weight (in kg): ").strip())
                print("Select Shipping Tier: 1: Standard, 2: Express, 3: Overnight")
                t_opt = input("Choice (1-3) [Default 1]: ").strip()
                t_map = {"1": "Standard", "2": "Express", "3": "Overnight"}
                tier = t_map.get(t_opt, "Standard")

                ship = service.create_shipment(s_code, r_name, r_phone, r_addr, dest_city, desc, weight, tier)
                print(f"\n[Success] Shipment Created! Tracking Number: {ship['tracking_number']}")
                print_waybill(ship)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("ASSIGN COURIER")
            trk = input("Enter tracking number (e.g. TRK-XXXXXX): ").strip()
            cour_code = input("Enter courier code (e.g. CUR-01): ").strip()
            try:
                updated = service.assign_courier(trk, cour_code)
                print(f"\n[Success] Courier '{updated['courier_name']}' assigned to shipment #{trk}!")
                print_waybill(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("UPDATE SHIPMENT STATUS & MILESTONE")
            trk = input("Enter tracking number: ").strip()
            print("Select Status: 1: In Transit, 2: Out for Delivery, 3: Delivered, 4: Cancelled")
            s_opt = input("Choice (1-4): ").strip()
            s_map = {"1": "In Transit", "2": "Out for Delivery", "3": "Delivered", "4": "Cancelled"}
            status = s_map.get(s_opt, "")

            loc = input("Enter current transit location / checkpoint (e.g. Chicago Hub): ").strip()
            remarks = input("Status update remarks: ").strip()
            try:
                updated = service.update_shipment_status(trk, status, loc, remarks)
                print(f"\n[Success] Shipment #{trk} updated to: {updated['status'].upper()}!")
                print_waybill(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("RECORD FREIGHT PAYMENT")
            trk = input("Enter tracking number: ").strip()
            try:
                updated = service.record_payment(trk)
                print(f"\n[Success] Freight payment of ${updated['delivery_fee']:.2f} confirmed as PAID!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("TRACK SHIPMENT")
            trk = input("Enter tracking number: ").strip()
            try:
                ship = service.get_shipment_details(trk)
                print_waybill(ship)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "8":
            print_header("VIEW SHIPMENTS")
            print("Filter: 1: All, 2: In Transit, 3: Out for Delivery, 4: Delivered, 5: Created")
            f_opt = input("Choice (1-5) [Default 1]: ").strip()
            f_map = {"2": "In Transit", "3": "Out for Delivery", "4": "Delivered", "5": "Created"}
            filter_val = f_map.get(f_opt, None)

            shipments = service.list_shipments(filter_val)
            if not shipments:
                print("No shipments found.")
            else:
                print(f"{'Tracking #':<14} {'Sender':<16} {'Destination':<16} {'Weight':>8} {'Fee':>8} {'Status':<16}")
                print("-" * 82)
                for s in shipments:
                    print(f"{s['tracking_number']:<14} {s['sender_name'][:15]:<16} {s['destination_city'][:15]:<16} {s['weight_kg']:>6.1f}kg ${s['delivery_fee']:>7.2f} {s['status']:<16}")

        elif choice == "9":
            print_header("LOGISTICS PERFORMANCE REPORT")
            rep = service.generate_logistics_report()
            print(f"Total Shipments Handled:      {rep['total_shipments']}")
            print(f"Total Cargo Weight:           {rep['total_weight_handled_kg']:,.1f} kg")
            print(f"Total Freight Invoiced:      ${rep['total_freight_invoiced']:>12,.2f}")
            print(f"Total Revenue Collected:     ${rep['total_freight_collected']:>12,.2f}")

            print("\nPipeline Status Breakdown:")
            for stat, cnt in rep["status_breakdown"].items():
                print(f"  - {stat:<18}: {cnt}")

            if rep["courier_performance"]:
                print("\nCourier Dispatch Metrics:")
                for cr in rep["courier_performance"]:
                    print(f"  * {cr['courier_name']} ({cr['vehicle_type']}): {cr['parcels_delivered']} delivered / {cr['parcels_assigned']} assigned")

        elif choice == "10":
            print("\nExiting Logistics and Shipment Tracking System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 10.")


if __name__ == "__main__":
    main()
