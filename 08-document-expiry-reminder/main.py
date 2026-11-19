"""
Personal Document Expiry Reminder System - CLI Interface
Provides an interactive command-line interface for tracking renewal deadlines and expiration reports.
"""

import sys
from datetime import datetime
from document_manager import (
    load_data,
    register_document,
    update_document,
    delete_document,
    get_expired_documents,
    get_documents_expiring_within,
    search_documents,
    generate_expiry_report_data,
    evaluate_document_status,
    find_document_by_id,
    DEFAULT_CATEGORIES,
    DATA_FILE
)


def display_menu():
    """
    Displays the interactive CLI menu.
    """
    print("\n" + "=" * 56)
    print("   PERSONAL DOCUMENT EXPIRY REMINDER SYSTEM (CLI)   ")
    print("=" * 56)
    print(" 1. Register New Document")
    print(" 2. View All Registered Documents")
    print(" 3. View Critical Expiries (Within 7 Days)")
    print(" 4. View Upcoming Expiries (Within 30 Days)")
    print(" 5. View Already Expired Documents")
    print(" 6. Search Documents (Name, Category, Number)")
    print(" 7. Update Document Information")
    print(" 8. Generate Full Expiry Report")
    print(" 9. Delete Document Record")
    print(" 10. Exit Application")
    print("=" * 56)


def format_documents_table(documents, show_category=True):
    """
    Prints a formatted tabular view of documents with status badges and days remaining.
    """
    if not documents:
        print("\nNo documents found matching this criteria.")
        return

    print("\n" + "=" * 90)
    print(f"{'ID':<4} | {'Document Name':<22} | {'Category':<16} | {'Expiry Date':<11} | {'Days Left':<10} | {'Status'}")
    print("-" * 90)

    for d in documents:
        doc_id = d.get("id", "-")
        name = d.get("name", "Unknown")[:22]
        cat = d.get("category", "-")[:16]
        exp = d.get("expiry_date", "-")

        eval_res = evaluate_document_status(exp)
        days = eval_res["days_remaining"]
        badge = eval_res["badge"]

        days_str = f"{days}d" if days >= 0 else f"{days}d (Past)"
        print(f"{doc_id:<4} | {name:<22} | {cat:<16} | {exp:<11} | {days_str:<10} | {badge}")

    print("=" * 90)


def handle_register_document(data):
    """Handles prompt flow for registering a new document."""
    print("\n--- [Register New Document] ---")
    name = input("Enter document name (e.g., International Passport): ").strip()
    if not name:
        print("[Error] Document name cannot be empty.")
        return

    print("\nSelect Category:")
    for idx, c in enumerate(DEFAULT_CATEGORIES, start=1):
        print(f"  {idx}. {c}")
    cat_choice = input(f"Choose category (1-{len(DEFAULT_CATEGORIES)}) [default: 1]: ").strip()

    category = DEFAULT_CATEGORIES[0]
    if cat_choice.isdigit() and 1 <= int(cat_choice) <= len(DEFAULT_CATEGORIES):
        category = DEFAULT_CATEGORIES[int(cat_choice) - 1]
    elif cat_choice:
        category = cat_choice.strip().title()

    doc_num = input("Enter document / reference number (optional): ").strip()
    issue_date = input("Enter issue date (YYYY-MM-DD): ").strip()
    expiry_date = input("Enter expiry date (YYYY-MM-DD): ").strip()
    issuing_auth = input("Enter issuing authority / organization (optional): ").strip()
    notes = input("Enter notes / renewal instructions (optional): ").strip()

    try:
        doc = register_document(
            data,
            name=name,
            category=category,
            issue_date_str=issue_date,
            expiry_date_str=expiry_date,
            document_number=doc_num,
            issuing_authority=issuing_auth,
            notes=notes,
            file_path=DATA_FILE
        )
        eval_res = evaluate_document_status(doc["expiry_date"])
        print(f"\n✓ Document '{doc['name']}' successfully registered! (ID: {doc['id']})")
        print(f"  Status: {eval_res['message']} {eval_res['badge']}")
    except ValueError as err:
        print(f"\n[Validation Error] {err}")


def handle_update_document(data):
    """Handles updating document fields."""
    print("\n--- [Update Document Information] ---")
    if not data["documents"]:
        print("No documents registered.")
        return

    id_str = input("Enter Document ID to update: ").strip()
    if not id_str.isdigit():
        print("[Error] Document ID must be numeric.")
        return

    doc = find_document_by_id(data["documents"], int(id_str))
    if not doc:
        print(f"[Error] Document ID {id_str} not found.")
        return

    print(f"\nCurrent details for '{doc['name']}':")
    print(f"  Category:     {doc['category']}")
    print(f"  Doc Number:   {doc.get('document_number') or '-'}")
    print(f"  Issue Date:   {doc['issue_date']}")
    print(f"  Expiry Date:  {doc['expiry_date']}")
    print("(Press Enter to keep existing values)")

    new_name = input(f"New name [{doc['name']}]: ").strip()
    new_cat = input(f"New category [{doc['category']}]: ").strip()
    new_num = input(f"New document number [{doc.get('document_number') or '-'}]: ").strip()
    new_issue = input(f"New issue date [{doc['issue_date']}]: ").strip()
    new_expiry = input(f"New expiry date [{doc['expiry_date']}]: ").strip()
    new_notes = input("New notes: ").strip()

    try:
        updated = update_document(
            data,
            doc_id=int(id_str),
            name=new_name if new_name else None,
            category=new_cat if new_cat else None,
            issue_date_str=new_issue if new_issue else None,
            expiry_date_str=new_expiry if new_expiry else None,
            document_number=new_num if new_num else None,
            notes=new_notes if new_notes else None,
            file_path=DATA_FILE
        )
        eval_res = evaluate_document_status(updated["expiry_date"])
        print(f"\n✓ Document ID {updated['id']} updated successfully!")
        print(f"  New Status: {eval_res['message']} {eval_res['badge']}")
    except ValueError as err:
        print(f"\n[Validation Error] {err}")


