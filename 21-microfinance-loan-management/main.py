#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Microfinance Loan Management System.
"""

import sys
from loan_service import LoanService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_loan_docket(l: dict):
    print("\n" + "-" * 60)
    print(f"  LOAN CONTRACT #{l['loan_reference']}")
    print(f"  Borrower: {l['borrower_name']} ({l['borrower_code']}) | Phone: {l['borrower_phone']}")
    print(f"  Status:   {l['status']} | App Date: {l['application_date']}")
    if l.get("approval_date"):
        print(f"  Approved: {l['approval_date']} | Due Date: {l['due_date']}")
    print("-" * 60)
    print(f"  Principal Amount:      ${l['principal_amount']:>12,.2f}")
    print(f"  Annual Interest Rate:   {l['interest_rate_percent']:>11.1f}%")
    print(f"  Loan Period:            {l['repayment_period_months']:>11} months")
    print(f"  Total Interest Accrued:${l['total_interest']:>12,.2f}")
    print(f"  Total Payable:         ${l['total_payable']:>12,.2f}")
    print(f"  Monthly Installment:   ${l['monthly_installment']:>12,.2f}")
    print("-" * 60)
    print(f"  Total Amount Repaid:   ${l['amount_repaid']:>12,.2f}")
    print(f"  OUTSTANDING BALANCE:   ${l['outstanding_balance']:>12,.2f}")
    if l.get("excess_records"):
        print("\n  Excess Payment Logs:")
        for ex in l["excess_records"]:
            print(f"    - Ref: {ex['excess_reference']} | Overpayment: ${ex['excess_amount']:.2f} on {ex['payment_date']}")
    print("-" * 60)


def main():
    service = LoanService()

    while True:
        print("\n" + "#" * 65)
        print("  MICROFINANCE LOAN MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Customer / Borrower")
        print(" 2. Create Loan Application")
        print(" 3. Approve / Reject Loan Application")
        print(" 4. View Repayment Schedule")
        print(" 5. Record Loan Repayment")
        print(" 6. View Overdue Loans")
        print(" 7. View Loan Portfolio & Balances")
        print(" 8. Generate Loan Performance Report")
        print(" 9. Search / View Loan Details")
        print(" 10. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-10): ").strip()

        if choice == "1":
            print_header("REGISTER BORROWER")
            code = input("Enter borrower code (e.g. BOR-101): ").strip()
            name = input("Enter full name: ").strip()
            phone = input("Enter phone number: ").strip()
            email = input("Enter email (optional): ").strip()
            try:
                inc = float(input("Enter monthly income ($): ").strip() or "0")
                b = service.register_borrower(code, name, phone, email, inc)
                print(f"\n[Success] Borrower '{b['name']}' ({b['borrower_code']}) registered successfully!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("CREATE LOAN APPLICATION")
            b_code = input("Enter borrower code: ").strip()
            try:
                principal = float(input("Enter requested loan amount ($): ").strip())
                rate = float(input("Enter annual interest rate (e.g. 12 for 12%): ").strip())
                months = int(input("Enter repayment period (in months): ").strip())
                app_date = input("Enter application date (YYYY-MM-DD or Enter for today): ").strip()
                loan = service.create_loan_application(b_code, principal, rate, months, app_date or None)
                print(f"\n[Success] Loan Application #{loan['loan_reference']} created!")
                print_loan_docket(loan)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("APPROVE / REJECT LOAN APPLICATION")
            ref = input("Enter loan reference number (e.g. LN-XXXXXX): ").strip()
            print("Decision: 1: Approve, 2: Reject")
            d_opt = input("Choice (1 or 2): ").strip()
            dec = "Approved" if d_opt == "1" else "Rejected"
            d_date = input("Enter decision date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                loan = service.decide_loan_application(ref, dec, d_date or None)
                print(f"\n[Success] Loan #{ref} marked as {loan['status']}!")
                print_loan_docket(loan)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("REPAYMENT SCHEDULE")
            ref = input("Enter loan reference number: ").strip()
            try:
                sched = service.calculate_repayment_schedule(ref)
                print(f"\n--- Repayment Schedule for #{ref.upper()} ---")
                print(f"{'Inst #':<8} {'Due Date':<14} {'Installment ($)':>16} {'Remaining Balance ($)':>22}")
                print("-" * 64)
                for s in sched:
                    print(f"{s['installment_number']:<8} {s['due_date']:<14} ${s['installment_amount']:>15,.2f} ${s['remaining_balance_after']:>21,.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("RECORD LOAN REPAYMENT")
            ref = input("Enter loan reference number: ").strip()
            try:
                amt = float(input("Enter repayment amount ($): ").strip())
                method = input("Enter payment method (Cash, Bank Transfer, Mobile Money, default Bank Transfer): ").strip() or "Bank Transfer"
                p_date = input("Enter payment date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Enter payment notes (optional): ").strip()
                res = service.record_repayment(ref, amt, p_date or None, method, notes)
                print(f"\n[Payment Logged] Ref #{res['latest_payment_ref']} | Loan Status: {res['status']}")
                if res.get("excess_logged", 0) > 0:
                    print(f"  [Notice] Excess payment of ${res['excess_logged']:.2f} explicitly recorded under voucher #{res['excess_reference']}.")
                print_loan_docket(res)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("OVERDUE LOANS ALERT")
            as_of = input("Enter check date (YYYY-MM-DD or Enter for today): ").strip()
            try:
                overdue = service.get_overdue_loans(as_of or None)
                if not overdue:
                    print("No overdue loans! Portfolio is in good standing.")
                else:
                    print(f"Found {len(overdue)} overdue loan(s):\n")
                    print(f"{'Loan Ref':<12} {'Borrower':<18} {'Phone':<12} {'Due Date':<12} {'Days Late':>10} {'Balance Due':>14}")
                    print("-" * 82)
                    for o in overdue:
                        print(f"{o['loan_reference']:<12} {o['borrower_name'][:17]:<18} {o['borrower_phone']:<12} {o['due_date']:<12} {o['days_overdue']:>10} ${o['outstanding_balance']:>13,.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("LOAN PORTFOLIO")
            print("Filter Status: 1: All, 2: Active, 3: Repaid, 4: Applied")
            f_opt = input("Choice (1-4) [Default 1]: ").strip()
            f_map = {"2": "Active", "3": "Repaid", "4": "Applied"}
            stat_filter = f_map.get(f_opt, None)

            loans = service.list_loans(stat_filter)
            if not loans:
                print("No loans found.")
            else:
                print(f"{'Ref #':<12} {'Borrower':<18} {'Principal':>10} {'Payable':>10} {'Repaid':>10} {'Balance':>10} {'Status':<10}")
                print("-" * 84)
                for l in loans:
                    print(f"{l['loan_reference']:<12} {l['borrower_name'][:17]:<18} ${l['principal_amount']:>9.0f} ${l['total_payable']:>9.0f} ${l['amount_repaid']:>9.0f} ${l['outstanding_balance']:>9.0f} {l['status']:<10}")

        elif choice == "8":
            print_header("LOAN PERFORMANCE REPORT")
            rep = service.generate_loan_performance_report()
            print(f"Total Applications Received:     {rep['total_applications']}")
            print(f"Disbursed Loans:                 {rep['disbursed_loans_count']}")
            print(f"Fully Repaid Loans:              {rep['fully_repaid_loans']}")
            print(f"Currently Overdue Loans:         {rep['overdue_loans_count']}")
            print("-" * 50)
            print(f"Total Principal Disbursed:      ${rep['total_principal_disbursed']:>12,.2f}")
            print(f"Total Interest Expected:        ${rep['total_interest_expected']:>12,.2f}")
            print(f"Total Expected Portfolio:       ${rep['total_expected_recovery']:>12,.2f}")
            print(f"Total Capital Recovered:        ${rep['total_capital_recovered']:>12,.2f}")
            print(f"Outstanding Portfolio Balance:  ${rep['outstanding_portfolio_balance']:>12,.2f}")
            print(f"Recovery Efficiency:             {rep['recovery_rate_percent']:>11.1f}%")

        elif choice == "9":
            print_header("SEARCH / VIEW LOAN")
            ref = input("Enter loan reference number: ").strip()
            try:
                l = service.get_loan_details(ref)
                print_loan_docket(l)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "10":
            print("\nExiting Microfinance Loan Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 10.")


if __name__ == "__main__":
    main()
