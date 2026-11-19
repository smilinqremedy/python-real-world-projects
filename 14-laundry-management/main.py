#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Laundry Service Management System.
"""

import sys
from laundry_service import LaundryService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_order_details(order: dict):
    print("\n" + "-" * 60)
    print(f"  LAUNDRY ORDER #{order['order_id']}")
    print(f"  Customer: {order['customer_name']} ({order['customer_code']}) | Tel: {order['customer_phone']}")
    print(f"  Date: {order['order_date']} | Status: {order['status']} | Payment: {order['payment_status']}")
    print("-" * 60)
    print(f"  {'Item Type':<20} {'Quantity':>8} {'Rate':>10} {'Subtotal':>12}")
    print("  " + "-" * 54)
    for itm in order["items"]:
        print(f"  {itm['item_type']:<20} {itm['quantity']:>8} ${itm['unit_price']:>9.2f} ${itm['subtotal']:>11.2f}")
    print("-" * 60)
    print(f"  Total Articles:        {order['total_items']:>12}")
    print(f"  Total Service Charge: ${order['total_charge']:>12.2f}")
    print(f"  Amount Paid:          ${order['amount_paid']:>12.2f}")
    print(f"  Remaining Balance:    ${order['outstanding_balance']:>12.2f}")
    if order.get("payments"):
        print("\n  Payment Records:")
        for p in order["payments"]:
            print(f"    - {p['payment_ref']} | ${p['amount']:.2f} via {p['payment_method']} on {p['payment_date']}")
    print("-" * 60)


def main():
    service = LaundryService()

    while True:
        print("\n" + "#" * 65)
        print("  LAUNDRY SERVICE MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Customer")
        print(" 2. View Service Price Rates")
        print(" 3. Create Laundry Order")
        print(" 4. Record Customer Payment")
        print(" 5. Update Order Status (Received -> Washing -> Ready -> Collected)")
        print(" 6. Search Order by Order ID")
        print(" 7. Display Pending Orders")
        print(" 8. Daily Revenue Report")
        print(" 9. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            print_header("REGISTER CUSTOMER")
            code = input("Enter customer code (e.g. CUST-101): ").strip()
            name = input("Enter full name: ").strip()
            phone = input("Enter phone number: ").strip()
            email = input("Enter email (optional): ").strip()
            try:
                c = service.register_customer(code, name, phone, email)
                print(f"\n[Success] Customer '{c['name']}' ({c['customer_code']}) registered successfully.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("SERVICE PRICE RATES")
            rates = service.get_service_rates()
            print(f"{'Item Category':<25} {'Service Price ($)':>18}")
            print("-" * 45)
            for r in rates:
                print(f"{r['item_type']:<25} ${r['price_per_item']:>17.2f}")

        elif choice == "3":
            print_header("CREATE LAUNDRY ORDER")
            cust_code = input("Enter customer code: ").strip()
            date_in = input("Enter order date (YYYY-MM-DD or Enter for today): ").strip()

            items = []
            print("\nEnter items to wash (Type 'done' when finished):")
            while True:
                itype = input("  Enter item type (e.g. Shirt, Suit, Dress, Trousers) or 'done': ").strip()
                if itype.lower() == "done":
                    break
                try:
                    qty = int(input(f"  Enter quantity for {itype}: ").strip())
                    items.append({"item_type": itype, "quantity": qty})
                except ValueError:
                    print("  [Error] Quantity must be an integer.")

            if not items:
                print("[Error] No items provided. Order cancelled.")
                continue

            try:
                order = service.create_order(cust_code, items, date_in or None)
                print(f"\n[Success] Order #{order['order_id']} created!")
                print_order_details(order)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("RECORD CUSTOMER PAYMENT")
            ord_id = input("Enter order ID (e.g. LND-XXXXXX): ").strip()
            try:
                amt = float(input("Enter payment amount ($): ").strip())
                method = input("Enter payment method (Cash/Card/Transfer, default Cash): ").strip() or "Cash"
                p_date = input("Enter payment date (YYYY-MM-DD or Enter for today): ").strip()
                updated = service.record_payment(ord_id, amt, p_date or None, method)
                print(f"\n[Success] Payment of ${amt:.2f} logged! Payment status: {updated['payment_status']}")
                print_order_details(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("UPDATE ORDER STATUS")
            ord_id = input("Enter order ID: ").strip()
            print("Status Options: 1: Received, 2: Washing, 3: Ready, 4: Collected")
            opt = input("Select status (1-4): ").strip()
            stat_map = {"1": "Received", "2": "Washing", "3": "Ready", "4": "Collected"}
            status = stat_map.get(opt, "")
            try:
                updated = service.update_order_status(ord_id, status)
                print(f"\n[Success] Order #{ord_id} status updated to: {updated['status']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("SEARCH ORDER")
            ord_id = input("Enter order ID: ").strip()
            try:
                order = service.get_order(ord_id)
                print_order_details(order)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("PENDING LAUNDRY ORDERS")
            pending = service.get_pending_orders()
            if not pending:
                print("No pending orders.")
            else:
                print(f"{'Order ID':<12} {'Date':<12} {'Customer':<18} {'Items':>6} {'Charge':>9} {'Paid':>9} {'Status':<10}")
                print("-" * 80)
                for o in pending:
                    print(f"{o['order_id']:<12} {o['order_date']:<12} {o['customer_name'][:17]:<18} {o['total_items']:>6} ${o['total_charge']:>8.2f} ${o['amount_paid']:>8.2f} {o['status']:<10}")

        elif choice == "8":
            print_header("DAILY REVENUE REPORT")
            d_str = input("Enter report date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                report = service.generate_daily_revenue_report(d_str or None)
                print(f"\n--- Daily Revenue Report for {report['report_date']} ---")
                print(f"Total Revenue Collected: ${report['total_revenue']:>12,.2f}")
                print(f"Payments Processed:       {report['total_payments_received']:>12}")
                print(f"Orders Placed:            {report['orders_placed_today']:>12}")
                print(f"Total Clothing Items:     {report['items_processed_today']:>12}")
                if report["payments"]:
                    print("\nTransactions:")
                    for p in report["payments"]:
                        print(f"  {p['payment_ref']} | ${p['amount']:.2f} ({p['payment_method']}) for Order #{p['order_id']} [{p['customer_name']}]")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "9":
            print("\nExiting Laundry Service Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()
