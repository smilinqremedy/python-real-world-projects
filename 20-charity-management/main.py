#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Donation and Charity Management System.
"""

import sys
from charity_service import CharityService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = CharityService()

    while True:
        print("\n" + "#" * 65)
        print("  DONATION & CHARITY MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Donor")
        print(" 2. Create Fundraising Campaign")
        print(" 3. Record Donation")
        print(" 4. Record Approved Fund Distribution")
        print(" 5. View Campaign Balance & Metrics")
        print(" 6. List All Campaigns")
        print(" 7. Generate Financial & Treasury Report")
        print(" 8. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-8): ").strip()

        if choice == "1":
            print_header("REGISTER DONOR")
            code = input("Enter donor code (e.g. DNR-101): ").strip()
            name = input("Enter donor full name / entity: ").strip()
            email = input("Enter donor email: ").strip()
            phone = input("Enter donor phone: ").strip()
            print("Select Donor Type: 1: Individual, 2: Corporate, 3: Foundation")
            t_opt = input("Choice (1-3) [Default 1]: ").strip()
            t_map = {"1": "Individual", "2": "Corporate", "3": "Foundation"}
            dtype = t_map.get(t_opt, "Individual")
            try:
                d = service.register_donor(code, name, email, phone, dtype)
                print(f"\n[Success] Donor '{d['name']}' ({d['donor_code']}) [{d['donor_type']}] registered!")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("CREATE FUNDRAISING CAMPAIGN")
            code = input("Enter campaign code (e.g. CMP-CLEANWATER): ").strip()
            name = input("Enter campaign title: ").strip()
            desc = input("Enter campaign cause / description: ").strip()
            try:
                target = float(input("Enter fundraising goal target ($): ").strip())
                s_date = input("Enter campaign start date (YYYY-MM-DD): ").strip()
                e_date = input("Enter campaign end date (YYYY-MM-DD): ").strip()
                camp = service.create_campaign(code, name, desc, target, s_date, e_date)
                print(f"\n[Success] Campaign '{camp['name']}' ({camp['campaign_code']}) launched! Goal: ${camp['target_amount']:,.2f}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD DONATION")
            d_code = input("Enter donor code: ").strip()
            c_code = input("Enter campaign code: ").strip()
            try:
                amt = float(input("Enter donation amount ($): ").strip())
                method = input("Payment method (Bank Transfer, Card, Cheque, Cash, default Bank Transfer): ").strip() or "Bank Transfer"
                d_date = input("Donation date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Donation notes / dedication: ").strip()
                don = service.record_donation(d_code, c_code, amt, method, d_date or None, notes)
                print(f"\n[Success] Donation Received! Receipt #{don['receipt_reference']}")
                print(f"Donor:    {don['donor_name']}")
                print(f"Campaign: {don['campaign_name']}")
                print(f"Amount:  ${don['amount']:,.2f} via {don['payment_method']} on {don['donation_date']}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("RECORD APPROVED FUND DISTRIBUTION")
            c_code = input("Enter campaign code: ").strip()
            recip = input("Enter recipient organization / beneficiary: ").strip()
            purp = input("Enter specific purpose / expenditure item: ").strip()
            try:
                amt = float(input("Enter disbursement amount ($): ").strip())
                d_date = input("Disbursement date (YYYY-MM-DD or Enter for today): ").strip()
                notes = input("Approval authority / board notes: ").strip()
                disb = service.record_disbursement(c_code, recip, purp, amt, d_date or None, notes)
                print(f"\n[Disbursement Approved] Voucher #{disb['disbursement_reference']}")
                print(f"Campaign:         {disb['campaign_name']}")
                print(f"Recipient:        {disb['recipient']} ({disb['purpose']})")
                print(f"Amount Released: ${disb['amount']:,.2f}")
                print(f"Remaining Funds: ${disb['remaining_balance']:,.2f}")
            except ValueError as e:
                print(f"\n[Disbursement Blocked] {e}")

        elif choice == "5":
            print_header("CAMPAIGN BALANCE & PERFORMANCE")
            c_code = input("Enter campaign code: ").strip()
            try:
                bal = service.get_campaign_balance(c_code)
                print(f"\n--- Campaign: {bal['name']} ({bal['campaign_code']}) ---")
                print(f"Status:            {bal['status']}")
                print(f"Target Goal:      ${bal['target_amount']:>12,.2f}")
                print(f"Total Donations:  ${bal['total_raised']:>12,.2f} ({bal['progress_percentage']}% of goal)")
                print(f"Funds Disbursed:  ${bal['total_disbursed']:>12,.2f}")
                print(f"AVAILABLE FUNDS:  ${bal['available_balance']:>12,.2f}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("ALL FUNDRAISING CAMPAIGNS")
            campaigns = service.list_campaigns()
            if not campaigns:
                print("No campaigns created yet.")
            else:
                print(f"{'Code':<14} {'Campaign Title':<22} {'Target':>10} {'Raised':>10} {'Disbursed':>10} {'Available':>10} {'Goal %':>7}")
                print("-" * 90)
                for c in campaigns:
                    print(f"{c['campaign_code']:<14} {c['name'][:21]:<22} ${c['target_amount']:>9.0f} ${c['total_raised']:>9.0f} ${c['total_disbursed']:>9.0f} ${c['available_balance']:>9.0f} {c['progress_percentage']:>6.1f}%")

        elif choice == "7":
            print_header("FINANCIAL & TREASURY REPORT")
            rep = service.generate_financial_report()
            print(f"Total Donations Processed:    {rep['total_donations_count']:>10}")
            print(f"Total Capital Raised:        ${rep['total_funds_raised']:>10,.2f}")
            print(f"Total Distributions Approved: {rep['total_disbursements_count']:>10}")
            print(f"Total Capital Distributed:   ${rep['total_funds_distributed']:>10,.2f}")
            print(f"NET TREASURY BALANCE:        ${rep['net_treasury_balance']:>10,.2f}")

            if rep["top_donors"]:
                print("\nTop Contributing Donors:")
                for d in rep["top_donors"]:
                    print(f"  * {d['donor_name']} [{d['donor_type']}]: ${d['total_contributed']:,.2f} across {d['donations_count']} donation(s)")

        elif choice == "8":
            print("\nExiting Donation and Charity Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 8.")


if __name__ == "__main__":
    main()
