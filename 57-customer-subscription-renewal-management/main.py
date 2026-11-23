"""
Command-Line Interface for Customer Subscription & Renewal Management System.
"""
import sys
from subscription_service import SubscriptionService, InvalidRenewalError


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def seed_demo_data(service: SubscriptionService):
    try:
        service.create_plan("STARTER-M", "Starter Monthly", "Monthly", 5000.0, "Basic access for individuals")
        service.create_plan("PRO-M", "Professional Monthly", "Monthly", 15000.0, "Advanced tooling for teams")
        service.create_plan("PRO-Y", "Professional Annual", "Yearly", 150000.0, "Annual discounted professional plan")
        service.create_plan("ENTERPRISE-Q", "Enterprise Quarterly", "Quarterly", 75000.0, "Enterprise suite for large firms")

        service.register_customer("CUST-101", "Amara Okonkwo", "amara@novatech.ng", "+2348031112233", "NovaTech Solutions")
        service.register_customer("CUST-102", "Babatunde Adeleke", "badeleke@lagosfintech.com", "+2348022223344", "Lagos Fintech Labs")
        service.register_customer("CUST-103", "Chioma Nwosu", "chioma@greenenergy.ng", "+2348099998877", "Green Energy Africa")

        sub1 = service.create_subscription("CUST-101", "PRO-M")
        sub2 = service.create_subscription("CUST-102", "ENTERPRISE-Q")
        sub3 = service.create_subscription("CUST-103", "STARTER-M")
        print(f"Demo data seeded successfully. Active Subscriptions: {sub1}, {sub2}, {sub3}")
    except Exception as e:
        print(f"Note: Seed data already present or error: {e}")


