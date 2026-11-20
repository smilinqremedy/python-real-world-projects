"""
Command-Line Interface for Nigerian Tax and Business Revenue Calculator.
"""
import sys
import os
from datetime import datetime
from finance_service import NigerianFinanceService, STATUTORY_DISCLAIMER


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75)


def seed_demo_data(service: NigerianFinanceService):
    """Seed sample Nigerian small business financial dataset."""
    try:
        service.register_business(
            business_name="Kano Agro-Allied & Distribution Ltd",
            rc_number="RC-1849204",
            tin="TIN-23849102-0001",
            business_type="Limited Liability Company (LLC)",
            sector="Agribusiness & FMCG Logistics",
            contact_email="finance@kanoagro.ng",
            contact_phone="+2348023456789",
            address="Plot 12 Commercial Layout, Bompai, Kano, Nigeria",
            currency="NGN",
            currency_symbol="₦"
        )

        today = datetime.now()
        cur_year = today.year
        cur_month = today.strftime("%m")

        # Record sample sales
        service.record_sale(f"{cur_year}-{cur_month}-02", "Wholesale", "50 Bags Premium Soybeans Wholesale", 4250000.0, "Danladi Grains Trading", False, "Bank Transfer")
        service.record_sale(f"{cur_year}-{cur_month}-05", "Product Sales", "Packaged Milled Rice Retail Crates", 1850000.0, "Metro Supermarkets Ltd", True, "Bank Transfer")
        service.record_sale(f"{cur_year}-{cur_month}-10", "Services Rendered", "Interstate Haulage & Reefer Truck Delivery", 950000.0, "Arewa Agro Processing", False, "Bank Transfer")
        service.record_sale(f"{cur_year}-{cur_month}-15", "Consulting", "Farm Yield Quality Assessment & Soil Test", 450000.0, "Jigawa Cooperative Union", False, "Online Payment")
        service.record_sale(f"{cur_year}-{cur_month}-18", "Product Sales", "Bulk Sesame Seed Delivery", 3100000.0, "Export Partners Global", False, "Bank Transfer")

        # Record sample expenses
        service.record_expense(f"{cur_year}-{cur_month}-03", "Cost of Goods Sold (COGS)", "COGS", "Direct farm procurement of soybeans", 2800000.0, "Hadejia Farmers Cooperative", True)
        service.record_expense(f"{cur_year}-{cur_month}-04", "Cost of Goods Sold (COGS)", "COGS", "Packaging sacks and grain bag branding", 180000.0, "Kano Packaging Mills", True)
        service.record_expense(f"{cur_year}-{cur_month}-08", "Rent & Office Space", "Operating", "Warehouse storage space monthly lease", 350000.0, "Northline Real Estate", True)
        service.record_expense(f"{cur_year}-{cur_month}-12", "Salaries & Wages", "Operating", "Monthly operational and warehouse staff payroll", 750000.0, "Staff Direct Deposit", True)
        service.record_expense(f"{cur_year}-{cur_month}-14", "Utilities & Power", "Operating", "Industrial diesel generator fuel purchase", 320000.0, "TotalEnergies Filling Station", True)
        service.record_expense(f"{cur_year}-{cur_month}-16", "Repairs & Maintenance", "Operating", "Truck brake servicing and tyre replacement", 140000.0, "Bompai Heavy Duty Mechanics", True)
        service.record_expense(f"{cur_year}-{cur_month}-19", "Capital Equipment / Depreciation", "Capital", "Semi-automated grain moisture tester meter", 250000.0, "AgriTech Scientific Instruments", False)

    except Exception:
        pass


