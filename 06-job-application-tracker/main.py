"""
Job Application Tracker - CLI Interface
Entry point for managing job applications, interview timelines, and conversion analytics.
"""

import sys
from datetime import datetime
from tracker import (
    load_data,
    add_application,
    update_application_status,
    update_application_details,
    search_applications_by_company,
    get_upcoming_interviews,
    calculate_application_statistics,
    find_application_by_id,
    VALID_STATUSES,
    DATA_FILE
)


def display_menu():
    """
    Displays the interactive CLI menu.
    """
    print("\n" + "=" * 54)
    print("      JOB APPLICATION TRACKING SYSTEM (CLI)       ")
    print("=" * 54)
    print(" 1. Add New Job Application")
    print(" 2. View All Applications Roster")
    print(" 3. Update Application Status (Stage)")
    print(" 4. Search Applications by Company")
    print(" 5. View Upcoming Interviews")
    print(" 6. View Application Funnel & Success Statistics")
    print(" 7. View Detailed Application Profile")
    print(" 8. Exit Application")
    print("=" * 54)


def handle_add_application(data):
    """
    Prompts user to add a new job application.
    """
    print("\n--- [Add New Job Application] ---")
    company = input("Enter company name: ").strip()
    job_title = input("Enter job title: ").strip()

    today_str = datetime.today().strftime("%Y-%m-%d")
    app_date = input(f"Enter application date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not app_date:
        app_date = today_str

    job_description = input("Enter brief job description (optional): ").strip()
    app_link = input("Enter application link / posting URL (optional): ").strip()

    print("\nInitial Status:")
    for idx, st in enumerate(VALID_STATUSES, start=1):
        print(f"  {idx}. {st}")
    status_choice = input(f"Select status (1-{len(VALID_STATUSES)}) [default: 1 (Applied)]: ").strip()

    status = "Applied"
    if status_choice.isdigit() and 1 <= int(status_choice) <= len(VALID_STATUSES):
        status = VALID_STATUSES[int(status_choice) - 1]

    inv_date = None
    if status == "Interview":
        inv_date = input("Enter scheduled interview date/time (YYYY-MM-DD or YYYY-MM-DD HH:MM): ").strip()

    notes = input("Enter initial notes / contacts (optional): ").strip()

    try:
        app = add_application(
            data,
            company=company,
            job_title=job_title,
            application_date=app_date,
            job_description=job_description,
            application_link=app_link,
            status=status,
            interview_date=inv_date,
            notes=notes,
            file_path=DATA_FILE
        )
        print(f"\n✓ Application for '{app['job_title']}' at '{app['company']}' created successfully! (ID: {app['id']})")
    except ValueError as err:
        print(f"\n[Error] {err}")


def display_applications_table(applications):
    """
    Prints a formatted tabular view of job applications.
    """
    if not applications:
        print("\nNo job applications found.")
        return

    print("\n" + "=" * 88)
    print(f"{'ID':<4} | {'Company':<20} | {'Job Title':<22} | {'Applied':<10} | {'Status':<12} | {'Interview'}")
    print("-" * 88)

    for app in applications:
        app_id = app.get("id", "-")
        comp = app.get("company", "Unknown")[:20]
        title = app.get("job_title", "Unknown")[:22]
        date_str = app.get("application_date", "-")
        status = app.get("status", "Applied")[:12]
        inv = app.get("interview_date") or "-"

        print(f"{app_id:<4} | {comp:<20} | {title:<22} | {date_str:<10} | {status:<12} | {inv}")

    print("=" * 88)


def handle_update_status(data):
    """
    Updates status for an application.
    """
    print("\n--- [Update Application Status] ---")
    if not data["applications"]:
        print("No applications recorded.")
        return

    id_str = input("Enter Application ID to update: ").strip()
    if not id_str.isdigit():
        print("[Error] Application ID must be a number.")
        return

    app = find_application_by_id(data["applications"], int(id_str))
    if not app:
        print(f"[Error] Application ID {id_str} not found.")
        return

    print(f"\nCurrent status for '{app['job_title']}' at '{app['company']}': [{app['status']}]")
    print("Choose new status:")
    for idx, st in enumerate(VALID_STATUSES, start=1):
        print(f"  {idx}. {st}")

    choice = input(f"Select status (1-{len(VALID_STATUSES)}): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(VALID_STATUSES)):
        print("[Error] Invalid status selection.")
        return

    new_status = VALID_STATUSES[int(choice) - 1]
    inv_date = None
    if new_status == "Interview":
        current_inv = app.get("interview_date") or "none"
        inv_date = input(f"Enter interview date/time (YYYY-MM-DD HH:MM) [current: {current_inv}]: ").strip()
        if not inv_date and app.get("interview_date"):
            inv_date = app["interview_date"]

    notes = input("Add/update notes (press Enter to keep existing): ").strip()

    try:
        updated = update_application_status(
            data,
            app_id=int(id_str),
            new_status=new_status,
            interview_date=inv_date if inv_date else None,
            notes=notes if notes else None,
            file_path=DATA_FILE
        )
        print(f"\n✓ Application ID {updated['id']} status updated to '{updated['status']}'!")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_search_company(data):
    """
    Searches applications by company name.
    """
    print("\n--- [Search Applications by Company] ---")
    query = input("Enter company name or keyword: ").strip()
    if not query:
        print("[Error] Search query cannot be empty.")
        return

    matches = search_applications_by_company(data["applications"], query)
    print(f"\nFound {len(matches)} matching application(s):")
    display_applications_table(matches)


def handle_upcoming_interviews(data):
    """
    Displays chronologically sorted upcoming interviews.
    """
    print("\n--- [Upcoming Job Interviews] ---")
    upcoming = get_upcoming_interviews(data["applications"])

    if not upcoming:
        print("\nNo upcoming interviews scheduled.")
        print("Tip: When a company invites you to an interview, update its status to 'Interview'!")
        return

    print(f"\nYou have {len(upcoming)} upcoming interview(s):")
    print("\n" + "=" * 80)
    print(f"{'Interview Date':<17} | {'Company':<20} | {'Job Title':<22} | {'Notes'}")
    print("-" * 80)

    for app in upcoming:
        inv = app.get("interview_date", "-")
        comp = app.get("company", "-")[:20]
        title = app.get("job_title", "-")[:22]
        note = (app.get("notes") or "-")[:20]
        print(f"{inv:<17} | {comp:<20} | {title:<22} | {note}")

    print("=" * 80)


def handle_success_statistics(data):
    """
    Calculates and displays funnel conversion and success statistics.
    """
    stats = calculate_application_statistics(data["applications"])

    print("\n" + "=" * 54)
    print("        APPLICATION SUCCESS & FUNNEL STATISTICS")
    print("=" * 54)
    print(f" Total Applications Submitted:  {stats['total_applications']:>12}")
    print(f" Active Pipeline:               {stats['active_pipeline']:>12}")
    print("-" * 54)
    print(" STAGE BREAKDOWN:")
    for st in VALID_STATUSES:
        count = stats["status_counts"].get(st, 0)
        pct = (count / stats["total_applications"] * 100) if stats["total_applications"] > 0 else 0.0
        bar = "■" * int(pct // 5)
        print(f"   {st:<14}: {count:>4} ({pct:>5.1f}%) {bar}")

    print("-" * 54)
    print(f" Interview Rate (Interview+Offer): {stats['interview_rate_pct']:>8.1f}%")
    print(f" Job Offer Rate:                   {stats['offer_rate_pct']:>8.1f}%")
    print(f" Rejection Rate:                   {stats['rejection_rate_pct']:>8.1f}%")
    print("=" * 54)


def handle_view_details(data):
    """
    Views complete details for a specific application.
    """
    print("\n--- [Application Profile Details] ---")
    id_str = input("Enter Application ID: ").strip()
    if not id_str.isdigit():
        print("[Error] Application ID must be a number.")
        return

    app = find_application_by_id(data["applications"], int(id_str))
    if not app:
        print(f"[Error] Application ID {id_str} not found.")
        return

    print("\n" + "=" * 60)
    print(f" APPLICATION PROFILE: ID #{app['id']}")
    print("=" * 60)
    print(f" Company:          {app['company']}")
    print(f" Job Title:        {app['job_title']}")
    print(f" Application Date: {app['application_date']}")
    print(f" Status:           {app['status'].upper()}")
    print(f" Interview Date:   {app.get('interview_date') or 'Not Scheduled'}")
    print(f" Posting URL:      {app.get('application_link') or 'None'}")
    print(f" Description:      {app.get('job_description') or 'None'}")
    print(f" Notes:            {app.get('notes') or 'None'}")
    print("-" * 60)
    print(f" Created:          {app.get('created_at', '-')}")
    print(f" Last Updated:     {app.get('updated_at', '-')}")
    print("=" * 60)


def main():
    """Main CLI execution loop."""
    print("\nLoading Job Application Tracker...")
    data = load_data(DATA_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-8): ").strip()

            if choice == "1":
                handle_add_application(data)
            elif choice == "2":
                display_applications_table(data["applications"])
            elif choice == "3":
                handle_update_status(data)
            elif choice == "4":
                handle_search_company(data)
            elif choice == "5":
                handle_upcoming_interviews(data)
            elif choice == "6":
                handle_success_statistics(data)
            elif choice == "7":
                handle_view_details(data)
            elif choice == "8":
                print("\nBest of luck with your job search! Goodbye.\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 8.")

        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
