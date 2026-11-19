"""
Electricity and Household Power Consumption Tracker - CLI Interface
Entry point for managing household energy budgets, prepaid credits, and generator expenses.
"""

import sys
from datetime import datetime
from database import initialize_database, DEFAULT_DB_FILE
from tracker_service import PowerTrackerService


def display_menu(remaining_status=None):
    """
    Displays the interactive main menu with status alert banner if units are low.
    """
    print("\n" + "=" * 58)
    print("   ELECTRICITY & POWER CONSUMPTION TRACKER (CLI)   ")
    print("=" * 58)

    if remaining_status and remaining_status["is_low"]:
        print(" [!] LOW UNITS WARNING: Only "
              f"{remaining_status['remaining_units_kwh']:.1f} kWh remaining! "
              f"(Est. {remaining_status['estimated_days_remaining']} days left)")
        print("-" * 58)

    print(" 1. Record Prepaid Electricity Purchase")
    print(" 2. Record Daily Electricity Consumption")
    print(" 3. View Remaining Units & Balance Status")
    print(" 4. View Average Daily Consumption")
    print(" 5. Estimate Monthly Energy Expenses")
    print(" 6. Record Generator Fuel Purchase")
    print(" 7. View Generator Fuel Expenses Summary")
    print(" 8. View Recent Daily Consumption History")
    print(" 9. Generate Monthly Energy Report")
    print(" 10. Configure Low-Units Alert Threshold")
    print(" 11. Exit Application")
    print("=" * 58)


