"""
Queue Management System - CLI Interface
Provides an interactive command-line interface for reception kiosks, counter officers, and queue displays.
"""

import sys
from database import initialize_database, DEFAULT_DB_FILE
from queue_manager import QueueManager


def format_duration(seconds):
    """Formats seconds into human-readable minutes and seconds string."""
    if seconds is None:
        return "-"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}m {secs}s" if mins > 0 else f"{secs}s"


def display_menu():
    """Displays the interactive CLI navigation menu."""
    print("\n" + "=" * 56)
    print("      BANK & SERVICE CENTRE QUEUE SYSTEM (CLI)     ")
    print("=" * 56)
    print(" 1. Issue Queue Ticket (Register Customer)")
    print(" 2. Call Next Customer to Service Counter")
    print(" 3. View Currently Serving Desks")
    print(" 4. Mark Customer Service as Completed")
    print(" 5. View Live Waiting Queue Board")
    print(" 6. Cancel Queue Ticket")
    print(" 7. View Completed Services History")
    print(" 8. View Average Waiting Time & Queue Analytics")
    print(" 9. View Service Categories & Counters")
    print(" 10. Exit System")
    print("=" * 56)


def handle_issue_ticket(manager):
    """Registers customer and issues a queue ticket."""
    print("\n--- [Issue New Queue Ticket] ---")
    name = input("Enter customer full name: ").strip()
    phone = input("Enter phone number (optional): ").strip()

    categories = manager.list_categories()
    print("\nSelect Service Category:")
    for idx, cat in enumerate(categories, start=1):
        print(f"  {idx}. [{cat['code']}] {cat['name']} - {cat['description']}")

    choice = input(f"Select category (1-{len(categories)}): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(categories)):
        print("[Error] Invalid category selection.")
        return

    cat_code = categories[int(choice) - 1]["code"]
    notes = input("Enter inquiry notes (optional): ").strip()

    ticket = manager.register_and_enqueue_customer(
        customer_name=name,
        category_code=cat_code,
        customer_phone=phone if phone else None,
        notes=notes if notes else None
    )

    print("\n" + "*" * 48)
    print("               QUEUE TICKET ISSUED")
    print("*" * 48)
    print(f" Ticket Number:    {ticket['ticket_number']}")
    print(f" Customer Name:    {ticket['customer_name']}")
    print(f" Service Category: [{ticket['category_code']}] {ticket['category_name']}")
    print(f" Position in Line: #{ticket['queue_position']}")
    print(f" Issued At:        {ticket['created_at']}")
    print("*" * 48)
    print(" Please take a seat. Your ticket will be called shortly.")


def handle_call_next(manager):
    """Calls next customer from queue to an available counter."""
    print("\n--- [Call Next Customer] ---")
    counters = manager.list_counters()
    print("Available Service Counters:")
    for c in counters:
        busy_status = f"(Serving: {c['ticket_number']})" if c['current_ticket_id'] else "[FREE / READY]"
        print(f"  Counter #{c['counter_id']}: {c['officer_name']} {busy_status}")

    counter_input = input("Enter your Counter # to call customer: ").strip()
    if not counter_input.isdigit():
        print("[Error] Counter number must be numeric.")
        return

    counter_id = int(counter_input)

    print("\nCall options:")
    print("  1. Call Next in Unified Queue (FIFO)")
    print("  2. Call by Specific Service Category")
    opt = input("Select option (1/2) [default: 1]: ").strip()

    category_code = None
    if opt == "2":
        categories = manager.list_categories()
        for idx, cat in enumerate(categories, start=1):
            print(f"  {idx}. [{cat['code']}] {cat['name']}")
        c_choice = input(f"Choose category (1-{len(categories)}): ").strip()
        if c_choice.isdigit() and 1 <= int(c_choice) <= len(categories):
            category_code = categories[int(c_choice) - 1]["code"]

    ticket = manager.call_next_customer(counter_id, category_code)

    print("\n" + "=" * 54)
    print("                 NOW CALLING...")
    print("=" * 54)
    print(f" TICKET NUMBER:    {ticket['ticket_number']}")
    print(f" CUSTOMER:         {ticket['customer_name']}")
    print(f" SERVICE:          {ticket['category_name']}")
    print(f" PROCEED TO:       Counter #{ticket['counter_id']} ({ticket['officer_name']})")
    print(f" Customer Waited:  {format_duration(ticket['wait_time_seconds'])}")
    print("=" * 54)


def handle_view_serving(manager):
    """Displays all desks currently serving customers."""
    print("\n--- [Live Service Counters Status] ---")
    serving_list = manager.get_currently_serving()

    if not serving_list:
        print("\nNo customers are currently being served at any counter.")
        return

    print("\n" + "=" * 80)
    print(f"{'Counter':<10} | {'Ticket':<10} | {'Customer Name':<20} | {'Service':<20} | {'Duration'}")
    print("-" * 80)
    for s in serving_list:
        c_str = f"Counter #{s['counter_id']}"
        dur_str = format_duration(s.get("elapsed_service_seconds", 0))
        print(f"{c_str:<10} | {s['ticket_number']:<10} | {s['customer_name']:<20} | {s['category_name']:<20} | {dur_str}")
    print("=" * 80)


def handle_complete_service(manager):
    """Marks an active service as completed."""
    print("\n--- [Mark Service as Completed] ---")
    counters = manager.list_counters()
    active_counters = [c for c in counters if c["current_ticket_id"]]

    if not active_counters:
        print("\nNo service desks currently have active customers.")
        return

    print("Desks currently serving:")
    for c in active_counters:
        print(f"  Counter #{c['counter_id']}: Serving Ticket {c['ticket_number']} ({c['customer_name']})")

    cid_str = input("\nEnter Counter # to complete service (or Ticket Number): ").strip()
    if not cid_str:
        return

    if cid_str.isdigit() and int(cid_str) in [c["counter_id"] for c in active_counters]:
        ticket = manager.mark_as_served(counter_id=int(cid_str))
    else:
        ticket = manager.mark_as_served(ticket_number_or_id=cid_str)

    print("\n" + "=" * 52)
    print("               SERVICE COMPLETED")
    print("=" * 52)
    print(f" Ticket Number:    {ticket['ticket_number']}")
    print(f" Customer:         {ticket['customer_name']}")
    print(f" Wait Duration:    {format_duration(ticket['wait_time_seconds'])}")
    print(f" Service Duration: {format_duration(ticket['service_time_seconds'])}")
    print(f" Counter Status:   Counter #{ticket['counter_id']} is now FREE for next customer.")
    print("=" * 52)


def handle_view_waiting_queue(manager):
    """Displays live queue board."""
    print("\n--- [Live Waiting Queue Board] ---")
    waiting = manager.get_waiting_customers()

    if not waiting:
        print("\nQueue is currently empty! No waiting customers.")
        return

    print(f"\nTotal Customers in Queue: {len(waiting)}")
    print("=" * 76)
    print(f"{'Position':<9} | {'Ticket':<10} | {'Customer Name':<22} | {'Category':<18} | {'Waiting'}")
    print("-" * 76)

    for idx, t in enumerate(waiting, start=1):
        wait_str = format_duration(t.get("elapsed_wait_seconds", 0))
        print(f"#{idx:<8} | {t['ticket_number']:<10} | {t['customer_name']:<22} | {t['category_name']:<18} | {wait_str}")
    print("=" * 76)


def handle_cancel_ticket(manager):
    """Cancels a waiting or serving ticket."""
    print("\n--- [Cancel Queue Ticket] ---")
    ticket_input = input("Enter Ticket Number (e.g. TX-101) or Ticket ID: ").strip()
    if not ticket_input:
        return

    reason = input("Enter reason for cancellation [Customer no-show/left]: ").strip()
    if not reason:
        reason = "Customer no-show / left"

    ticket = manager.cancel_ticket(ticket_input, reason)
    print(f"\n✓ Ticket '{ticket['ticket_number']}' for customer '{ticket['customer_name']}' has been CANCELLED.")


def handle_view_completed(manager):
    """Displays history of completed tickets."""
    print("\n--- [Completed Service History] ---")
    completed = manager.get_completed_services(limit=25)

    if not completed:
        print("\nNo completed services logged yet.")
        return

    print("\n" + "=" * 85)
    print(f"{'Ticket':<10} | {'Customer Name':<20} | {'Category':<18} | {'Waited':<10} | {'Service':<10} | {'Completed'}")
    print("-" * 85)

    for c in completed:
        wait_str = format_duration(c.get("wait_time_seconds", 0))
        serv_str = format_duration(c.get("service_time_seconds", 0))
        time_str = c.get("completed_at", "-")[-8:] if c.get("completed_at") else "-"
        print(f"{c['ticket_number']:<10} | {c['customer_name']:<20} | {c['category_name']:<18} | {wait_str:<10} | {serv_str:<10} | {time_str}")
    print("=" * 85)


def handle_view_analytics(manager):
    """Displays average waiting time and queue metrics."""
    print("\n--- [Queue Analytics & Waiting Time Report] ---")
    overall = manager.calculate_average_waiting_time()

    print("\n" + "=" * 54)
    print("             OVERALL QUEUE PERFORMANCE")
    print("=" * 54)
    print(f" Total Customers Served:     {overall['served_count']:>14}")
    print(f" Average Waiting Time:       {format_duration(int(overall['avg_wait_seconds'])):>14} ({overall['avg_wait_minutes']:.1f} mins)")
    print(f" Average Service Duration:   {format_duration(int(overall['avg_service_seconds'])):>14} ({overall['avg_service_minutes']:.1f} mins)")
    print("=" * 54)

    categories = manager.list_categories()
    print("\n--- Breakdown by Service Category ---")
    print(f"{'Category Code':<15} | {'Served':<8} | {'Avg Wait Time':<16} | {'Avg Service Time'}")
    print("-" * 65)

    for cat in categories:
        cat_stats = manager.calculate_average_waiting_time(cat["code"])
        wait_str = format_duration(int(cat_stats["avg_wait_seconds"]))
        serv_str = format_duration(int(cat_stats["avg_service_seconds"]))
        print(f"[{cat['code']}] {cat['name'][:18]:<12} | {cat_stats['served_count']:>6} | {wait_str:>14} | {serv_str:>16}")
    print("=" * 65)


def handle_view_categories_and_counters(manager):
    """Displays available categories and service desks."""
    print("\n" + "=" * 60)
    print("             SERVICE CATEGORIES CATALOG")
    print("=" * 60)
    for cat in manager.list_categories():
        print(f" [{cat['code']}] {cat['name']}")
        print(f"     Description: {cat['description']}")
    print("-" * 60)
    print(" ACTIVE SERVICE DESKS:")
    for c in manager.list_counters():
        busy = f"[Serving #{c['ticket_number']}]" if c['current_ticket_id'] else "[AVAILABLE]"
        print(f"  Counter #{c['counter_id']}: {c['officer_name']} - {busy}")
    print("=" * 60)


def main():
    """Main application loop."""
    print("\nInitializing Bank / Service Centre Queue System...")
    initialize_database(DEFAULT_DB_FILE)
    manager = QueueManager(DEFAULT_DB_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-10): ").strip()

            if choice == "1":
                handle_issue_ticket(manager)
            elif choice == "2":
                handle_call_next(manager)
            elif choice == "3":
                handle_view_serving(manager)
            elif choice == "4":
                handle_complete_service(manager)
            elif choice == "5":
                handle_view_waiting_queue(manager)
            elif choice == "6":
                handle_cancel_ticket(manager)
            elif choice == "7":
                handle_view_completed(manager)
            elif choice == "8":
                handle_view_analytics(manager)
            elif choice == "9":
                handle_view_categories_and_counters(manager)
            elif choice == "10":
                print("\nThank you for using the Queue Management System. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 10.")

        except ValueError as err:
            print(f"\n[Operation Notice] {err}")
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
