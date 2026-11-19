#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Event Registration and Ticketing System.
"""

import sys
from ticketing_service import TicketingService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def print_ticket_pass(t: dict):
    print("\n" + "-" * 55)
    print(f"  EVENT ADMISSION TICKET: #{t['ticket_id']}")
    print(f"  Event:       {t['event_title']} ({t['event_code']})")
    print(f"  Date & Loc:  {t['event_date']} | {t['location']}")
    print("-" * 55)
    print(f"  Attendee:    {t['attendee_name']} ({t['attendee_email']})")
    print(f"  Price Paid:  ${t['price_paid']:.2f} [{t['payment_status']}]")
    check_status = f"CHECKED IN at {t['check_in_time']}" if t['is_checked_in'] else "NOT CHECKED IN"
    print(f"  Check-in:    {check_status}")
    print("-" * 55)


def main():
    service = TicketingService()

    while True:
        print("\n" + "#" * 65)
        print("  EVENT REGISTRATION & TICKETING SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Create Event")
        print(" 2. Register Attendee & Issue Ticket")
        print(" 3. Record Ticket Payment")
        print(" 4. Check-In Attendee via Ticket ID")
        print(" 5. Check Ticket Availability for Event")
        print(" 6. Search / Verify Ticket")
        print(" 7. List All Events")
        print(" 8. Generate Registration & Revenue Report")
        print(" 9. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            print_header("CREATE EVENT")
            code = input("Enter event code (e.g. EVT-CONF26): ").strip()
            title = input("Enter event title: ").strip()
            ev_date = input("Enter event date (YYYY-MM-DD): ").strip()
            location = input("Enter event location / venue: ").strip()
            try:
                price = float(input("Enter ticket price ($): ").strip())
                cap = int(input("Enter maximum seating capacity: ").strip())
                ev = service.create_event(code, title, ev_date, location, price, cap)
                print(f"\n[Success] Event '{ev['title']}' ({ev['event_code']}) created! Capacity: {ev['max_capacity']} seats.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("REGISTER ATTENDEE & ISSUE TICKET")
            code = input("Enter event code: ").strip()
            name = input("Enter attendee full name: ").strip()
            email = input("Enter attendee email: ").strip()
            phone = input("Enter attendee phone: ").strip()
            is_paid_input = input("Mark ticket as paid now? (y/n, default n): ").strip().lower()
            is_paid = (is_paid_input == 'y')
            try:
                t = service.register_attendee(code, name, email, phone, is_paid)
                print(f"\n[Success] Registration successful! Ticket ID: {t['ticket_id']}")
                print_ticket_pass(t)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD TICKET PAYMENT")
            t_id = input("Enter ticket ID (e.g. TCK-XXXXXX): ").strip()
            try:
                t = service.record_payment(t_id)
                print(f"\n[Success] Payment confirmed for ticket #{t_id}!")
                print_ticket_pass(t)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("CHECK-IN ATTENDEE")
            t_id = input("Scan / Enter ticket ID: ").strip()
            try:
                t = service.check_in_attendee(t_id)
                print(f"\n[Verified] Welcome, {t['attendee_name']}! Check-in confirmed.")
                print_ticket_pass(t)
            except ValueError as e:
                print(f"\n[Check-in Failed] {e}")

        elif choice == "5":
            print_header("CHECK EVENT AVAILABILITY")
            code = input("Enter event code: ").strip()
            try:
                avail = service.get_event_availability(code)
                print(f"\n--- Ticket Availability for {avail['title']} ({avail['event_code']}) ---")
                print(f"Date & Location:    {avail['event_date']} | {avail['location']}")
                print(f"Price per Ticket:  ${avail['ticket_price']:.2f}")
                print(f"Max Capacity:       {avail['max_capacity']}")
                print(f"Tickets Booked:     {avail['registered_attendees']}")
                print(f"Seats Available:    {avail['remaining_tickets']}")
                if avail["is_sold_out"]:
                    print("Status: [SOLD OUT]")
                else:
                    print("Status: [OPEN FOR REGISTRATION]")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "6":
            print_header("SEARCH / VERIFY TICKET")
            t_id = input("Enter ticket ID: ").strip()
            try:
                t = service.get_ticket_details(t_id)
                print_ticket_pass(t)
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "7":
            print_header("SCHEDULED EVENTS")
            events = service.list_events()
            if not events:
                print("No events found.")
            else:
                print(f"{'Code':<12} {'Event Title':<22} {'Date':<12} {'Price':>8} {'Cap':>6} {'Booked':>7} {'Avail':>7}")
                print("-" * 80)
                for ev in events:
                    print(f"{ev['event_code']:<12} {ev['title'][:21]:<22} {ev['event_date']:<12} ${ev['ticket_price']:>7.2f} {ev['max_capacity']:>6} {ev['tickets_booked']:>7} {ev['remaining']:>7}")

        elif choice == "8":
            print_header("REGISTRATION & REVENUE REPORT")
            code = input("Enter event code (or press Enter for all events): ").strip()
            try:
                reports = service.generate_report(code or None)
                if not reports:
                    print("No event reports found.")
                else:
                    for rep in reports:
                        print(f"\n--- Financial & Attendance Report: {rep['title']} ({rep['event_code']}) ---")
                        print(f"Event Date:          {rep['event_date']}")
                        print(f"Venue Capacity:      {rep['max_capacity']} attendees")
                        print(f"Tickets Issued:      {rep['tickets_issued']} ({rep['occupancy_rate']}% booked)")
                        print(f"Remaining Capacity:  {rep['remaining_capacity']}")
                        print(f"Paid Tickets:        {rep['paid_tickets']}")
                        print(f"Total Revenue:      ${rep['total_revenue']:,.2f}")
                        print(f"Actual Check-Ins:    {rep['checked_in_count']} ({rep['turnout_rate']}% turnout)")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "9":
            print("\nExiting Event Registration and Ticketing System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()