def handle_delete_document(data):
    """Deletes a document record."""
    print("\n--- [Delete Document Record] ---")
    id_str = input("Enter Document ID to delete: ").strip()
    if not id_str.isdigit():
        print("[Error] Document ID must be numeric.")
        return

    confirm = input(f"Are you sure you want to permanently delete document #{id_str}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Deletion cancelled.")
        return

    try:
        deleted = delete_document(data, int(id_str), DATA_FILE)
        print(f"\n✓ Document '{deleted['name']}' (ID: #{deleted['id']}) has been deleted.")
    except ValueError as err:
        print(f"\n[Error] {err}")


def handle_view_critical_7d(data):
    """Displays documents expiring in 7 days or fewer."""
    print("\n--- [CRITICAL: Documents Expiring Within 7 Days] ---")
    critical_docs = get_documents_expiring_within(data["documents"], max_days=7)
    if not critical_docs:
        print("\n✓ No documents expiring in the next 7 days. All clear!")
        return
    print(f"\n[!] WARNING: {len(critical_docs)} document(s) require immediate renewal:")
    format_documents_table(critical_docs)


def handle_view_upcoming_30d(data):
    """Displays documents expiring in 30 days or fewer."""
    print("\n--- [Upcoming: Documents Expiring Within 30 Days] ---")
    upcoming_docs = get_documents_expiring_within(data["documents"], max_days=30)
    if not upcoming_docs:
        print("\n✓ No documents expiring in the next 30 days.")
        return
    print(f"\nFound {len(upcoming_docs)} document(s) expiring within 30 days:")
    format_documents_table(upcoming_docs)


def handle_view_expired(data):
    """Displays documents that have already expired."""
    print("\n--- [EXPIRED DOCUMENTS] ---")
    expired_docs = get_expired_documents(data["documents"])
    if not expired_docs:
        print("\n✓ Great news! None of your registered documents have expired.")
        return
    print(f"\n[!] ATTENTION: {len(expired_docs)} document(s) have already EXPIRED:")
    format_documents_table(expired_docs)


def handle_search_documents(data):
    """Searches documents by query."""
    print("\n--- [Search Documents] ---")
    query = input("Enter document name, category, or document number: ").strip()
    if not query:
        print("[Error] Search query cannot be empty.")
        return

    matches = search_documents(data["documents"], query)
    print(f"\nFound {len(matches)} matching document(s):")
    format_documents_table(matches)


def handle_generate_report(data):
    """Generates comprehensive document expiry report."""
    rep = generate_expiry_report_data(data["documents"])

    print("\n" + "=" * 60)
    print(f"        PERSONAL DOCUMENT EXPIRY AUDIT REPORT")
    print(f"        Date: {rep['report_date']}")
    print("=" * 60)
    print(f" Total Registered Documents:     {rep['total_documents']:>8}")
    print("-" * 60)
    print(f" Valid & Active (> 30 days):     {rep['counts']['valid']:>8}  [HEALTHY]")
    print(f" Expiring Soon (8 - 30 days):    {rep['counts']['expiring_30d']:>8}  [UPCOMING]")
    print(f" Critical Expiries (<= 7 days):  {rep['counts']['critical_7d']:>8}  [URGENT]")
    print(f" Already Expired:                {rep['counts']['expired']:>8}  [ACTION REQUIRED]")
    print("=" * 60)

    # Category Breakdown
    print("\n--- Category Breakdown ---")
    for cat, count in sorted(rep["category_counts"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:<30}: {count:>3} document(s)")

    # Urgent Actions Required
    urgent_items = rep["critical_7d_documents"] + rep["expired_documents"]
    if urgent_items:
        print("\n" + "!" * 60)
        print("          URGENT RENEWAL ACTION CHECKLIST")
        print("!" * 60)
        for d in urgent_items:
            tag = "EXPIRED" if d["days_remaining"] < 0 else f"Expires in {d['days_remaining']}d"
            print(f" • [ID: {d['id']:<3}] {d['name']} ({d['category']}) -> {tag} [Due: {d['expiry_date']}]")
        print("!" * 60)
    else:
        print("\n✓ No immediate renewals needed. All documents are up to date!")


def main():
    """Main CLI execution loop."""
    print("\nStarting Personal Document Expiry Reminder System...")
    data = load_data(DATA_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-10): ").strip()

            if choice == "1":
                handle_register_document(data)
            elif choice == "2":
                format_documents_table(data["documents"])
            elif choice == "3":
                handle_view_critical_7d(data)
            elif choice == "4":
                handle_view_upcoming_30d(data)
            elif choice == "5":
                handle_view_expired(data)
            elif choice == "6":
                handle_search_documents(data)
            elif choice == "7":
                handle_update_document(data)
            elif choice == "8":
                handle_generate_report(data)
            elif choice == "9":
                handle_delete_document(data)
            elif choice == "10":
                print("\nKeep your documents updated! Goodbye.\n")
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