def main():
    service = SubscriptionService()

    while True:
        print_header("Customer Subscription & Renewal Management")
        print("1. Register New Customer")
        print("2. List Customers")
        print("3. Create Subscription Plan")
        print("4. List Available Plans")
        print("5. Create New Subscription")
        print("6. View Subscription Details")
        print("7. Renew Subscription")
        print("8. Cancel Subscription")
        print("9. Check & Update Overdue Expirations (Grace / Suspended)")
        print("10. View Subscriptions Expiring Soon")
        print("11. Generate MRR & Revenue Dashboard")
        print("12. Seed Demo Data")
        print("0. Exit")

        choice = input("\nSelect an option [0-12]: ").strip()

        if choice == "1":
            print_header("Register Customer")
            cid = input("Customer ID (e.g. CUST-105): ").strip()
            name = input("Full Name: ").strip()
            email = input("Email Address: ").strip()
            phone = input("Phone Number: ").strip()
            company = input("Company / Organization (optional): ").strip() or None
            try:
                row_id = service.register_customer(cid, name, email, phone, company)
                print(f"Customer registered successfully! (DB ID: {row_id})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            print_header("Customer Directory")
            customers = service.list_customers()
            if not customers:
                print("No customers registered yet.")
            else:
                for c in customers:
                    print(f"[{c['customer_id']}] {c['full_name']} | {c['email']} | {c['phone']} | {c['company'] or 'N/A'}")

        elif choice == "3":
            print_header("Create Subscription Plan")
            code = input("Plan Code (e.g. BIZ-M): ").strip()
            name = input("Plan Name (e.g. Business Monthly): ").strip()
            cycle = input("Billing Cycle (Monthly / Quarterly / Yearly): ").strip()
            try:
                price = float(input("Price (NGN): ").strip())
                desc = input("Description: ").strip() or None
                service.create_plan(code, name, cycle, price, desc)
                print(f"Plan '{code}' created successfully!")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            print_header("Active Subscription Plans")
            plans = service.list_plans()
            for p in plans:
                print(f"[{p['plan_code']}] {p['name']} - ₦{p['price']:,.2f} / {p['billing_cycle']} ({p['description'] or ''})")

        elif choice == "5":
            print_header("Create Subscription")
            cid = input("Customer ID: ").strip()
            code = input("Plan Code: ").strip()
            s_date = input("Start Date (YYYY-MM-DD or leave blank for today): ").strip() or None
            try:
                ref = service.create_subscription(cid, code, s_date)
                print(f"Subscription activated! Reference: {ref}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "6":
            print_header("Subscription Details")
            ref = input("Subscription Reference (e.g. SUB-20261120-1234): ").strip()
            try:
                sub = service.get_subscription_details(ref)
                print(f"\nReference:    {sub['subscription_ref']}")
                print(f"Customer:     {sub['customer_name']} ({sub['customer_id']})")
                print(f"Email:        {sub['customer_email']}")
                print(f"Plan:         {sub['plan_name']} (₦{sub['plan_price']:,.2f} / {sub['billing_cycle']})")
                print(f"Start Date:   {sub['start_date']}")
                print(f"Expiry Date:  {sub['expiry_date']}")
                print(f"Status:       {sub['status']}")

                print("\nPayment History:")
                for pay in sub["payments"]:
                    print(f" - [{pay['payment_date']}] {pay['payment_ref']} | ₦{pay['amount']:,.2f} via {pay['payment_method']}")

                print("\nRenewal Logs:")
                for r in sub["renewals"]:
                    print(f" - Renewed at {r['renewed_at']}: Expiry shifted from {r['previous_expiry']} to {r['new_expiry']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "7":
            print_header("Renew Subscription")
            ref = input("Subscription Reference: ").strip()
            try:
                amount = float(input("Amount Paid (NGN): ").strip())
                method = input("Payment Method (Credit Card / Bank Transfer / Direct Debit / PayPal) [Credit Card]: ").strip() or "Credit Card"
                res = service.renew_subscription(ref, amount, method)
                print(f"Subscription renewed successfully!")
                print(f"New Expiry Date: {res['new_expiry']}")
                print(f"Payment Reference: {res['payment_ref']}")
            except InvalidRenewalError as ire:
                print(f"RENEWAL BUSINESS RULE VIOLATION: {ire}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "8":
            print_header("Cancel Subscription")
            ref = input("Subscription Reference: ").strip()
            reason = input("Cancellation Reason: ").strip() or "Customer request"
            try:
                service.cancel_subscription(ref, reason)
                print(f"Subscription {ref} has been cancelled.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "9":
            print_header("Run Expiration & Status Check")
            res = service.check_and_update_expirations()
            print(f"Evaluated against reference date: {res['reference_date']}")
            print(f"Subscriptions moved to 'Grace Period' (<= 7 days overdue): {res['newly_grace_period_count']}")
            print(f"Subscriptions moved to 'Suspended' (> 7 days overdue):    {res['newly_suspended_count']}")

        elif choice == "10":
            print_header("Subscriptions Expiring Soon")
            days = input("Days threshold [default 7]: ").strip()
            days = int(days) if days.isdigit() else 7
            expiring = service.get_expiring_soon(days_threshold=days)
            if not expiring:
                print(f"No subscriptions expiring in the next {days} days.")
            else:
                for sub in expiring:
                    print(f"[{sub['subscription_ref']}] {sub['customer_name']} | Plan: {sub['plan_name']} | Expiry: {sub['expiry_date']} | Status: {sub['status']}")

        elif choice == "11":
            print_header("Financial & Subscription Metrics")
            m = service.generate_revenue_report()
            print(f"Total Registered Customers:     {m['total_customers']}")
            print(f"Active Subscriptions:           {m['active_subscriptions']}")
            print(f"Grace Period Subscriptions:     {m['grace_period_subscriptions']}")
            print(f"Suspended Subscriptions:        {m['suspended_subscriptions']}")
            print(f"Cancelled Subscriptions:        {m['cancelled_subscriptions']}")
            print(f"--------------------------------------------------")
            print(f"Monthly Recurring Revenue (MRR): ₦{m['mrr']:,.2f}")
            print(f"Annual Recurring Revenue (ARR):  ₦{m['arr']:,.2f}")
            print(f"Total Cashflow Collected:        ₦{m['total_payments_collected']:,.2f}")

        elif choice == "12":
            seed_demo_data(service)

        elif choice == "0":
            print("Exiting Subscription Management System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose an option from 0 to 12.")


if __name__ == "__main__":
    main()
