#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Restaurant Order Management System.
"""

import sys
from order_service import OrderService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_receipt(details: dict):
    print("\n" + "-" * 55)
    print(f"  RECEIPT: Order #{details['order_number']}")
    print(f"  Customer: {details['customer_name']} | Table: {details['table_number']}")
    print(f"  Date: {details['order_date']} | Status: {details['order_status']} ({details['payment_status']})")
    print("-" * 55)
    if not details.get("items"):
        print("  [Order is empty]")
    else:
        print(f"  {'Item':<24} {'Qty':>5} {'Price':>10} {'Total':>10}")
        print("  " + "-" * 51)
        for item in details["items"]:
            print(f"  {item['name'][:23]:<24} {item['quantity']:>5} ${item['unit_price']:>9.2f} ${item['item_total']:>9.2f}")
    print("-" * 55)
    print(f"  Subtotal:              ${details['subtotal']:>10.2f}")
    if details['discount_percent'] > 0:
        print(f"  Discount ({details['discount_percent']:.1f}%):       -${details['discount_amount']:>10.2f}")
    print(f"  Tax (5%):              ${details['tax_amount']:>10.2f}")
    print(f"  TOTAL BILL:            ${details['total_bill']:>10.2f}")
    if details.get("amount_paid", 0) > 0:
        print(f"  Amount Paid:           ${details['amount_paid']:>10.2f}")
        if "change" in details:
            print(f"  Change Returned:       ${details['change']:>10.2f}")
    print("-" * 55)


def main():
    service = OrderService()

    while True:
        print("\n" + "#" * 65)
        print("  RESTAURANT ORDER MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. View Available Menu")
        print(" 2. Create New Customer Order")
        print(" 3. Add Meals to Order")
        print(" 4. Modify / Remove Meal in Order")
        print(" 5. Apply Discount to Order")
        print(" 6. View Order Bill & Details")
        print(" 7. Record Payment & Complete Order")
        print(" 8. View Orders (Pending / Completed / All)")
        print(" 9. Generate Daily Sales Report")
        print(" 10. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-10): ").strip()

        if choice == "1":
            print_header("AVAILABLE MENU")
            menu = service.get_menu(available_only=True)
            print(f"{'Code':<8} {'Item Name':<28} {'Category':<12} {'Price':>8}")
            print("-" * 60)
            for m in menu:
                print(f"{m['item_code']:<8} {m['name'][:27]:<28} {m['category']:<12} ${m['price']:>7.2f}")

        elif choice == "2":
            print_header("CREATE NEW ORDER")
            cust = input("Enter customer name: ").strip()
            tbl = input("Enter table number (e.g. T-04, Takeout): ").strip()
            try:
                order = service.create_order(cust, tbl)
                print(f"\n[Success] Created Order #{order['order_number']} for {order['customer_name']} at Table {order['table_number']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("ADD MEAL TO ORDER")
            ord_num = input("Enter order number (e.g. ORD-XXXXXX): ").strip()
            item_code = input("Enter menu item code (e.g. M-101): ").strip()
            try:
                qty = int(input("Enter quantity: ").strip())
                updated = service.add_meal_to_order(ord_num, item_code, qty)
                print_receipt(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("MODIFY OR REMOVE ITEM")
            ord_num = input("Enter order number: ").strip()
            item_code = input("Enter item code: ").strip()
            try:
                qty = int(input("Enter new quantity (0 to remove item): ").strip())
                updated = service.change_item_quantity(ord_num, item_code, qty)
                print_receipt(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("APPLY DISCOUNT")
            ord_num = input("Enter order number: ").strip()
            try:
                disc = float(input("Enter discount percentage (0-100%): ").strip())
                updated = service.apply_discount(ord_num, disc)
                print_receipt(updated)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("VIEW ORDER BILL")
            ord_num = input("Enter order number: ").strip()
            try:
                details = service.get_order_details(ord_num)
                print_receipt(details)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("PROCESS PAYMENT & COMPLETE ORDER")
            ord_num = input("Enter order number: ").strip()
            try:
                details = service.get_order_details(ord_num)
                print_receipt(details)
                amount = float(input(f"Enter cash/card amount tendered (Total: ${details['total_bill']:.2f}): ").strip())
                completed = service.record_payment(ord_num, amount)
                print("\n[Success] Payment Confirmed! Order Completed.")
                print_receipt(completed)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "8":
            print_header("VIEW ORDERS")
            opt = input("Filter orders? (1: All, 2: Pending, 3: Completed) [Default: 1]: ").strip()
            f_map = {"2": "Pending", "3": "Completed"}
            status = f_map.get(opt, None)

            orders = service.get_orders(status)
            if not orders:
                print("No orders found.")
            else:
                print(f"{'Order #':<12} {'Customer':<18} {'Table':<8} {'Total':>10} {'Payment':<10} {'Status':<10}")
                print("-" * 72)
                for o in orders:
                    print(f"{o['order_number']:<12} {o['customer_name'][:17]:<18} {o['table_number']:<8} ${o['total_bill']:>9.2f} {o['payment_status']:<10} {o['order_status']:<10}")

        elif choice == "9":
            print_header("DAILY SALES REPORT")
            d_str = input("Enter report date (YYYY-MM-DD or press Enter for today): ").strip()
            try:
                report = service.generate_daily_sales_report(d_str or None)
                print(f"\n--- Daily Sales Report for {report['report_date']} ---")
                print(f"Total Completed Orders: {report['total_completed_orders']:>10}")
                print(f"Total Revenue:         ${report['total_revenue']:>10.2f}")
                print(f"Total Tax Collected:   ${report['total_tax']:>10.2f}")
                print(f"Discounts Granted:     ${report['total_discounts']:>10.2f}")
                if report["top_items"]:
                    print("\nTop Selling Meals:")
                    for idx, itm in enumerate(report["top_items"], 1):
                        print(f"  {idx}. {itm['name']} - {itm['units_sold']} units (${itm['revenue']:.2f})")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "10":
            print("\nExiting Restaurant Order Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 10.")


if __name__ == "__main__":
    main()