def handle_record_purchase(service):
    """Records a prepaid electricity purchase."""
    print("\n--- [Record Prepaid Electricity Purchase] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter purchase date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    amount_str = input("Enter amount paid ($): ").strip().lstrip("$£€")
    units_str = input("Enter electricity units credited (kWh): ").strip()
    token = input("Enter recharge token number (optional): ").strip()

    purchase = service.record_prepaid_purchase(
        purchase_date=date_str,
        amount_paid=amount_str,
        units_credited=units_str,
        token_number=token if token else None
    )

    print("\n✓ Electricity recharge recorded successfully!")
    print(f"  Units Credited: {purchase['units_credited']:.2f} kWh")
    print(f"  Amount Paid:    ${purchase['amount_paid']:.2f}")
    print(f"  Effective Rate: ${purchase['unit_rate']:.4f} per kWh")


def handle_record_consumption(service):
    """Records daily electricity consumption."""
    print("\n--- [Record Daily Electricity Consumption] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter consumption date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    print("Input method:")
    print("  1. Enter direct units consumed (kWh)")
    print("  2. Enter cumulative meter reading")
    choice = input("Select option (1/2) [default: 1]: ").strip()

    units_val = None
    meter_val = None

    if choice == "2":
        meter_val = input("Enter current meter reading (kWh): ").strip()
    else:
        units_val = input("Enter electricity units consumed today (kWh): ").strip()

    notes = input("Enter notes / major appliances used (optional): ").strip()

    result = service.record_daily_consumption(
        log_date=date_str,
        units_consumed=units_val if units_val else None,
        meter_reading=meter_val if meter_val else None,
        notes=notes if notes else None
    )

    print(f"\n✓ Successfully logged {result['units_consumed']:.2f} kWh consumed on {result['log_date']}.")

    # Immediate status check
    status = service.get_remaining_units_status()
    if status["is_low"]:
        print(f"\n[ALERT] Remaining balance is LOW: {status['remaining_units_kwh']:.1f} kWh left "
              f"(Threshold: {status['threshold_kwh']:.1f} kWh)!")


def handle_view_remaining_units(service):
    """Displays current remaining prepaid units and status."""
    status = service.get_remaining_units_status()
    rate = service.get_effective_electricity_rate()

    print("\n" + "=" * 50)
    print("          PREPAID ELECTRICITY BALANCE")
    print("=" * 50)
    print(f" Total Units Purchased:    {status['total_purchased_kwh']:>12,.2f} kWh")
    print(f" Total Units Consumed:     {status['total_consumed_kwh']:>12,.2f} kWh")
    print("-" * 50)
    print(f" Remaining Units Balance:  {status['remaining_units_kwh']:>12,.2f} kWh")
    rem_value = status['remaining_units_kwh'] * rate
    print(f" Equivalent Dollar Value:  ${rem_value:>11,.2f}")
    print(f" Low-Units Alert Level:    {status['threshold_kwh']:>12,.1f} kWh")
    print("-" * 50)

    if status["is_low"]:
        print(f" STATUS: [!] LOW UNITS ALERT (< {status['threshold_kwh']:.1f} kWh)")
        print(f" Estimated Days Remaining: ~{status['estimated_days_remaining']:.1f} days")
    else:
        print(" STATUS: [OK] Balance is Healthy")
        print(f" Estimated Days Remaining: ~{status['estimated_days_remaining']:.1f} days")
    print("=" * 50)


def handle_view_average_consumption(service):
    """Displays average daily consumption metrics."""
    avg_data = service.get_average_daily_consumption(days=30)
    rate = service.get_effective_electricity_rate()

    print("\n" + "=" * 50)
    print("         DAILY CONSUMPTION BENCHMARKS")
    print("=" * 50)
    print(f" Tracked Days Analyzed:      {avg_data['tracked_days']:>12}")
    print(f" Total Consumption (Tracked):{avg_data['total_kwh']:>12,.2f} kWh")
    print("-" * 50)
    print(f" Average Daily Consumption:  {avg_data['average_daily_kwh']:>12,.2f} kWh/day")
    daily_cost = avg_data['average_daily_kwh'] * rate
    print(f" Average Daily Cost:         ${daily_cost:>11,.2f}/day")
    print(f" Current Electricity Tariff: ${rate:>11,.4f}/kWh")
    print("=" * 50)


def handle_estimate_monthly_expenses(service):
    """Displays estimated monthly energy expenses."""
    est = service.estimate_monthly_electricity_expenses()

    print("\n" + "=" * 54)
    print("          MONTHLY ENERGY EXPENSES PROJECTION")
    print("=" * 54)
    print(f" Average Daily Consumption:   {est['average_daily_kwh']:>14,.2f} kWh/day")
    print(f" Projected 30-Day Usage:       {est['projected_monthly_kwh']:>14,.2f} kWh")
    print(f" Effective Grid Tariff:       ${est['tariff_rate_per_kwh']:>13,.4f} /kWh")
    print("-" * 54)
    print(f" Projected Grid Electricity:  ${est['estimated_grid_cost']:>14,.2f}")
    print(f" Projected Generator Fuel:    ${est['estimated_generator_cost']:>14,.2f}")
    print("=" * 54)
    print(f" TOTAL ESTIMATED MONTHLY BILL: ${est['total_estimated_monthly_expense']:>13,.2f}")
    print("=" * 54)


def handle_record_generator_fuel(service):
    """Records a generator fuel purchase."""
    print("\n--- [Record Generator Fuel Purchase] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter purchase date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    fuel_type = input("Enter fuel type (Petrol/Diesel) [default: Petrol]: ").strip()
    if not fuel_type:
        fuel_type = "Petrol"

    liters_str = input("Enter quantity of fuel purchased (Liters): ").strip()
    rate_str = input("Enter cost per liter ($): ").strip().lstrip("$£€")
    hours_str = input("Enter engine run hours since last refueling (optional): ").strip()
    notes = input("Enter notes (optional): ").strip()

    expense = service.record_generator_fuel(
        expense_date=date_str,
        liters_bought=liters_str,
        cost_per_liter=rate_str,
        fuel_type=fuel_type,
        run_hours=hours_str if hours_str else None,
        notes=notes if notes else None
    )

    print("\n✓ Generator fuel purchase recorded successfully!")
    print(f"  Fuel: {expense['liters_bought']:.2f}L of {expense['fuel_type']}")
    print(f"  Cost: ${expense['cost_per_liter']:.2f}/L (Total: ${expense['total_cost']:.2f})")


def handle_view_generator_summary(service):
    """Displays separate generator fuel tracking summary."""
    summary = service.get_generator_summary()

    print("\n" + "=" * 52)
    print("           GENERATOR EXPENSES SUMMARY")
    print("=" * 52)
    print(f" Total Refueling Entries:      {summary['total_entries']:>14}")
    print(f" Total Fuel Purchased:         {summary['total_liters']:>14,.2f} Liters")
    print(f" Total Generator Fuel Spend:   ${summary['total_spend']:>13,.2f}")
    print(f" Average Fuel Cost per Liter:  ${summary['average_cost_per_liter']:>13,.2f}/L")
    print("-" * 52)
    if summary["total_run_hours"] > 0:
        print(f" Total Recorded Run Hours:     {summary['total_run_hours']:>14,.1f} hrs")
        print(f" Fuel Consumption Burn Rate:   {summary['liters_per_hour']:>14,.2f} L/hr")
    print("=" * 52)


def handle_list_consumption(service):
    """Displays table of recent daily consumption logs."""
    logs = service.list_consumption_logs(limit=20)
    print("\n" + "=" * 65)
    print(f"{'Date':<12} | {'Consumed (kWh)':<16} | {'Meter Reading':<14} | {'Notes'}")
    print("-" * 65)
    if not logs:
        print("  No consumption logs recorded yet.")
    else:
        for log in logs:
            meter_str = f"{log['meter_reading']:.1f}" if log['meter_reading'] is not None else "-"
            notes_str = log['notes'] or "-"
            print(f"{log['log_date']:<12} | {log['units_consumed']:>12,.2f} kWh  | {meter_str:>14} | {notes_str}")
    print("=" * 65)


def handle_monthly_report(service):
    """Generates monthly energy report."""
    print("\n--- [Monthly Consolidated Energy Report] ---")
    current_month = datetime.today().strftime("%Y-%m")
    month_input = input(f"Enter target month (YYYY-MM) [default: {current_month}]: ").strip()
    if not month_input:
        month_input = current_month

    rep = service.generate_monthly_energy_report(month_input)

    print("\n" + "=" * 58)
    print(f"           ENERGY CONSUMPTION REPORT: {rep['month']}")
    print("=" * 58)
    print(" GRID ELECTRICITY:")
    print(f"   Units Purchased:           {rep['units_bought_kwh']:>12,.2f} kWh")
    print(f"   Units Consumed:            {rep['units_consumed_kwh']:>12,.2f} kWh")
    print(f"   Days Tracked:              {rep['days_logged']:>12} days")
    print(f"   Daily Average Usage:       {rep['avg_daily_kwh']:>12,.2f} kWh/day")
    print(f"   Total Grid Spend:          ${rep['grid_spend']:>11,.2f}")
    print("-" * 58)
    print(" GENERATOR EXPENSES (BACKUP POWER):")
    print(f"   Fuel Purchased:            {rep['liters_bought']:>12,.2f} Liters")
    if rep['generator_run_hours'] > 0:
        print(f"   Run Hours:                 {rep['generator_run_hours']:>12,.1f} hrs")
    print(f"   Total Generator Spend:     ${rep['generator_spend']:>11,.2f}")
    print("=" * 58)
    print(f" TOTAL COMBINED ENERGY COST:   ${rep['total_energy_expense']:>11,.2f}")
    print(f"   Grid Power Cost Share:      {rep['grid_share_pct']:>11.1f}%")
    print(f"   Generator Cost Share:       {rep['generator_share_pct']:>11.1f}%")
    print("=" * 58)


def handle_configure_threshold(service):
    """Configures the low-units alert threshold."""
    current = service.get_low_units_threshold()
    print(f"\nCurrent low-units alert threshold: {current:.1f} kWh")
    new_val = input("Enter new low-units alert threshold (kWh): ").strip()
    try:
        val_float = float(new_val)
        if val_float <= 0:
            print("[Error] Threshold must be positive.")
            return
        service.set_setting("low_units_threshold", str(val_float))
        print(f"✓ Low-units alert threshold updated to {val_float:.1f} kWh.")
    except ValueError:
        print("[Error] Invalid numeric value.")


def main():
    """Main CLI execution loop."""
    print("\nInitializing Electricity & Power Tracker Database...")
    initialize_database(DEFAULT_DB_FILE)
    service = PowerTrackerService(DEFAULT_DB_FILE)

    while True:
        try:
            status = service.get_remaining_units_status()
            display_menu(status)
            choice = input("Enter your choice (1-11): ").strip()

            if choice == "1":
                handle_record_purchase(service)
            elif choice == "2":
                handle_record_consumption(service)
            elif choice == "3":
                handle_view_remaining_units(service)
            elif choice == "4":
                handle_view_average_consumption(service)
            elif choice == "5":
                handle_estimate_monthly_expenses(service)
            elif choice == "6":
                handle_record_generator_fuel(service)
            elif choice == "7":
                handle_view_generator_summary(service)
            elif choice == "8":
                handle_list_consumption(service)
            elif choice == "9":
                handle_monthly_report(service)
            elif choice == "10":
                handle_configure_threshold(service)
            elif choice == "11":
                print("\nThank you for tracking your energy consumption efficiently. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 11.")

        except ValueError as err:
            print(f"\n[Validation Error] {err}")
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
