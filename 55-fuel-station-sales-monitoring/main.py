"""
Interactive CLI for Fuel Station Sales & Tank Monitoring System.
"""
import sys
from decimal import Decimal
from datetime import datetime
from fuel_service import FuelStationService, to_decimal


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: FuelStationService):
    try:
        service.register_product("PMS", "Premium Motor Spirit (Petrol)", "650.00")
        service.register_product("AGO", "Automotive Gas Oil (Diesel)", "1150.00")
        service.register_product("DPK", "Dual Purpose Kerosene", "950.00")

        service.register_tank("TK-PMS-01", "PMS", capacity_litres=45000, initial_volume=12500)
        service.register_tank("TK-AGO-01", "AGO", capacity_litres=33000, initial_volume=8000)

        today = datetime.now().strftime("%Y-%m-%d")
        service.record_delivery("TK-PMS-01", "NNPC Retail Supply", 20000.0, "590.00", today, "WB-NNPC-9912")

        # Record pump sales
        service.record_pump_sale("TK-PMS-01", "PUMP-1", 10450.0, 14200.0, today)
        service.record_pump_sale("TK-PMS-01", "PUMP-2", 8200.0, 11450.0, today)
    except Exception:
        pass


def handle_record_sale(service: FuelStationService):
    print_banner("Record Pump Sales (Meter Readings)")
    tanks = service.list_tanks()
    print("Select Tank / Product:")
    for t in tanks:
        print(f"  [{t['tank_code']}] {t['product_name']} (₦{t['unit_price']}/L) - Stock: {t['current_volume_litres']}L")

    try:
        tcode = input("\nEnter Tank Code: ").strip()
        pump = input("Pump Identifier (e.g. PUMP-1): ").strip()
        m_start = input("Opening Meter Reading (L): ").strip()
        m_end = input("Closing Meter Reading (L): ").strip()
        sdate = input("Sale Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None

        s_ref = service.record_pump_sale(tcode, pump, m_start, m_end, sdate)
        litres = to_decimal(Decimal(m_end) - Decimal(m_start))
        print(f"\n[SUCCESS] Pump sale recorded! Sale Ref: {s_ref}")
        print(f"Litres Dispensed: {litres} L")
    except (ValueError, Exception) as e:
        print(f"\n[ERROR] {e}")


def handle_record_delivery(service: FuelStationService):
    print_banner("Record Fuel Delivery (Stock Replenishment)")
    try:
        tcode = input("Target Tank Code (e.g. TK-PMS-01): ").strip()
        supplier = input("Depot / Supplier Name: ").strip()
        qty = input("Quantity Delivered (Litres): ").strip()
        cost = input("Cost per Litre (₦): ").strip()
        waybill = input("Waybill / Discharge Ticket Number: ").strip() or None
        ddate = input("Delivery Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None

        d_ref = service.record_delivery(tcode, supplier, qty, cost, ddate, waybill)
        print(f"\n[SUCCESS] Delivery recorded and tank replenished! Ref: {d_ref}")
    except (ValueError, Exception) as e:
        print(f"\n[ERROR] {e}")


def handle_reconciliation(service: FuelStationService):
    print_banner("Tank Dip Reconciliation & Discrepancy Detection")
    try:
        tcode = input("Tank Code (e.g. TK-PMS-01): ").strip()
        rdate = input("Reconciliation Date (YYYY-MM-DD) [Enter for Today]: ").strip() or datetime.now().strftime("%Y-%m-%d")
        open_dip = input("Opening Physical Dip Reading (Litres): ").strip()
        close_dip = input("Closing Physical Dip Reading (Litres): ").strip()

        res = service.reconcile_tank(tcode, rdate, open_dip, close_dip)
        print("\n" + "=" * 65)
        print(f"  RECONCILIATION RESULT FOR {res['tank_code']} ({res['date']})")
        print("=" * 65)
        print(f"Opening Dip Volume    : {res['opening_dip']:>14,.2f} L")
        print(f"+ Deliveries Received : {res['deliveries']:>14,.2f} L")
        print(f"- Pump Sales Dispensed: {res['pump_sales']:>14,.2f} L")
        print("-" * 50)
        print(f"EXPECTED CLOSING STOCK: {res['expected_closing']:>14,.2f} L")
        print(f"ACTUAL PHYSICAL DIP   : {res['actual_closing']:>14,.2f} L")
        print("-" * 50)
        print(f"DISCREPANCY VARIANCE  : {res['discrepancy']:>14,.2f} L")
        print(f"STATUS CLASSIFICATION : {res['status'].upper()}")
        print(f"Total Sales Revenue   : ₦{res['total_revenue']:>13,.2f}")
        print("=" * 65)

    except (ValueError, Exception) as e:
        print(f"\n[ERROR] {e}")


def handle_view_tanks(service: FuelStationService):
    print_banner("Storage Tanks Current Status")
    tanks = service.list_tanks()
    print(f"{'Tank':<12} {'Product':<26} {'Price/L':<10} {'Current Vol':<14} {'Capacity':<14} {'Level %'}")
    print("-" * 88)
    for t in tanks:
        curr = Decimal(t["current_volume_litres"])
        cap = Decimal(t["capacity_litres"])
        pct = (curr / cap * Decimal("100")).quantize(Decimal("0.1"))
        print(f"{t['tank_code']:<12} {t['product_name'][:24]:<26} ₦{t['unit_price']:<9} {curr:>10,.1f} L  {cap:>10,.1f} L  {pct}%")


def handle_daily_report(service: FuelStationService):
    print_banner("Daily Fuel Station Sales & Reconciliation Report")
    rdate = input("Report Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None
    rep = service.generate_daily_report(rdate)

    print(f"\nDate: {rep['date']}")
    print(f"Total Fuel Dispensed : {rep['total_litres_sold']:,.2f} Litres")
    print(f"Total Sales Revenue  : ₦{rep['total_revenue']:,.2f}")

    if rep["product_breakdown"]:
        print("\n--- Sales by Product ---")
        for p in rep["product_breakdown"]:
            print(f"  * {p['product_name']}: {p['total_litres']:,.2f} L (₦{p['total_rev']:,.2f})")

    if rep["tank_reconciliations"]:
        print("\n--- Daily Tank Dip Audits ---")
        for r in rep["tank_reconciliations"]:
            print(f"  [{r['tank_code']}] Expected: {r['expected_closing_litres']}L | Actual: {r['actual_closing_dip_litres']}L | Discrepancy: {r['discrepancy_litres']}L ({r['discrepancy_status']})")


def main():
    service = FuelStationService()
    seed_demo_data(service)

    while True:
        print_banner("Fuel Station Sales & Tank Monitoring System")
        print("1. Record Daily Pump Sales (Meter Readings)")
        print("2. Record Fuel Delivery (Stock Replenishment)")
        print("3. Perform Tank Dip Reconciliation & Discrepancy Check")
        print("4. View Tank Levels & Inventory")
        print("5. Generate Daily Sales & Audit Report")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ").strip()
        if choice == "1":
            handle_record_sale(service)
        elif choice == "2":
            handle_record_delivery(service)
        elif choice == "3":
            handle_reconciliation(service)
        elif choice == "4":
            handle_view_tanks(service)
        elif choice == "5":
            handle_daily_report(service)
        elif choice == "6":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
