"""
Customer Complaint and Support Ticket Management System - CLI Interface
Provides an interactive command-line interface for customer service operations and complaint tracking.
"""

import sys
from database import initialize_database, CATEGORIES, PRIORITY_LEVELS, TICKET_STATUSES, DEFAULT_DB_FILE
from ticket_service import TicketService


def display_menu():
    """Displays the interactive CLI menu."""
    print("\n" + "=" * 58)
    print("   CUSTOMER COMPLAINT & SUPPORT TICKET SYSTEM (CLI)   ")
    print("=" * 58)
    print(" 1. Register New Customer")
    print(" 2. Create Support Ticket (File Complaint)")
    print(" 3. Assign Ticket to Support Agent")
    print(" 4. Update Ticket Status (Open/In Progress/Resolved/Reopened)")
    print(" 5. Display Unresolved Tickets (Priority Order)")
    print(" 6. Search Ticket by ID or Code")
    print(" 7. View All Tickets Roster")
    print(" 8. Generate Support & Resolution Reports")
    print(" 9. View Support Agents Directory")
    print(" 10. Exit Application")
    print("=" * 58)


def handle_register_customer(service):
    """Registers a new customer."""
    print("\n--- [Register New Customer] ---")
    name = input("Enter customer full name: ").strip()
    email = input("Enter customer email address: ").strip()
    phone = input("Enter phone number (optional): ").strip()
    company = input("Enter company / organization (optional): ").strip()

    try:
        cust = service.register_customer(name, email, phone if phone else None, company if company else None)
        print(f"\n✓ Customer '{cust['full_name']}' registered successfully! (Customer ID: {cust['customer_id']})")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_create_ticket(service):
    """Creates a new complaint support ticket."""
    print("\n--- [Create Support Ticket] ---")
    cust_id_str = input("Enter Customer ID: ").strip()
    if not cust_id_str.isdigit():
        print("[Error] Customer ID must be a numeric value.")
        return

    title = input("Enter ticket title / summary: ").strip()
    description = input("Enter detailed complaint description: ").strip()

    print("\nSelect Ticket Category:")
    for idx, cat in enumerate(CATEGORIES, start=1):
        print(f"  {idx}. {cat}")
    c_choice = input(f"Choose category (1-{len(CATEGORIES)}): ").strip()

    if not c_choice.isdigit() or not (1 <= int(c_choice) <= len(CATEGORIES)):
        print("[Error] Invalid category selection.")
        return
    category = CATEGORIES[int(c_choice) - 1]

    print("\nSelect Priority Level:")
    for idx, prio in enumerate(PRIORITY_LEVELS, start=1):
        print(f"  {idx}. {prio}")
    p_choice = input(f"Choose priority (1-{len(PRIORITY_LEVELS)}) [default: 2 (Medium)]: ").strip()

    priority = "Medium"
    if p_choice.isdigit() and 1 <= int(p_choice) <= len(PRIORITY_LEVELS):
        priority = PRIORITY_LEVELS[int(p_choice) - 1]

    agents = service.list_agents()
    print("\nAssign to Agent (Optional):")
    print("  0. Leave Unassigned (Open pool)")
    for a in agents:
        print(f"  {a['agent_id']}. {a['full_name']} ({a['department']})")
    a_choice = input(f"Select agent ID [default: 0]: ").strip()

    agent_id = None
    if a_choice.isdigit() and int(a_choice) in [a["agent_id"] for a in agents]:
        agent_id = int(a_choice)

    try:
        ticket = service.create_ticket(
            customer_id=int(cust_id_str),
            title=title,
            description=description,
            category=category,
            priority=priority,
            agent_id=agent_id
        )
        print("\n" + "*" * 52)
        print("           SUPPORT TICKET CREATED")
        print("*" * 52)
        print(f" Ticket Code:      {ticket['ticket_code']} (ID: #{ticket['ticket_id']})")
        print(f" Customer:         {ticket['customer_name']} ({ticket['customer_email']})")
        print(f" Title:            {ticket['title']}")
        print(f" Category:         {ticket['category']}")
        print(f" Priority:         [{ticket['priority'].upper()}]")
        print(f" Assigned Agent:   {ticket.get('agent_name') or 'Unassigned'}")
        print(f" Initial Status:   {ticket['status']}")
        print("*" * 52)
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_assign_ticket(service):
    """Assigns an open ticket to a support agent."""
    print("\n--- [Assign Ticket to Support Agent] ---")
    ticket_query = input("Enter Ticket ID or Code (e.g. TICK-2026-001): ").strip()
    if not ticket_query:
        return

    agents = service.list_agents()
    print("\nActive Support Agents:")
    for a in agents:
        print(f"  {a['agent_id']}. {a['full_name']} - {a['department']}")

    agent_id_str = input("\nEnter Agent ID to assign: ").strip()
    if not agent_id_str.isdigit():
        print("[Error] Agent ID must be numeric.")
        return

    try:
        updated = service.assign_ticket(ticket_query, int(agent_id_str))
        print(f"\n✓ Ticket {updated['ticket_code']} successfully assigned to {updated['agent_name']} ({updated['agent_department']})!")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_update_status(service):
    """Updates ticket status with business rule enforcement."""
    print("\n--- [Update Ticket Status] ---")
    ticket_query = input("Enter Ticket ID or Code: ").strip()
    if not ticket_query:
        return

    try:
        ticket = service.find_ticket(ticket_query)
        print(f"\nCurrent Ticket: {ticket['ticket_code']} | Title: '{ticket['title']}'")
        print(f"Current Status: [{ticket['status']}] | Assigned Agent: {ticket.get('agent_name') or 'UNASSIGNED'}")

        print("\nAvailable Status Transitions:")
        for idx, st in enumerate(TICKET_STATUSES, start=1):
            print(f"  {idx}. {st}")

        choice = input(f"Choose status (1-{len(TICKET_STATUSES)}): ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(TICKET_STATUSES)):
            print("[Error] Invalid status choice.")
            return

        new_status = TICKET_STATUSES[int(choice) - 1]
        resolution_notes = None
        if new_status == "Resolved":
            resolution_notes = input("Enter resolution summary / root-cause notes: ").strip()

        updated = service.update_ticket_status(ticket_query, new_status, resolution_notes)
        print(f"\n✓ Ticket {updated['ticket_code']} status transitioned to [{updated['status'].upper()}]!")
    except ValueError as err:
        print(f"\n[Operation Failed] {err}")


def handle_unresolved_by_priority(service):
    """Displays unresolved tickets sorted by priority."""
    print("\n--- [Unresolved Tickets by Priority] ---")
    tickets = service.get_unresolved_tickets_by_priority()

    if not tickets:
        print("\n✓ Great job! There are currently no unresolved tickets.")
        return

    print(f"\nTotal Unresolved Tickets: {len(tickets)}")
    print("=" * 95)
    print(f"{'Code':<14} | {'Priority':<9} | {'Status':<12} | {'Category':<18} | {'Customer':<18} | {'Agent'}")
    print("-" * 95)

    for t in tickets:
        prio_badge = f"[{t['priority'].upper()}]"
        agent = t.get("agent_name") or "[UNASSIGNED]"
        print(f"{t['ticket_code']:<14} | {prio_badge:<9} | {t['status']:<12} | {t['category'][:18]:<18} | {t['customer_name'][:18]:<18} | {agent}")

    print("=" * 95)


def handle_search_ticket(service):
    """Searches and displays full ticket profile."""
    print("\n--- [Search Ticket by ID or Code] ---")
    query = input("Enter Ticket ID (e.g. 1) or Code (e.g. TICK-2026-001): ").strip()
    if not query:
        return

    try:
        t = service.find_ticket(query)
        print("\n" + "=" * 65)
        print(f" TICKET PROFILE: {t['ticket_code']} (ID #{t['ticket_id']})")
        print("=" * 65)
        print(f" Title:             {t['title']}")
        print(f" Customer:          {t['customer_name']} ({t['customer_email']})")
        print(f" Category:          {t['category']}")
        print(f" Priority:          [{t['priority'].upper()}]")
        print(f" Status:            [{t['status'].upper()}]")
        print(f" Assigned Agent:    {t.get('agent_name') or 'UNASSIGNED'}")
        print(f" Created At:        {t['created_at']}")
        print(f" Last Updated:      {t['updated_at']}")
        if t.get("resolved_at"):
            print(f" Resolved At:       {t['resolved_at']}")
        print("-" * 65)
        print(f" Description:")
        print(f"   {t['description']}")
        if t.get("resolution_notes"):
            print("-" * 65)
            print(f" Resolution Notes:")
            print(f"   {t['resolution_notes']}")
        print("=" * 65)
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_view_all_tickets(service):
    """Displays all tickets roster."""
    print("\n--- [All Tickets Roster] ---")
    tickets = service.list_all_tickets()

    if not tickets:
        print("\nNo tickets recorded in the system.")
        return

    print("\n" + "=" * 95)
    print(f"{'Code':<14} | {'Priority':<9} | {'Status':<12} | {'Category':<18} | {'Title':<20} | {'Agent'}")
    print("-" * 95)
    for t in tickets:
        agent = t.get("agent_name") or "[Unassigned]"
        print(f"{t['ticket_code']:<14} | {t['priority']:<9} | {t['status']:<12} | {t['category'][:18]:<18} | {t['title'][:20]:<20} | {agent}")
    print("=" * 95)


def handle_generate_reports(service):
    """Displays aggregated ticket resolution reports."""
    rep = service.generate_ticket_reports()

    print("\n" + "=" * 58)
    print("         CUSTOMER SUPPORT & RESOLUTION REPORT")
    print("=" * 58)
    print(f" Total Tickets Created:        {rep['total_tickets']:>12}")
    print(f" Resolved Tickets:             {rep['resolved_count']:>12}")
    print(f" Unresolved / In-Flight:       {rep['unresolved_count']:>12}")
    print(f" Resolution Rate:              {rep['resolution_rate_pct']:>11.1f}%")
    print("-" * 58)
    print(" STATUS BREAKDOWN:")
    for st in TICKET_STATUSES:
        count = rep["status_breakdown"].get(st, 0)
        pct = (count / rep["total_tickets"] * 100) if rep["total_tickets"] > 0 else 0.0
        bar = "■" * int(pct // 5)
        print(f"   {st:<16}: {count:>4} ({pct:>5.1f}%) {bar}")

    print("-" * 58)
    print(" PRIORITY BREAKDOWN:")
    for prio in PRIORITY_LEVELS:
        count = rep["priority_breakdown"].get(prio, 0)
        pct = (count / rep["total_tickets"] * 100) if rep["total_tickets"] > 0 else 0.0
        bar = "■" * int(pct // 5)
        print(f"   {prio:<16}: {count:>4} ({pct:>5.1f}%) {bar}")

    print("-" * 58)
    print(" CATEGORY BREAKDOWN:")
    for cat, count in sorted(rep["category_breakdown"].items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat:<28}: {count:>3} tickets")
    print("=" * 58)


def handle_view_agents(service):
    """Displays agent directory."""
    print("\n" + "=" * 60)
    print("            SUPPORT AGENTS DIRECTORY")
    print("=" * 60)
    for a in service.list_agents():
        print(f" ID #{a['agent_id']:<2} | {a['full_name']:<20} | {a['department']:<22} | {a['email']}")
    print("=" * 60)


def main():
    """Main application loop."""
    print("\nInitializing Customer Support Ticket System Database...")
    initialize_database(DEFAULT_DB_FILE)
    service = TicketService(DEFAULT_DB_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-10): ").strip()

            if choice == "1":
                handle_register_customer(service)
            elif choice == "2":
                handle_create_ticket(service)
            elif choice == "3":
                handle_assign_ticket(service)
            elif choice == "4":
                handle_update_status(service)
            elif choice == "5":
                handle_unresolved_by_priority(service)
            elif choice == "6":
                handle_search_ticket(service)
            elif choice == "7":
                handle_view_all_tickets(service)
            elif choice == "8":
                handle_generate_reports(service)
            elif choice == "9":
                handle_view_agents(service)
            elif choice == "10":
                print("\nThank you for delivering excellent customer support. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 10.")

        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
