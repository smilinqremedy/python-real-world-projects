"""
Small Business Sales and Profit Analysis System - CLI Interface
Entry point for small business sales tracking, COGS accounting, operational expense monitoring, and profit reporting.
"""

import sys
from datetime import datetime
from database import initialize_database, EXPENSE_CATEGORIES, PRODUCT_CATEGORIES, DEFAULT_DB_FILE
from analytics_service import ProfitAnalyticsService


def display_menu():
    """Displays the interactive CLI menu."""
    print("\n" + "=" * 58)
    print("   SMALL BUSINESS SALES & PROFIT ANALYSIS SYSTEM (CLI)   ")
    print("=" * 58)
    print(" 1. Register New Product")
    print(" 2. Record Customer Sale")
    print(" 3. Record Operational Expense")
    print(" 4. View Financial Summary (Revenue, Expenses & Profit)")
    print(" 5. Identify Best-Selling Products")
    print(" 6. Generate Daily Sales Report")
    print(" 7. Generate Monthly Financial Report (P&L)")
    print(" 8. View Product Catalog & Update Pricing")
    print(" 9. View Recent Sales Log")
    print(" 10. View Operational Expenses Log")
    print(" 11. Exit System")
    print("=" * 58)


def handle_register_product(service):
    """Registers a new product with cost and selling price."""
    print("\n--- [Register New Product] ---")
    name = input("Enter product name: ").strip()
    if not name:
        print("[Error] Product name cannot be blank.")
        return

    print("\nSelect Product Category:")
    for idx, c in enumerate(PRODUCT_CATEGORIES, start=1):
        print(f"  {idx}. {c}")
    c_choice = input(f"Choose category (1-{len(PRODUCT_CATEGORIES)}) [default: 6]: ").strip()

    category = PRODUCT_CATEGORIES[-1]
    if c_choice.isdigit() and 1 <= int(c_choice) <= len(PRODUCT_CATEGORIES):
        category = PRODUCT_CATEGORIES[int(c_choice) - 1]

    cost_str = input("Enter purchase cost price ($): ").strip().lstrip("$£€")
    selling_str = input("Enter retail selling price ($): ").strip().lstrip("$£€")

    try:
        prod = service.register_product(name, cost_str, selling_str, category)
        margin = ((prod['selling_price'] - prod['cost_price']) / prod['selling_price'] * 100)
        print(f"\n✓ Product '{prod['product_name']}' registered successfully! (ID: {prod['product_id']})")
        print(f"  Cost Price:    ${prod['cost_price']:.2f}")
        print(f"  Selling Price: ${prod['selling_price']:.2f} (Target Margin: {margin:.1f}%)")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_record_sale(service):
    """Records a customer sale transaction."""
    print("\n--- [Record Customer Sale] ---")
    products = service.list_products()
    if not products:
        print("Product catalog is empty. Please register a product first.")
        return

    print("Product Catalog:")
    for p in products:
        print(f"  ID #{p['product_id']:<2}: {p['product_name']:<25} (Cost: ${p['cost_price']:.2f} | Price: ${p['selling_price']:.2f})")

    pid_str = input("\nEnter Product ID sold: ").strip()
    if not pid_str.isdigit():
        print("[Error] Product ID must be numeric.")
        return

    qty_str = input("Enter quantity sold: ").strip()
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter sale date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    price_override = input("Enter unit selling price [press Enter for standard price]: ").strip().lstrip("$£€")
    notes = input("Enter customer notes (optional): ").strip()

    try:
        sale = service.record_sale(
            product_id=int(pid_str),
            quantity=qty_str,
            sale_date=date_str,
            unit_selling_price=price_override if price_override else None,
            customer_notes=notes if notes else None
        )
        print("\n" + "=" * 50)
        print("                 SALE RECORDED")
        print("=" * 50)
        print(f" Sale ID:        #{sale['sale_id']}")
        print(f" Product:        {sale['product_name']}")
        print(f" Quantity:       {sale['quantity']} units @ ${sale['unit_selling_price']:.2f}")
        print(f" Total Revenue:  ${sale['total_revenue']:.2f}")
        print(f" Cost of Goods:  ${sale['total_cogs']:.2f}")
        print(f" Gross Profit:   ${sale['gross_profit']:.2f}")
        print("=" * 50)
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_record_expense(service):
    """Records an operational expense."""
    print("\n--- [Record Operational Expense] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter expense date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    print("\nSelect Expense Category:")
    for idx, cat in enumerate(EXPENSE_CATEGORIES, start=1):
        print(f"  {idx}. {cat}")
    c_choice = input(f"Choose category (1-{len(EXPENSE_CATEGORIES)}): ").strip()

    if not c_choice.isdigit() or not (1 <= int(c_choice) <= len(EXPENSE_CATEGORIES)):
        print("[Error] Invalid category selection.")
        return
    category = EXPENSE_CATEGORIES[int(c_choice) - 1]

    amount_str = input("Enter expense amount ($): ").strip().lstrip("$£€")
    description = input("Enter expense description / memo: ").strip()

    try:
        exp = service.record_operational_expense(date_str, category, amount_str, description)
        print(f"\n✓ Operating expense of ${exp['amount']:.2f} logged under '{exp['category']}'. (ID: #{exp['expense_id']})")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_financial_summary(service):
    """Displays total revenue, COGS, OPEX, and net profit summary."""
    summary = service.calculate_overall_financial_summary()

    print("\n" + "=" * 54)
    print("           OVERALL FINANCIAL & PROFIT SUMMARY")
    print("=" * 54)
    print(f" Total Sales Completed:       {summary['total_transactions']:>12}")
    print(f" Total Product Units Sold:    {summary['total_units_sold']:>12,}")
    print("-" * 54)
    print(f" TOTAL REVENUE (Inflow):     ${summary['total_revenue']:>14,.2f}")
    print(f" Cost of Goods Sold (COGS):  ${summary['total_cogs']:>14,.2f}")
    print("-" * 54)
    print(f" GROSS PROFIT:               ${summary['gross_profit']:>14,.2f}")
    print(f" Gross Profit Margin:         {summary['gross_margin_pct']:>13.2f}%")
    print("-" * 54)
    print(f" Total Operating Expenses:   ${summary['total_operational_expenses']:>14,.2f}")
    print(f" Total Overall Expenses:     ${summary['total_expenses']:>14,.2f}")
    print("=" * 54)
    net_status = "SURPLUS (Net Profit)" if summary['net_profit'] >= 0 else "DEFICIT (Net Loss)"
    print(f" NET PROFIT:                 ${summary['net_profit']:>14,.2f} [{net_status}]")
    print(f" Net Profit Margin:           {summary['net_margin_pct']:>13.2f}%")
    print("=" * 54)


def handle_bestsellers(service):
    """Displays best-selling products."""
    print("\n--- [Best-Selling Products Analysis] ---")
    print("Rank by:")
    print("  1. Total Units Sold")
    print("  2. Gross Revenue Generated")
    opt = input("Select ranking criterion (1/2) [default: 1]: ").strip()
    criterion = "revenue" if opt == "2" else "units"

    bestsellers = service.identify_best_selling_products(limit=10, rank_by=criterion)
    if not bestsellers:
        print("\nNo sales transactions recorded yet.")
        return

    print("\n" + "=" * 80)
    print(f"{'Rank':<5} | {'Product Name':<25} | {'Units Sold':<11} | {'Revenue ($)':<14} | {'Gross Profit ($)'}")
    print("-" * 80)
    for idx, p in enumerate(bestsellers, start=1):
        print(f"#{idx:<4} | {p['product_name'][:25]:<25} | {p['total_units_sold']:>10,} | ${p['total_revenue']:>12,.2f} | ${p['total_gross_profit']:>14,.2f}")
    print("=" * 80)


def handle_daily_report(service):
    """Generates a daily sales report."""
    print("\n--- [Daily Sales Report] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    target = input(f"Enter target date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not target:
        target = today_str

    try:
        rep = service.generate_daily_sales_report(target)
        print("\n" + "=" * 58)
        print(f"              DAILY SALES REPORT: {rep['report_date']}")
        print("=" * 58)
        print(f" Total Transactions:        {rep['transaction_count']:>14}")
        print(f" Total Units Sold:          {rep['units_sold']:>14,}")
        print(f" Total Daily Revenue:      ${rep['total_revenue']:>14,.2f}")
        print(f" Total Daily COGS:         ${rep['total_cogs']:>14,.2f}")
        print("-" * 58)
        print(f" Daily Gross Profit:       ${rep['gross_profit']:>14,.2f} ({rep['gross_margin_pct']:.1f}% margin)")
        print("=" * 58)

        if rep["sales_transactions"]:
            print("\nItemized Sales:")
            print(f"{'Sale ID':<8} | {'Product':<20} | {'Qty':<5} | {'Revenue ($)':<12} | {'Profit ($)'}")
            print("-" * 65)
            for s in rep["sales_transactions"]:
                print(f"#{s['sale_id']:<7} | {s['product_name'][:20]:<20} | {s['quantity']:<5} | ${s['total_revenue']:>10,.2f} | ${s['gross_profit']:>10,.2f}")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_monthly_report(service):
    """Generates monthly financial P&L statement."""
    print("\n--- [Monthly Financial Report (P&L)] ---")
    current_month = datetime.today().strftime("%Y-%m")
    month_input = input(f"Enter target month (YYYY-MM) [default: {current_month}]: ").strip()
    if not month_input:
        month_input = current_month

    try:
        pnl = service.generate_monthly_financial_report(month_input)
        print("\n" + "=" * 60)
        print(f"         PROFIT & LOSS FINANCIAL STATEMENT: {pnl['month']}")
        print("=" * 60)
        print(f" REVENUE:")
        print(f"   Gross Sales Revenue:            ${pnl['revenue']:>14,.2f}")
        print(f"   Cost of Goods Sold (COGS):      ${pnl['cogs']:>14,.2f}")
        print("-" * 60)
        print(f" GROSS PROFIT:                     ${pnl['gross_profit']:>14,.2f} ({pnl['gross_margin_pct']:.1f}%)")
        print("-" * 60)
        print(f" OPERATIONAL EXPENSES (OPEX):")
        if pnl["operational_breakdown"]:
            for cat, amt in pnl["operational_breakdown"].items():
                print(f"   • {cat:<30}: ${amt:>11,.2f}")
        else:
            print("   (No operating expenses logged for this month)")
        print(f"   Total Operating Expenses:       ${pnl['operational_expenses_total']:>14,.2f}")
        print("=" * 60)
        net_status = "SURPLUS" if pnl['net_profit'] >= 0 else "DEFICIT"
        print(f" NET PROFIT:                       ${pnl['net_profit']:>14,.2f} [{net_status}]")
        print(f" Net Profit Margin:                 {pnl['net_margin_pct']:>13.1f}%")
        print(f" Total Expenses (COGS + OPEX):     ${pnl['total_expenses']:>14,.2f}")
        print("=" * 60)
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_view_products(service):
    """Lists products and allows pricing updates."""
    products = service.list_products()
    print("\n" + "=" * 80)
    print(f"{'ID':<4} | {'Product Name':<25} | {'Category':<22} | {'Cost ($)':<10} | {'Selling ($)'}")
    print("-" * 80)
    for p in products:
        print(f"{p['product_id']:<4} | {p['product_name'][:25]:<25} | {p['category'][:22]:<22} | ${p['cost_price']:>8,.2f} | ${p['selling_price']:>9,.2f}")
    print("=" * 80)

    edit = input("\nUpdate pricing for a product? (y/n) [default: n]: ").strip().lower()
    if edit == "y":
        pid = input("Enter Product ID to update: ").strip()
        if not pid.isdigit():
            print("[Error] Numeric ID required.")
            return
        nc = input("Enter new cost price ($) [Enter to skip]: ").strip().lstrip("$£€")
        ns = input("Enter new selling price ($) [Enter to skip]: ").strip().lstrip("$£€")
        try:
            upd = service.update_product_pricing(int(pid), nc if nc else None, ns if ns else None)
            print(f"✓ Pricing updated for '{upd['product_name']}': Cost=${upd['cost_price']:.2f}, Selling=${upd['selling_price']:.2f}")
        except ValueError as err:
            print(f"[Error] {err}")


def handle_view_sales(service):
    """Displays recent sales."""
    sales = service.list_recent_sales(limit=25)
    print("\n" + "=" * 85)
    print(f"{'Sale ID':<8} | {'Date':<11} | {'Product Name':<22} | {'Qty':<5} | {'Revenue ($)':<12} | {'Gross Profit ($)'}")
    print("-" * 85)
    for s in sales:
        print(f"#{s['sale_id']:<7} | {s['sale_date']:<11} | {s['product_name'][:22]:<22} | {s['quantity']:<5} | ${s['total_revenue']:>10,.2f} | ${s['gross_profit']:>14,.2f}")
    print("=" * 85)


def handle_view_expenses(service):
    """Displays operating expenses."""
    expenses = service.list_operational_expenses(limit=25)
    print("\n" + "=" * 80)
    print(f"{'ID':<5} | {'Date':<11} | {'Category':<25} | {'Amount ($)':<12} | {'Description'}")
    print("-" * 80)
    for e in expenses:
        print(f"#{e['expense_id']:<4} | {e['expense_date']:<11} | {e['category'][:25]:<25} | ${e['amount']:>10,.2f} | {e['description']}")
    print("=" * 80)


def main():
    """Main CLI application loop."""
    print("\nInitializing Small Business Sales & Profit Database...")
    initialize_database(DEFAULT_DB_FILE)
    service = ProfitAnalyticsService(DEFAULT_DB_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-11): ").strip()

            if choice == "1":
                handle_register_product(service)
            elif choice == "2":
                handle_record_sale(service)
            elif choice == "3":
                handle_record_expense(service)
            elif choice == "4":
                handle_financial_summary(service)
            elif choice == "5":
                handle_bestsellers(service)
            elif choice == "6":
                handle_daily_report(service)
            elif choice == "7":
                handle_monthly_report(service)
            elif choice == "8":
                handle_view_products(service)
            elif choice == "9":
                handle_view_sales(service)
            elif choice == "10":
                handle_view_expenses(service)
            elif choice == "11":
                print("\nThank you for managing your business profitability. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 11.")

        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
