#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Agricultural Produce Trading System.
"""

import sys
from trading_service import TradingService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = TradingService()

    while True:
        print("\n" + "#" * 65)
        print("  AGRICULTURAL PRODUCE TRADING SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Farmer / Supplier")
        print(" 2. Register Buyer")
        print(" 3. Add Agricultural Produce")
        print(" 4. Restock Existing Produce")
        print(" 5. Process Purchase / Sale")
        print(" 6. View Available Produce Inventory")
        print(" 7. Generate Produce Sales Report")
        print(" 8. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            print_header("REGISTER FARMER / SUPPLIER")
            code = input("Enter farmer code (e.g. FARM-101): ").strip()
            name = input("Enter farmer/farm name: ").strip()
            loc = input("Enter farm location / district: ").strip()
            phone = input("Enter phone number: ").strip()
            try:
                f = service.register_farmer(code, name, loc, phone)
                print(f"\n[Success] Farmer '{f['name']}' ({f['farmer_code']}) in {f['location']} registered successfully!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER BUYER")
            code = input("Enter buyer code (e.g. BUY-101): ").strip()
            name = input("Enter contact person name: ").strip()
            comp = input("Enter buyer business/store name (optional): ").strip()
            phone = input("Enter phone number: ").strip()
            try:
                b = service.register_buyer(code, name, phone, comp)
                print(f"\n[Success] Buyer '{b['name']}' ({b['buyer_code']}) registered successfully!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("ADD AGRICULTURAL PRODUCE")
            f_code = input("Enter farmer code: ").strip()
            p_code = input("Enter produce code (e.g. PRD-CASSAVA): ").strip()
            name = input("Enter produce name (e.g. White Cassava Tubers): ").strip()
            cat = input("Enter category (Grains, Tubers, Vegetables, Legumes, Fruits): ").strip()
            unit = input("Enter unit of measurement (kg, bag, crate, ton): ").strip()
            try:
                qty = float(input(f"Enter available quantity ({unit}): ").strip())
                price = float(input(f"Enter selling price per {unit} ($): ").strip())
                p = service.add_produce(f_code, p_code, name, cat, unit, qty, price)
                print(f"\n[Success] Produce '{p['name']}' ({p['produce_code']}) listed! Stock: {p['available_quantity']} {p['unit']} @ ${p['price_per_unit']:.2f}/{p['unit']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("RESTOCK PRODUCE")
            p_code = input("Enter produce code: ").strip()
            try:
                qty = float(input("Enter additional quantity to add: ").strip())
                updated = service.restock_produce(p_code, qty)
                print(f"\n[Success] Restocked '{updated['name']}'! New available stock: {updated['available_quantity']} {updated['unit']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("PROCESS PURCHASE / SALE")
            b_code = input("Enter buyer code: ").strip()
            p_code = input("Enter produce code: ").strip()
            try:
                qty = float(input("Enter purchase quantity: ").strip())
                s_date = input("Enter sale date (YYYY-MM-DD or Enter for today): ").strip()
                inv = service.process_purchase(b_code, p_code, qty, s_date or None)
                print(f"\n[Transaction Successful] Invoice #{inv['invoice_number']}")
                print(f"Buyer:       {inv['buyer_name']}")
                print(f"Produce:     {inv['produce_name']} (Supplier: {inv['farmer_name']})")
                print(f"Quantity:    {inv['quantity']} {inv['unit']} @ ${inv['unit_price']:.2f}/{inv['unit']}")
                print(f"Total Sale:  ${inv['total_price']:,.2f}")
                print(f"Stock Left:  {inv['remaining_stock']} {inv['unit']}")
            except ValueError as e:
                print(f"\n[Purchase Failed] {e}")

        elif choice == "6":
            print_header("PRODUCE INVENTORY DIRECTORY")
            cat = input("Filter by category (or Enter for all): ").strip()
            items = service.list_produce_inventory(cat or None)
            if not items:
                print("No produce inventory listed.")
            else:
                print(f"{'Code':<12} {'Produce Name':<22} {'Category':<12} {'Stock':>10} {'Unit':<6} {'Price/Unit':>11} {'Farmer':<16}")
                print("-" * 92)
                for itm in items:
                    print(f"{itm['produce_code']:<12} {itm['name'][:21]:<22} {itm['category']:<12} {itm['available_quantity']:>10.1f} {itm['unit']:<6} ${itm['price_per_unit']:>10.2f} {itm['farmer_name'][:15]:<16}")

        elif choice == "7":
            print_header("PRODUCE SALES REPORT")
            start = input("Enter start date (YYYY-MM-DD or Enter for all): ").strip()
            end = input("Enter end date (YYYY-MM-DD or Enter for all): ").strip()
            try:
                report = service.generate_sales_report(start or None, end or None)
                print(f"\n--- Sales Performance: {report['period']} ---")
                print(f"Total Transactions:   {report['transaction_count']:>10}")
                print(f"Total Volume Sold:    {report['total_volume_sold']:>10.2f}")
                print(f"Total Gross Revenue: ${report['total_revenue']:>10,.2f}")

                if report["sales_by_produce"]:
                    print("\nRevenue by Produce:")
                    for p in report["sales_by_produce"]:
                        print(f"  * {p['produce_name']}: {p['volume_sold']} {p['unit']} sold (${p['revenue']:,.2f})")

                if report["sales_by_buyer"]:
                    print("\nTop Buyers:")
                    for b in report["sales_by_buyer"]:
                        comp_str = f" ({b['company']})" if b['company'] else ""
                        print(f"  * {b['buyer_name']}{comp_str}: {b['purchases_count']} order(s), ${b['spent']:,.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "8":
            print("\nExiting Agricultural Produce Trading System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