def handle_record_sale(service: NigerianFinanceService):
    print_banner("Record Daily Sales Revenue")
    try:
        date_str = input("Sale Date (YYYY-MM-DD) [Leave blank for today]: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        print("\nSelect Category:")
        print("  1. Product Sales")
        print("  2. Services Rendered")
        print("  3. Wholesale")
        print("  4. Consulting")
        print("  5. Commission")
        print("  6. Other Revenue")
        cat_choice = input("Choice (1-6): ").strip()
        cat_map = {
            "1": "Product Sales", "2": "Services Rendered", "3": "Wholesale",
            "4": "Consulting", "5": "Commission", "6": "Other Revenue"
        }
        category = cat_map.get(cat_choice, "Product Sales")

        desc = input("Transaction Description: ").strip()
        customer = input("Customer Name (optional): ").strip() or None
        gross_amount = float(input("Gross Sales Amount (NGN / ₦): ").strip())

        vat_input = input("Was 7.5% VAT charged / collected on this sale? (y/n) [n]: ").strip().lower()
        vat_applied = vat_input == "y"

        print("\nPayment Method: 1. Bank Transfer  2. POS  3. Cash  4. Online Payment")
        pay_choice = input("Choice (1-4) [1]: ").strip()
        pay_map = {"1": "Bank Transfer", "2": "POS", "3": "Cash", "4": "Online Payment"}
        payment_method = pay_map.get(pay_choice, "Bank Transfer")

        ref = service.record_sale(date_str, category, desc, gross_amount, customer, vat_applied, payment_method)
        print(f"\n[SUCCESS] Sales transaction saved! Reference ID: {ref}")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_record_expense(service: NigerianFinanceService):
    print_banner("Record Business Expense")
    try:
        date_str = input("Expense Date (YYYY-MM-DD) [Leave blank for today]: ").strip()
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        print("\nSelect Expense Classification:")
        print("  1. COGS (Cost of Goods Sold - inventory, raw materials, direct packaging)")
        print("  2. Operating (OpEx - rent, payroll, utilities, marketing, maintenance)")
        print("  3. Capital (Equipment, vehicles, long-term capital assets)")
        type_choice = input("Choice (1-3) [2]: ").strip()
        type_map = {"1": "COGS", "2": "Operating", "3": "Capital"}
        expense_type = type_map.get(type_choice, "Operating")

        category = input("Expense Category (e.g. Salaries, Rent, Fuel, Inventory): ").strip()
        desc = input("Description: ").strip()
        vendor = input("Vendor / Payee Name (optional): ").strip() or None
        amount = float(input("Amount in Naira (₦): ").strip())

        deduct_input = input("Is this expense wholly, exclusively, and necessarily incurred for business (tax-deductible)? (y/n) [y]: ").strip().lower()
        is_deductible = deduct_input != "n"
        receipt_ref = input("Receipt / Invoice Number (optional): ").strip() or None

        ref = service.record_expense(date_str, category, expense_type, desc, amount, vendor, is_deductible, receipt_ref)
        print(f"\n[SUCCESS] Expense record saved! Reference ID: {ref}")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def show_pnl_dashboard(service: NigerianFinanceService):
    print_banner("Financial Performance & Profitability Dashboard")
    start = input("Start Date (YYYY-MM-DD) [Enter for all time]: ").strip() or None
    end = input("End Date (YYYY-MM-DD) [Enter for all time]: ").strip() or None

    pnl = service.calculate_profit_and_loss(start, end)
    b = service.get_business_info()
    sym = b.get("currency_symbol", "₦")

    print(f"\nEntity: {b['business_name']} ({b['rc_number']})")
    print(f"Period: {pnl['period_start']} to {pnl['period_end']}")
    print("-" * 65)
    print(f"  Gross Revenue / Turnover : {sym}{pnl['total_revenue']:>16,.2f}")
    print(f"  Cost of Goods Sold (COGS): {sym}{pnl['cogs']:>16,.2f}")
    print("  " + "-" * 45)
    print(f"  GROSS PROFIT             : {sym}{pnl['gross_profit']:>16,.2f}  (Margin: {pnl['gross_margin_percent']}%)")
    print(f"  Operating Expenses (OpEx): {sym}{pnl['operating_expenses']:>16,.2f}")
    print("  " + "-" * 45)
    print(f"  NET PROFIT (Before Tax)  : {sym}{pnl['net_profit']:>16,.2f}  (Margin: {pnl['net_margin_percent']}%)")
    print("-" * 65)
    print(f"  Capital Expenditures     : {sym}{pnl['capital_expenses']:>16,.2f}")
    print(f"  Output VAT Collected     : {sym}{pnl['vat_collected']:>16,.2f}")
    print("-" * 65)


def show_tax_estimation(service: NigerianFinanceService):
    print_banner("Nigerian Business Tax Obligation Estimation")
    start = input("Start Date (YYYY-MM-DD) [Enter for all time]: ").strip() or None
    end = input("End Date (YYYY-MM-DD) [Enter for all time]: ").strip() or None

    tax = service.estimate_tax_obligations(start, end)
    b = service.get_business_info()
    sym = b.get("currency_symbol", "₦")

    print(f"\nTax Review for: {b['business_name']} (TIN: {b['tin']})")
    print(f"Company Classification : {tax['company_tier']}")
    print(f"Gross Turnover         : {sym}{tax['turnover']:,.2f}")
    print(f"Assessable Net Profit  : {sym}{tax['assessable_profit']:,.2f}")
    print("-" * 70)
    print(f"  Companies Income Tax (CIT @ {tax['cit_rate_applied']*100:.0f}%)   : {sym}{tax['estimated_cit']:>14,.2f}")
    print(f"  Tertiary Education Tax (EDT @ 3%)        : {sym}{tax['estimated_edt']:>14,.2f}")
    if tax["estimated_minimum_tax"] > 0:
        print(f"  Minimum Tax Assessment                   : {sym}{tax['estimated_minimum_tax']:>14,.2f}")
    print(f"  VAT Collected (Qualifying Supplies)      : {sym}{tax['estimated_vat_collected']:>14,.2f}")
    print("  " + "-" * 50)
    print(f"  TOTAL ESTIMATED TAX OBLIGATION           : {sym}{tax['estimated_total_tax']:>14,.2f}")
    print("-" * 70)

    print("\n[KEY TAX ASSUMPTIONS]")
    for idx, asm in enumerate(tax["assumptions"], 1):
        print(f"  {idx}. {asm}")

    print("\n" + "*" * 75)
    print(f"  {tax['disclaimer']}")
    print("*" * 75)


def handle_monthly_summary(service: NigerianFinanceService):
    print_banner("Monthly Financial Summaries")
    summaries = service.generate_monthly_financial_summary()
    if not summaries:
        print("No monthly transactions recorded yet.")
        return

    b = service.get_business_info()
    sym = b.get("currency_symbol", "₦")

    print(f"{'Month':<10} {'Revenue (' + sym + ')':<18} {'COGS (' + sym + ')':<16} {'Gross Profit':<16} {'OpEx (' + sym + ')':<16} {'Net Profit (' + sym + ')'}")
    print("-" * 92)
    for s in summaries:
        print(f"{s['month']:<10} {s['revenue']:>15,.2f}  {s['cogs']:>13,.2f}  {s['gross_profit']:>13,.2f}  {s['operating_expenses']:>13,.2f}  {s['net_profit']:>15,.2f}")
    print("-" * 92)


def handle_configure_tax(service: NigerianFinanceService):
    print_banner("Configure Nigerian Tax Parameters")
    rules = service.get_tax_rules()
    print("Current Configuration:")
    print(f"  1. Small Business Turnover Threshold : ₦{rules['small_turnover_threshold']:,.2f}")
    print(f"  2. Medium Business Turnover Threshold: ₦{rules['medium_turnover_threshold']:,.2f}")
    print(f"  3. Small Business CIT Rate           : {rules['small_cit_rate']*100:.1f}%")
    print(f"  4. Medium Business CIT Rate          : {rules['medium_cit_rate']*100:.1f}%")
    print(f"  5. Large Business CIT Rate           : {rules['large_cit_rate']*100:.1f}%")
    print(f"  6. Tertiary Education Tax (EDT) Rate : {rules['education_tax_rate']*100:.1f}%")
    print(f"  7. Standard VAT Rate                 : {rules['vat_rate']*100:.1f}%")
    print(f"  8. Minimum Tax Rate                  : {rules['minimum_tax_rate']*100:.2f}%")

    change = input("\nDo you wish to modify these parameters? (y/n) [n]: ").strip().lower()
    if change == "y":
        try:
            st = float(input(f"New Small Turnover Threshold [{rules['small_turnover_threshold']}]: ") or rules['small_turnover_threshold'])
            mt = float(input(f"New Medium Turnover Threshold [{rules['medium_turnover_threshold']}]: ") or rules['medium_turnover_threshold'])
            sc = float(input(f"New Small CIT Rate (0.0 to 1.0) [{rules['small_cit_rate']}]: ") or rules['small_cit_rate'])
            mc = float(input(f"New Medium CIT Rate (0.0 to 1.0) [{rules['medium_cit_rate']}]: ") or rules['medium_cit_rate'])
            lc = float(input(f"New Large CIT Rate (0.0 to 1.0) [{rules['large_cit_rate']}]: ") or rules['large_cit_rate'])
            ed = float(input(f"New Education Tax Rate [{rules['education_tax_rate']}]: ") or rules['education_tax_rate'])
            vat = float(input(f"New VAT Rate [{rules['vat_rate']}]: ") or rules['vat_rate'])
            mint = float(input(f"New Minimum Tax Rate [{rules['minimum_tax_rate']}]: ") or rules['minimum_tax_rate'])

            service.update_tax_rules(st, mt, sc, mc, lc, ed, vat, mint)
            print("\n[SUCCESS] Tax rules updated successfully!")
        except ValueError as e:
            print(f"\n[ERROR] {e}")


def handle_export_reports(service: NigerianFinanceService, format_type: str):
    print_banner(f"Export Financial & Tax Statement ({format_type.upper()})")
    default_dir = os.path.join(os.path.dirname(__file__), "exports")
    os.makedirs(default_dir, exist_ok=True)

    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    if format_type == "csv":
        default_file = os.path.join(default_dir, f"financial_statement_{today_str}.csv")
        out_path = input(f"Output File Path [{default_file}]: ").strip() or default_file
        saved = service.export_financials_to_csv(out_path)
        print(f"\n[SUCCESS] CSV report exported successfully to:\n  {saved}")
    elif format_type == "pdf":
        default_file = os.path.join(default_dir, f"financial_tax_report_{today_str}.pdf")
        out_path = input(f"Output File Path [{default_file}]: ").strip() or default_file
        saved = service.export_financials_to_pdf(out_path)
        print(f"\n[SUCCESS] PDF report generated successfully to:\n  {saved}")


def main():
    service = NigerianFinanceService()
    seed_demo_data(service)

    while True:
        b = service.get_business_info()
        print_banner(f"Nigerian Business Revenue & Tax Calculator - {b['business_name']}")
        print("1. Record Daily Sales Revenue")
        print("2. Record Business Expense")
        print("3. View Financial Performance & Profit Dashboard (Gross vs Net)")
        print("4. View Monthly Financial Summaries")
        print("5. Generate Tax Obligation Estimation & Review Assumptions")
        print("6. Configure Tax Rates and Thresholds")
        print("7. Export Financial Statement to CSV")
        print("8. Export Financial & Tax Report to PDF")
        print("9. Register / Update Business Profile")
        print("10. Exit")

        choice = input("\nSelect an option (1-10): ").strip()
        if choice == "1":
            handle_record_sale(service)
        elif choice == "2":
            handle_record_expense(service)
        elif choice == "3":
            show_pnl_dashboard(service)
        elif choice == "4":
            handle_monthly_summary(service)
        elif choice == "5":
            show_tax_estimation(service)
        elif choice == "6":
            handle_configure_tax(service)
        elif choice == "7":
            handle_export_reports(service, "csv")
        elif choice == "8":
            handle_export_reports(service, "pdf")
        elif choice == "9":
            print_banner("Business Profile")
            name = input(f"Business Name [{b['business_name']}]: ").strip() or b['business_name']
            rc = input(f"RC/BN Number [{b['rc_number']}]: ").strip() or b['rc_number']
            tin = input(f"Tax ID (TIN) [{b['tin']}]: ").strip() or b['tin']
            btype = input(f"Business Type [{b['business_type']}]: ").strip() or b['business_type']
            sec = input(f"Sector [{b['sector']}]: ").strip() or b['sector']
            email = input(f"Email [{b['contact_email']}]: ").strip() or b['contact_email']
            phone = input(f"Phone [{b['contact_phone']}]: ").strip() or b['contact_phone']
            service.register_business(name, rc, tin, btype, sec, email, phone)
            print("\n[SUCCESS] Business profile updated.")
        elif choice == "10":
            print("Exiting application. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
