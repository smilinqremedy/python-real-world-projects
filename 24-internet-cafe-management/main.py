#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Internet Cafe Management System.
"""

import sys
from cafe_service import CafeService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_session_ticket(s: dict):
    print("\n" + "-" * 55)
    print(f"  INTERNET CAFE SESSION #{s['session_id']}")
    print(f"  Customer:     {s['customer_name']}")
    print(f"  Terminal:     {s['computer_code']} ({s['ip_address']})")
    print(f"  Rate:         ${s['hourly_rate_applied']:.2f} / hr")
    print("-" * 55)
    print(f"  Start Time:   {s['start_time']}")
    if s.get("end_time"):
        print(f"  End Time:     {s['end_time']}")
        print(f"  Duration:     {s['duration_minutes']} min(s)")
        print(f"  TOTAL BILL:   ${s['total_bill']:>7.2f}")
        print(f"  Payment:      {s['payment_status']} (Paid: ${s['amount_paid']:.2f})")
        if "change_returned" in s:
            print(f"  Change:       ${s['change_returned']:.2f}")
    else:
        print("  Status:       ACTIVE SESSION (Running...)")
    print("-" * 55)


def main():
    service = CafeService()

    while True:
        print("\n" + "#" * 65)
        print("  INTERNET CAFE MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Computer Terminal")
        print(" 2. Start Customer Session")
        print(" 3. End Customer Session & Compute Bill")
        print(" 4. Record Customer Payment")
        print(" 5. View Terminal Status & Availability")
        print(" 6. View Active Sessions")
        print(" 7. View Completed Sessions")
        print(" 8. Generate Daily Revenue Report")
        print(" 9. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            print_header("REGISTER COMPUTER TERMINAL")
            code = input("Enter terminal code (e.g. PC-01): ").strip()
            ip = input("Enter IP address: ").strip()
            specs = input("Enter hardware specifications: ").strip()
            try:
                rate = float(input("Enter hourly usage rate ($): ").strip())
                comp = service.register_computer(code, ip, specs, rate)
                print(f"\n[Success] Terminal '{comp['computer_code']}' registered! Rate: ${comp['hourly_rate']:.2f}/hr. Status: {comp['status']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("START CUSTOMER SESSION")
            c_code = input("Enter computer terminal code: ").strip()
            cust = input("Enter customer full name: ").strip()
            s_time = input("Enter start time (YYYY-MM-DD HH:MM:SS or Enter for now): ").strip()
            try:
                sess = service.start_session(c_code, cust, s_time or None)
                print(f"\n[Session Started] ID: #{sess['session_id']}")
                print_session_ticket(sess)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("END CUSTOMER SESSION")
            s_id = input("Enter session ID (e.g. SES-XXXXXX): ").strip()
            e_time = input("Enter end time (YYYY-MM-DD HH:MM:SS or Enter for now): ").strip()
            try:
                sess = service.end_session(s_id, e_time or None)
                print(f"\n[Session Ended] Total duration: {sess['duration_minutes']} mins.")
                print_session_ticket(sess)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("RECORD SESSION PAYMENT")
            s_id = input("Enter session ID: ").strip()
            try:
                amt = float(input("Enter payment amount tendered ($): ").strip())
                sess = service.record_payment(s_id, amt)
                print(f"\n[Payment Confirmed] Receipt #{sess['session_id']} marked as Paid.")
                print_session_ticket(sess)
            except ValueError as e:
                print(f"\n[Payment Rejected] {e}")

        elif choice == "5":
            print_header("TERMINAL AVAILABILITY")
            comps = service.list_computers()
            if not comps:
                print("No terminals registered.")
            else:
                print(f"{'Terminal':<10} {'IP Address':<16} {'Hourly Rate':>12} {'Status':<14} {'Hardware':<22}")
                print("-" * 76)
                for c in comps:
                    print(f"{c['computer_code']:<10} {c['ip_address']:<16} ${c['hourly_rate']:>11.2f} {c['status']:<14} {c['specs'][:21]:<22}")

        elif choice == "6":
            print_header("ACTIVE RUNNING SESSIONS")
            active = service.list_sessions("Active")
            if not active:
                print("No active sessions currently running.")
            else:
                print(f"{'Session ID':<12} {'Customer':<18} {'Terminal':<10} {'Start Time':<20} {'Status':<8}")
                print("-" * 70)
                for a in active:
                    print(f"{a['session_id']:<12} {a['customer_name'][:17]:<18} {a['computer_code']:<10} {a['start_time']:<20} {a['status']:<8}")

        elif choice == "7":
            print_header("COMPLETED SESSIONS")
            completed = service.list_sessions("Completed")
            if not completed:
                print("No completed sessions found.")
            else:
                print(f"{'Session ID':<12} {'Customer':<16} {'Terminal':<10} {'Mins':>6} {'Bill':>9} {'Payment':<8}")
                print("-" * 64)
                for c in completed:
                    print(f"{c['session_id']:<12} {c['customer_name'][:15]:<16} {c['computer_code']:<10} {c['duration_minutes']:>6} ${c['total_bill']:>8.2f} {c['payment_status']:<8}")

        elif choice == "8":
            print_header("DAILY REVENUE REPORT")
            d_str = input("Enter report date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                rep = service.generate_daily_revenue_report(d_str or None)
                print(f"\n--- Daily Revenue Report: {rep['report_date']} ---")
                print(f"Total Completed Sessions:     {rep['completed_sessions']:>10}")
                print(f"Total Billable Time:          {rep['total_usage_hours']:>10} hrs ({rep['total_usage_minutes']} mins)")
                print(f"Total Invoiced Amount:       ${rep['total_billed']:>10,.2f}")
                print(f"Total Collections Received:  ${rep['total_revenue_collected']:>10,.2f}")

                if rep["terminal_breakdown"]:
                    print("\nUtilization by Terminal:")
                    print(f"{'Terminal':<12} {'Sessions':>10} {'Usage (Mins)':>14} {'Revenue':>12}")
                    print("-" * 50)
                    for t in rep["terminal_breakdown"]:
                        print(f"{t['computer_code']:<12} {t['sessions_count']:>10} {t['terminal_minutes']:>14} ${t['revenue']:>11.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "9":
            print("\nExiting Internet Cafe Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()
