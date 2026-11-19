#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Water Delivery Management System.
"""

import sys
from delivery_service import DeliveryService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_order_card(order: dict):
    print("\n" + "-" * 60)
    print(f"  WATER DELIVERY ORDER #{order['order_number']}")
    print(f"  Customer: {order['customer_name']} ({order['customer_code']}) | Tel: {order['customer_phone']}")
    print(f"  Address:  {order['delivery_address']}")
    print("-" * 60)
    print(f"  Container Type:       {order['container_type']}")
    print(f"  Quantity:             {order['quantity']} units @ ${order['container_unit_price']:.2f}")
    print(f"  Delivery Fee:         ${order['delivery_fee']:.2f}")
    print(f"  TOTAL CHARGE:         ${order['total_charge']:.2f}")
    print("-" * 60)
    driver = f"{order['driver_name']} ({order['vehicle_plate']})" if order.get("driver_name") else "Unassigned"
    print(f"  Assigned Driver:      {driver}")
    print(f"  Delivery Status:      {order['status']}")
    print(f"  Payment Status:       {order['payment_status']} ({order.get('payment_method') or 'N/A'})")
    print(f"  Order Date:           {order['order_date']}")
    if order.get("notes"):
        print(f"  Special Instructions: {order['notes']}")
    print("-" * 60)


def main():
    service = DeliveryService()

    while True:
        print("\n" + "#" * 65)
        print("  WATER DELIVERY MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Customer")
        print(" 2. Register Delivery Driver")
        print(" 3. Create Water Delivery Order")
        print(" 4. Assign Order to Driver")
        print(" 5. Update Delivery Status")
        print(" 6. Record Order Payment")
        print(" 7. View Deliveries (Pending / Completed / All)")
        print(" 8. Search / View Order Details")
        print(" 9. Generate Daily Sales & Delivery Report")
        print(" 10. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-10): ").strip()

        if choice == "1":
            print_header("REGISTER CUSTOMER")
            code = input("Enter customer code (e.g. C-101): ").strip()
            name = input("Enter customer full name: ").strip()
            phone = input("Enter phone number: ").strip()
            addr = input("Enter delivery address: ").strip()
            try:
                c = service.register_customer(code, name, phone, addr)
                print(f"\n[Success] Customer '{c['name']}' ({c['customer_code']}) registered!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER DELIVERY DRIVER")
            code = input("Enter driver code (e.g. DRV-01): ").strip()
            name = input("Enter driver name: ").strip()
            phone = input("Enter driver phone: ").strip()
            plate = input("Enter vehicle license plate: ").strip()
            try:
                d = service.register_driver(code, name, phone, plate)
                print(f"\n[Success] Driver '{d['name']}' ({d['driver_code']}) registered! Vehicle: {d['vehicle_plate']}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("CREATE WATER ORDER")
            c_code = input("Enter customer code: ").strip()
            print("Select Container Type:")
            print("  1: 20L Jug ($4.50)")
            print("  2: 10L Dispenser ($3.00)")
            print("  3: 5L Bottle Pack ($6.00)")
            c_opt = input("Choice (1-3): ").strip()
            type_map = {"1": "20L Jug", "2": "10L Dispenser", "3": "5L Bottle Pack"}
            ctype = type_map.get(c_opt, "20L Jug")

            try:
                qty = int(input("Enter number of containers: ").strip())
                addr = input("Delivery address (or press Enter for default address): ").strip()
                date_in = input("Order date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Delivery notes / instructions (optional): ").strip()

                order = service.create_order(c_code, ctype, qty, addr or None, date_in or None, notes)
                print(f"\n[Success] Order #{order['order_number']} created successfully!")
                print_order_card(order)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("ASSIGN DRIVER TO ORDER")
            ord_num = input("Enter order number: ").strip()
            drv_code = input("Enter driver code: ").strip()
            try:
                updated = service.assign_driver(ord_num, drv_code)
                print(f"\n[Success] Order #{ord_num} assigned to driver '{updated['driver_name']}'!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("UPDATE DELIVERY STATUS")
            ord_num = input("Enter order number: ").strip()
            print("Statuses: 1: Out For Delivery, 2: Delivered, 3: Cancelled")
            opt = input("Choice (1-3): ").strip()
            s_map = {"1": "Out For Delivery", "2": "Delivered", "3": "Cancelled"}
            status = s_map.get(opt, "")
            try:
                updated = service.update_delivery_status(ord_num, status)
                print(f"\n[Success] Order #{ord_num} status updated to '{updated['status']}'!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("RECORD ORDER PAYMENT")
            ord_num = input("Enter order number: ").strip()
            method = input("Enter payment method (Cash, Card, Transfer, default Cash): ").strip() or "Cash"
            try:
                updated = service.record_payment(ord_num, method)
                print(f"\n[Success] Order #{ord_num} payment marked as Paid via {updated['payment_method']}!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("VIEW DELIVERIES")
            print("1: Pending / In-Transit, 2: Completed (Delivered), 3: All")
            f_choice = input("Filter choice (1-3) [Default 1]: ").strip()
            f_map = {"1": "Pending", "2": "Completed", "3": None}
            filter_val = f_map.get(f_choice, "Pending")

            deliveries = service.get_deliveries(filter_val)
            if not deliveries:
                print("No deliveries found.")
            else:
                print(f"{'Order #':<12} {'Customer':<18} {'Containers':>10} {'Total':>9} {'Driver':<14} {'Status':<16} {'Payment':<8}")
                print("-" * 92)
                for d in deliveries:
                    drv = d['driver_name'] or "Unassigned"
                    qty_str = f"{d['quantity']}x {d['container_type'][:3]}"
                    print(f"{d['order_number']:<12} {d['customer_name'][:17]:<18} {qty_str:>10} ${d['total_charge']:>8.2f} {drv[:13]:<14} {d['status']:<16} {d['payment_status']:<8}")

        elif choice == "8":
            print_header("ORDER DETAILS")
            ord_num = input("Enter order number: ").strip()
            try:
                order = service.get_order(ord_num)
                print_order_card(order)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "9":
            print_header("DAILY SALES REPORT")
            d_str = input("Enter report date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                report = service.generate_daily_sales_report(d_str or None)
                print(f"\n--- Daily Sales Report for {report['report_date']} ---")
                print(f"Paid Orders:           {report['paid_orders_count']:>8}")
                print(f"Containers Delivered:  {report['total_containers_sold']:>8}")
                print(f"Total Sales Revenue:  ${report['total_revenue']:>11,.2f}")

                if report["breakdown_by_container"]:
                    print("\nContainers Sold:")
                    for c in report["breakdown_by_container"]:
                        print(f"  - {c['container_type']}: {c['containers_sold']} units (${c['revenue']:.2f})")

                if report["driver_deliveries"]:
                    print("\nCompleted Deliveries by Driver:")
                    for drv in report["driver_deliveries"]:
                        print(f"  - {drv['driver_name']}: {drv['deliveries_completed']} trip(s)")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "10":
            print("\nExiting Water Delivery Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 10.")


if __name__ == "__main__":
    main()
