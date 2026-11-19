#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Pharmacy Inventory and Sales Management System.
"""

import sys
from pharmacy_service import PharmacyService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = PharmacyService()

    while True:
        print("\n" + "#" * 65)
        print("  PHARMACY INVENTORY & SALES SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Medicine")
        print(" 2. Record Medicine Purchase (Add Stock Batch)")
        print(" 3. Process Medicine Sale")
        print(" 4. View Low Stock Alerts")
        print(" 5. View Expiry Alerts (Expired & Expiring Soon)")
        print(" 6. View Pharmacy Batch Inventory")
        print(" 7. Generate Daily / Monthly Sales Report")
        print(" 8. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            print_header("REGISTER MEDICINE")
            code = input("Enter medicine code (e.g. MED-AMOX500): ").strip()
            name = input("Enter medicine brand / generic name: ").strip()
            cat = input("Enter category (Antibiotics, Analgesics, Antacids, Vitamins): ").strip()
            unit = input("Enter dispensing unit (Tablets, Capsules, Syrup, Ointment): ").strip()
            try:
                reorder = int(input("Enter reorder alert threshold (default 10): ").strip() or "10")
                med = service.register_medicine(code, name, cat, unit, reorder)
                print(f"\n[Success] Medicine '{med['name']}' ({med['medicine_code']}) registered! Reorder level: {med['reorder_level']} {med['unit']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("RECORD MEDICINE PURCHASE (ADD BATCH)")
            m_code = input("Enter medicine code: ").strip()
            b_num = input("Enter batch number (e.g. BCH-2026-01): ").strip()
            try:
                cost = float(input("Enter purchase cost price ($): ").strip())
                sell = float(input("Enter selling price ($): ").strip())
                qty = int(input("Enter purchase quantity: ").strip())
                mfg_date = input("Enter manufacture date (YYYY-MM-DD): ").strip()
                exp_date = input("Enter expiry date (YYYY-MM-DD): ").strip()
                batch = service.record_medicine_purchase(m_code, b_num, cost, sell, qty, mfg_date, exp_date)
                print(f"\n[Success] Batch '{batch['batch_number']}' added for {batch['medicine_name']}! Stock: {batch['quantity']} units | Expiry: {batch['expiry_date']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("PROCESS MEDICINE SALE")
            b_num = input("Enter batch number to dispense from: ").strip()
            try:
                qty = int(input("Enter quantity to dispense: ").strip())
                s_date = input("Enter sale date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Customer notes (optional): ").strip()
                sale = service.process_sale(b_num, qty, s_date or None, notes)
                print(f"\n[Sale Dispensed] Receipt #{sale['receipt_number']}")
                print(f"Medicine:    {sale['medicine_name']} (Batch: {sale['batch_number']})")
                print(f"Dispensed:   {sale['quantity']} {sale['unit']} @ ${sale['unit_price']:.2f}/{sale['unit']}")
                print(f"Total Bill:  ${sale['total_price']:,.2f}")
                print(f"Stock Left:  {sale['remaining_batch_stock']} {sale['unit']}")
            except ValueError as e:
                print(f"\n[Sale Blocked] {e}")

        elif choice == "4":
            print_header("LOW STOCK ALERTS")
            low_stock = service.get_low_stock_medicines()
            if not low_stock:
                print("Stock levels are healthy across all registered medicines.")
            else:
                print(f"{'Code':<14} {'Medicine Name':<24} {'Category':<14} {'Available':>10} {'Reorder At':>12}")
                print("-" * 78)
                for m in low_stock:
                    stock_str = f"{m['total_stock']} {m['unit']}"
                    reorder_str = f"{m['reorder_level']} {m['unit']}"
                    print(f"{m['medicine_code']:<14} {m['name'][:23]:<24} {m['category']:<14} {stock_str:>10} {reorder_str:>12}")

        elif choice == "5":
            print_header("EXPIRY ALERTS")
            as_of = input("Enter check date (YYYY-MM-DD or Enter for today): ").strip()
            alerts = service.get_expiry_alerts(30, as_of or None)

            if alerts["expired_batches"]:
                print(f"\n[CRITICAL WARNING] {len(alerts['expired_batches'])} Expired Batch(es) (DO NOT SELL):")
                print(f"{'Batch #':<14} {'Medicine Name':<22} {'Stock Left':>11} {'Expired On':<12}")
                print("-" * 62)
                for b in alerts["expired_batches"]:
                    print(f"{b['batch_number']:<14} {b['medicine_name'][:21]:<22} {b['current_quantity']:>11} {b['expiry_date']:<12}")
            else:
                print("\nNo expired batches found.")

            if alerts["approaching_expiry_batches"]:
                print(f"\n[WARNING] {len(alerts['approaching_expiry_batches'])} Batch(es) Expiring within 30 days:")
                print(f"{'Batch #':<14} {'Medicine Name':<22} {'Stock Left':>11} {'Expires On':<12}")
                print("-" * 62)
                for b in alerts["approaching_expiry_batches"]:
                    print(f"{b['batch_number']:<14} {b['medicine_name'][:21]:<22} {b['current_quantity']:>11} {b['expiry_date']:<12}")

        elif choice == "6":
            print_header("BATCH INVENTORY DIRECTORY")
            batches = service.list_inventory()
            if not batches:
                print("No inventory batches in stock.")
            else:
                print(f"{'Batch #':<14} {'Medicine':<20} {'Category':<12} {'Stock':>8} {'Price':>8} {'Expiry Date':<12}")
                print("-" * 78)
                for b in batches:
                    print(f"{b['batch_number']:<14} {b['medicine_name'][:19]:<20} {b['category']:<12} {b['current_quantity']:>8} ${b['selling_price']:>7.2f} {b['expiry_date']:<12}")

        elif choice == "7":
            print_header("SALES REPORT")
            print("1: Daily Report, 2: Monthly Report, 3: All-Time")
            r_opt = input("Choice (1-3) [Default 1]: ").strip()
            if r_opt == "2":
                month = input("Enter month (YYYY-MM, e.g. 2026-11): ").strip()
                report = service.generate_sales_report(target_month=month)
            elif r_opt == "3":
                report = service.generate_sales_report()
            else:
                day = input("Enter date (YYYY-MM-DD or Enter for today): ").strip()
                report = service.generate_sales_report(target_date=day or None)

            print(f"\n--- Sales Report for {report['period']} ---")
            print(f"Total Transactions: {report['transactions_count']:>8}")
            print(f"Total Units Sold:   {report['total_units_sold']:>8}")
            print(f"Gross Revenue:     ${report['total_revenue']:>11,.2f}")

            if report["sales_breakdown"]:
                print("\nBreakdown by Medicine:")
                for m in report["sales_breakdown"]:
                    print(f"  * {m['medicine_name']} ({m['category']}): {m['units_sold']} units dispensed (${m['revenue']:,.2f})")

        elif choice == "8":
            print("\nExiting Pharmacy Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
