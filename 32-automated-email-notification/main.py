"""
Command-Line Interface for Automated Email Notification System.
"""
import sys
import os
from datetime import datetime, timedelta
from email_service import EmailService


def print_header(title):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def seed_demo_data(service):
    try:
        service.register_recipient("Customer Sarah", "sarah@example.com")
        service.register_recipient("Partner Michael", "michael@enterprise.org")
        service.register_recipient("Client Chloe", "chloe@startup.io")

        service.create_template(
            name="appointment_reminder",
            subject_template="Appointment Reminder: {service_name} on {date}",
            body_template="Dear {name},\n\nThis is a quick reminder regarding your upcoming appointment for {service_name} scheduled on {date}.\nLocation: {location}\n\nWarm regards,\nClient Services Team",
            description="Appointment scheduling reminder"
        )

        service.create_template(
            name="payment_receipt",
            subject_template="Payment Receipt #{receipt_id}",
            body_template="Hello {name},\n\nWe have successfully received your payment of ${amount:.2f} for Invoice #{invoice_id}.\nDate: {payment_date}\n\nThank you for your business!",
            description="Payment confirmation receipt"
        )

        service.create_template(
            name="overdue_notice",
            subject_template="Notice: Overdue Balance for Account #{account_id}",
            body_template="Dear {name},\n\nOur records indicate an outstanding balance of ${balance:.2f} that was due on {due_date}.\nPlease remit payment to avoid service interruption.\n\nFinance Operations",
            description="Payment reminder and overdue notice"
        )
        print(" Demo recipients and email templates seeded successfully.")
    except Exception as e:
        print(f" Demo seeding notice: {e}")


def main():
    service = EmailService()
    seed_demo_data(service)

    while True:
        mode_str = "TEST MODE (MOCK SIMULATION)" if service.test_mode else "LIVE SMTP MODE"
        print_header(f"Automated Email Notification System [{mode_str}]")
        print("1. Register Recipient")
        print("2. Manage Recipient Consent (Subscribe / Unsubscribe)")
        print("3. Create Email Template")
        print("4. Send Instant Individual Email")
        print("5. Send Personalized Templated Email")
        print("6. Schedule Automated Email Reminder")
        print("7. Process Pending Queue Immediately")
        print("8. View Email Sending History & Logs")
        print("9. Generate Activity & Deliverability Report")
        print("10. List Recipients & Templates")
        print("11. Toggle Test Mode")
        print("0. Exit")

        choice = input("\nEnter selection (0-11): ").strip()

        if choice == "1":
            name = input("Recipient Name: ")
            email = input("Email Address: ")
            try:
                service.register_recipient(name, email)
                print(f" Recipient '{name}' ({email}) registered.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "2":
            email = input("Recipient Email: ")
            status = input("Consent status (subscribed / unsubscribed): ")
            try:
                service.update_consent(email, status)
                print(f" Recipient '{email}' consent updated to '{status}'.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "3":
            tname = input("Template Key (e.g. welcome_email): ")
            subj = input("Subject Template (e.g. Welcome {name}!): ")
            print("Enter Body Template (support placeholders like {name}, {date}):")
            body = input("> ")
            desc = input("Description: ")
            try:
                service.create_template(tname, subj, body, desc)
                print(f" Template '{tname}' created.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "4":
            email = input("Recipient Email: ")
            subj = input("Subject: ")
            body = input("Body: ")
            try:
                res = service.send_instant(email, subj, body)
                print(f" Email queued (#{res['queue_id']}) and processed.")
                print(f" Outcome: {res['dispatch_summary']}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "5":
            email = input("Recipient Email: ")
            tname = input("Template Key (e.g. appointment_reminder, payment_receipt): ")
            template = service.get_template(tname)
            if not template:
                print(f" Template '{tname}' does not exist.")
                continue

            print("Enter context parameters:")
            name = input("Recipient Name: ")
            if tname == "appointment_reminder":
                srv = input("Service Name: ")
                dt = input("Date & Time: ")
                loc = input("Location: ")
                ctx = {"name": name, "service_name": srv, "date": dt, "location": loc}
            elif tname == "payment_receipt":
                rec_id = input("Receipt ID: ")
                amt = float(input("Amount ($): "))
                inv_id = input("Invoice ID: ")
                pdt = input("Payment Date: ")
                ctx = {"name": name, "receipt_id": rec_id, "amount": amt, "invoice_id": inv_id, "payment_date": pdt}
            elif tname == "overdue_notice":
                acc_id = input("Account ID: ")
                bal = float(input("Balance ($): "))
                ddt = input("Due Date: ")
                ctx = {"name": name, "account_id": acc_id, "balance": bal, "due_date": ddt}
            else:
                ctx = {"name": name}

            try:
                qid = service.send_templated_email(email, tname, ctx)
                res = service.process_queue()
                print(f" Templated email dispatched: {res}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "6":
            email = input("Recipient Email: ")
            subj = input("Subject: ")
            body = input("Body: ")
            minutes = int(input("Schedule delivery in how many minutes from now?: "))
            sched_time = datetime.now() + timedelta(minutes=minutes)
            try:
                qid = service.queue_email(email, subj, body, scheduled_at=sched_time)
                print(f" Email scheduled for {sched_time.strftime('%Y-%m-%d %H:%M:%S')} (Queue ID #{qid})")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "7":
            try:
                res = service.process_queue()
                print(f" Queue processed: {res['processed']} attempted, {res['succeeded']} succeeded, {res['failed']} failed.")
            except Exception as e:
                print(f" Error processing queue: {e}")

        elif choice == "8":
            filt = input("Filter by recipient email (or press Enter for all): ").strip()
            history = service.get_history(recipient_email=filt if filt else None, limit=20)
            print(f"\nRecent Email Logs ({len(history)} records):")
            print("-" * 65)
            for h in history:
                print(f"[{h['sent_at']}] To: {h['recipient_email']} | Status: {h['status'].upper()} ({h['delivery_mode']})")
                print(f"   Subject: {h['subject']}")
                if h["error_message"]:
                    print(f"   Error: {h['error_message']}")

        elif choice == "9":
            try:
                rep = service.generate_activity_report()
                print_header("Email Activity & Deliverability Report")
                print(f"Total Registered Recipients: {rep['total_recipients']} ({rep['unsubscribed_recipients']} unsubscribed)")
                print(f"Queue Status: {rep['queue_pending']} pending, {rep['queue_sent']} sent, {rep['queue_failed']} failed, {rep['queue_cancelled']} cancelled")
                print(f"Total Dispatch Attempts: {rep['total_attempts']}")
                print(f"Successful Deliveries: {rep['successful_deliveries']}")
                print(f"Failed Deliveries: {rep['failed_deliveries']}")
                print(f"Deliverability Rate: {rep['deliverability_rate_pct']}%")
                print(f"Operating Mode: {'TEST / SIMULATION' if rep['test_mode_active'] else 'LIVE SMTP'}")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "10":
            print("\n--- Recipients ---")
            for r in service.list_recipients():
                print(f"- {r['name']} <{r['email']}> [{r['consent_status'].upper()}]")
            print("\n--- Templates ---")
            for t in service.list_templates():
                print(f"- {t['name']}: {t['description']}")

        elif choice == "11":
            service.test_mode = not service.test_mode
            print(f" Switched Test Mode to: {service.test_mode}")

        elif choice == "0":
            print("Exiting Automated Email Notification System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice, please select 0-11.")


if __name__ == "__main__":
    main()
