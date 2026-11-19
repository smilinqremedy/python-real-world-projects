#!/usr/bin/env python3
"""
Interactive Command-Line Interface for School Fee Payment Management System.
"""

import sys
from fee_service import FeeService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_receipt_card(b: dict):
    print("\n" + "-" * 60)
    print(f"  OFFICIAL SCHOOL FEE RECEIPT")
    if "latest_receipt_reference" in b:
        print(f"  Receipt #:   {b['latest_receipt_reference']} | Date: {b.get('payment_date')}")
        print(f"  Amount Paid: ${b.get('amount_paid_now', 0):,.2f}")
        print("-" * 60)
    print(f"  Student:     {b['name']} ({b['student_reg_no']})")
    print(f"  Class:       {b['class_name']} ({b['class_code']})")
    print(f"  Academic:    {b['academic_session']} | {b['academic_term']}")
    print(f"  Parent:      {b['parent_name']} (Tel: {b['parent_phone']})")
    print("-" * 60)
    print(f"  Session Term Fee:     ${b['term_fee']:>12,.2f}")
    print(f"  Cumulative Paid:      ${b['total_paid']:>12,.2f}")
    print(f"  OUTSTANDING BALANCE:  ${b['outstanding_balance']:>12,.2f}")
    print(f"  Payment Status:        {b['payment_status'].upper()}")
    print("-" * 60)


def main():
    service = FeeService()

    while True:
        print("\n" + "#" * 65)
        print("  SCHOOL FEE PAYMENT MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Define Class & Fee Structure")
        print(" 2. Register Student & Assign to Class")
        print(" 3. Record Student Fee Payment")
        print(" 4. View Student Fee Balance & Status")
        print(" 5. View Students with Unpaid / Partial Fees")
        print(" 6. Search Student Payment History")
        print(" 7. List Classes & Enrollment")
        print(" 8. Generate Financial Collection Report")
        print(" 9. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            print_header("DEFINE CLASS & FEE")
            code = input("Enter class code (e.g. GR-7A): ").strip()
            name = input("Enter class title (e.g. Grade 7 Alpha): ").strip()
            sess = input("Enter academic session (e.g. 2026/2027): ").strip()
            try:
                fee = float(input("Enter term fee per student ($): ").strip())
                c = service.define_class(code, name, sess, fee)
                print(f"\n[Success] Class '{c['name']}' ({c['class_code']}) defined! Fee: ${c['term_fee']:.2f}/term.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER STUDENT")
            reg = input("Enter student registration number (e.g. STU-001): ").strip()
            name = input("Enter student full name: ").strip()
            c_code = input("Enter assigned class code: ").strip()
            p_name = input("Enter parent / guardian name: ").strip()
            p_phone = input("Enter parent phone number: ").strip()
            try:
                s = service.register_student(reg, name, c_code, p_name, p_phone)
                print(f"\n[Success] Student '{s['name']}' ({s['student_reg_no']}) registered in class {s['class_code']}!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD FEE PAYMENT")
            reg = input("Enter student registration number: ").strip()
            try:
                amt = float(input("Enter payment installment amount ($): ").strip())
                term = input("Enter academic term (Term 1, Term 2, Term 3, default Term 1): ").strip() or "Term 1"
                method = input("Enter payment method (Bank Transfer, Card, Cash, default Bank Transfer): ").strip() or "Bank Transfer"
                p_date = input("Enter payment date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Payment notes (optional): ").strip()

                rec = service.record_fee_payment(reg, amt, term, p_date or None, method, notes)
                print(f"\n[Success] Payment of ${amt:,.2f} recorded!")
                print_receipt_card(rec)
            except ValueError as e:
                print(f"\n[Payment Rejected] {e}")

        elif choice == "4":
            print_header("STUDENT FEE BALANCE")
            reg = input("Enter student registration number: ").strip()
            term = input("Enter academic term (default Term 1): ").strip() or "Term 1"
            try:
                b = service.get_student_balance(reg, term)
                print_receipt_card(b)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("UNPAID & ARREARS LIST")
            term = input("Enter academic term (default Term 1): ").strip() or "Term 1"
            c_code = input("Filter by class code (or Enter for whole school): ").strip()
            try:
                unpaid = service.get_unpaid_students(term, c_code or None)
                if not unpaid:
                    print("All students in the requested scope have settled their fees in full!")
                else:
                    print(f"Found {len(unpaid)} student(s) with pending balances:\n")
                    print(f"{'Reg #':<12} {'Student Name':<20} {'Class':<10} {'Term Fee':>10} {'Paid':>10} {'Balance Due':>13} {'Status':<8}")
                    print("-" * 88)
                    for s in unpaid:
                        print(f"{s['student_reg_no']:<12} {s['name'][:19]:<20} {s['class_code']:<10} ${s['term_fee']:>9.2f} ${s['total_paid']:>9.2f} ${s['outstanding_balance']:>12.2f} {s['payment_status']:<8}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("PAYMENT HISTORY")
            reg = input("Enter student registration number: ").strip()
            try:
                hist = service.get_student_payment_history(reg)
                print(f"\nPayment Ledger for: {hist['name']} ({hist['student_reg_no']}) | Class: {hist['class_name']}")
                print(f"Lifetime Payments Total: ${hist['lifetime_paid']:,.2f}")
                if not hist["payments"]:
                    print("  [No payment transactions recorded yet]")
                else:
                    print(f"\n{'Receipt #':<12} {'Date':<12} {'Term':<10} {'Method':<14} {'Amount':>10}")
                    print("-" * 62)
                    for p in hist["payments"]:
                        print(f"{p['receipt_reference']:<12} {p['payment_date']:<12} {p['academic_term']:<10} {p['payment_method'][:13]:<14} ${p['amount']:>9.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("CLASSES & ENROLLMENT")
            classes = service.list_classes()
            if not classes:
                print("No classes created yet.")
            else:
                print(f"{'Code':<12} {'Class Name':<22} {'Session':<12} {'Term Fee':>10} {'Enrolled':>10}")
                print("-" * 70)
                for c in classes:
                    print(f"{c['class_code']:<12} {c['name'][:21]:<22} {c['academic_session']:<12} ${c['term_fee']:>9.2f} {c['enrolled_students']:>10}")

        elif choice == "8":
            print_header("FINANCIAL COLLECTION REPORT")
            term = input("Enter academic term (default Term 1): ").strip() or "Term 1"
            try:
                rep = service.generate_financial_report(term)
                print(f"\n--- Financial Collection Report: {rep['academic_term']} ---")
                print(f"Total Enrolled Students:        {rep['total_enrolled_students']:>10}")
                print(f"Total Expected Tuition:        ${rep['total_expected_revenue']:>12,.2f}")
                print(f"Total Collections Received:    ${rep['total_collected_revenue']:>12,.2f}")
                print(f"Total Outstanding Fee Debt:    ${rep['total_outstanding_debt']:>12,.2f}")
                print(f"Overall Collection Efficiency:  {rep['overall_collection_rate']:>11.1f}%")

                if rep["classes"]:
                    print("\nClass-by-Class Breakdown:")
                    print(f"{'Class':<12} {'Students':>8} {'Expected':>12} {'Collected':>12} {'Arrears':>12} {'Rate':>7}")
                    print("-" * 68)
                    for c in rep["classes"]:
                        print(f"{c['class_code']:<12} {c['enrolled_students']:>8} ${c['expected_revenue']:>11,.0f} ${c['collected_revenue']:>11,.0f} ${c['outstanding_debt']:>11,.0f} {c['collection_rate_percent']:>6.1f}%")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "9":
            print("\nExiting School Fee Payment Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()
