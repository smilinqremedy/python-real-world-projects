"""
Interactive Command-Line Interface for Digital Asset & Equipment Assignment Tracker.
"""
import sys
from datetime import datetime
from asset_service import AssetTrackerService, AssetAssignmentError


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: AssetTrackerService):
    try:
        e1 = service.register_employee("EMP-101", "Chukwudi Nwosu", "chukwudi.n@company.com", "Engineering", "Senior Backend Engineer")
        e2 = service.register_employee("EMP-102", "Zainab Abubakar", "zainab.a@company.com", "Product & Design", "Lead Product Designer")
        e3 = service.register_employee("EMP-103", "Oluwaseun Balogun", "seun.b@company.com", "Finance & Ops", "Financial Analyst")

        service.register_asset("AST-001", "Apple MacBook Pro 16-inch M3 Pro", "Laptop", "SN-MBP-98214", "2026-01-15", 3200000.0, "A2991", "New")
        service.register_asset("AST-002", "Lenovo ThinkPad T14 Gen 4", "Laptop", "SN-LNV-44120", "2026-02-10", 1850000.0, "21HD001", "New")
        service.register_asset("AST-003", "Dell UltraSharp 27-inch 4K Monitor", "Monitor", "SN-DLL-78019", "2026-01-20", 650000.0, "U2723QE", "New")
        service.register_asset("AST-004", "Apple iPhone 15 Pro Max 256GB", "Mobile Phone", "SN-IPH-33921", "2026-03-01", 1950000.0, "A3106", "New")
        service.register_asset("AST-005", "Cisco Meraki Go Wi-Fi 6 Router", "Networking", "SN-CSK-88102", "2026-01-05", 420000.0, "GR12", "Good")

        # Assign asset AST-001 to EMP-101
        service.assign_asset("AST-001", "EMP-101", "2026-02-01", "2026-12-31", notes="Assigned for primary software development.")
    except Exception:
        pass


def handle_register_asset(service: AssetTrackerService):
    print_banner("Register Company Asset")
    try:
        tag = input("Asset Tag (e.g. AST-006): ").strip()
        name = input("Asset Name / Model Description: ").strip()
        cat = input("Category (Laptop / Mobile Phone / Monitor / Peripheral / Furniture / Networking): ").strip()
        sn = input("Hardware Serial Number: ").strip()
        pdate = input("Purchase Date (YYYY-MM-DD): ").strip()
        cost = float(input("Purchase Cost (₦): ").strip())
        model = input("Model Number (optional): ").strip() or None
        cond = input("Initial Condition (New / Good / Fair) [New]: ").strip() or "New"

        service.register_asset(tag, name, cat, sn, pdate, cost, model, cond)
        print(f"\n[SUCCESS] Asset '{name}' registered under tag: {tag}")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_register_employee(service: AssetTrackerService):
    print_banner("Register Employee")
    try:
        eid = input("Employee ID (e.g. EMP-104): ").strip()
        name = input("Full Name: ").strip()
        email = input("Corporate Email: ").strip()
        dept = input("Department: ").strip()
        desig = input("Job Title / Designation: ").strip()

        service.register_employee(eid, name, email, dept, desig)
        print(f"\n[SUCCESS] Employee '{name}' registered successfully.")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_assign_asset(service: AssetTrackerService):
    print_banner("Assign Asset to Employee")
    try:
        tag = input("Asset Tag (e.g. AST-002): ").strip()
        eid = input("Employee ID (e.g. EMP-102): ").strip()
        adate = input("Assignment Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None
        edate = input("Expected Return Date (YYYY-MM-DD) [Optional]: ").strip() or None
        notes = input("Assignment Purpose / Notes: ").strip() or None

        asg_ref = service.assign_asset(tag, eid, adate, edate, notes)
        print(f"\n[SUCCESS] Asset successfully assigned! Assignment Reference: {asg_ref}")
    except (ValueError, AssetAssignmentError) as e:
        print(f"\n[ASSIGNMENT BLOCKED] {e}")


def handle_return_asset(service: AssetTrackerService):
    print_banner("Return Assigned Asset")
    try:
        asg_ref = input("Assignment Reference (e.g. ASG-20261120-XXXX): ").strip()
        rdate = input("Return Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None
        print("Asset Condition on Return: 1. Good  2. Fair  3. Damaged  4. Broken")
        c_choice = input("Select Condition (1-4) [1]: ").strip() or "1"
        c_map = {"1": "Good", "2": "Fair", "3": "Damaged", "4": "Broken"}
        cond = c_map.get(c_choice, "Good")
        notes = input("Inspection / Return Notes: ").strip() or None

        service.return_asset(asg_ref, rdate, cond, notes)
        print(f"\n[SUCCESS] Asset returned and checked into inventory. Current condition: {cond}")
    except (ValueError, AssetAssignmentError) as e:
        print(f"\n[ERROR] {e}")


def handle_view_asset_history(service: AssetTrackerService):
    print_banner("Asset Timeline & Assignment History")
    tag = input("Enter Asset Tag: ").strip()
    try:
        ast = service.get_asset_history(tag)
        print(f"\nAsset Tag      : {ast['asset_tag']}  [{ast['status'].upper()}]")
        print(f"Name           : {ast['name']} ({ast['category']})")
        print(f"Serial Number  : {ast['serial_number']} | Model: {ast.get('model_number') or 'N/A'}")
        print(f"Purchase Date  : {ast['purchase_date']} | Cost: ₦{ast['purchase_cost']:,.2f}")
        print(f"Condition      : {ast['current_condition']}")
        if ast.get("holder_name"):
            print(f"Current Holder : {ast['holder_name']} ({ast['holder_emp_id']}) - {ast['holder_dept']}")

        print("\n--- Assignment History ---")
        if ast["assignments"]:
            for a in ast["assignments"]:
                ret = f"Returned {a['returned_date']} ({a['condition_at_return']})" if a['returned_date'] else "ACTIVE"
                print(f"[{a['assigned_date']}] Ref: {a['assignment_ref']} | To: {a['employee_name']} ({a['department']}) | Status: {ret}")
        else:
            print("  No assignments on record.")

        print("\n--- Condition & Maintenance Log ---")
        for cl in ast["condition_logs"]:
            print(f"[{cl['timestamp'][:19]}] Action: {cl['action']} | Condition: {cl['new_condition']} | Note: {cl.get('notes') or ''}")

    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_allocation_report(service: AssetTrackerService):
    print_banner("Asset Allocation & Inventory Report")
    rep = service.generate_allocation_report()
    print(f"\nTotal Company Assets: {rep['total_assets']}")

    print("\n--- Assets by Status ---")
    for s in rep["by_status"]:
        print(f"  * {s['status']:<18}: {s['count']}")

    print("\n--- Category Breakdown ---")
    for c in rep["by_category"]:
        print(f"  * {c['category']:<18}: {c['total']} total ({c['assigned_count']} assigned)")

    print("\n--- Assigned Assets by Department ---")
    for d in rep["by_department"]:
        print(f"  * {d['department']:<22}: {d['assigned_assets']} assets")

    if rep["damaged_or_missing"]:
        print("\n--- [AUDIT ALERT] Damaged / Missing / Under Repair Equipment ---")
        for dm in rep["damaged_or_missing"]:
            print(f"  ! {dm['asset_tag']} - {dm['name']} | Status: {dm['status']} | Condition: {dm['current_condition']}")


def main():
    service = AssetTrackerService()
    seed_demo_data(service)

    while True:
        print_banner("Digital Asset & Equipment Assignment Tracker")
        print("1. Register Company Asset")
        print("2. Register Employee")
        print("3. Assign Asset to Employee")
        print("4. Return Assigned Asset")
        print("5. View Asset Timeline & History")
        print("6. Generate Allocation & Inventory Report")
        print("7. List All Assets")
        print("8. Exit")

        choice = input("\nSelect option (1-8): ").strip()
        if choice == "1":
            handle_register_asset(service)
        elif choice == "2":
            handle_register_employee(service)
        elif choice == "3":
            handle_assign_asset(service)
        elif choice == "4":
            handle_return_asset(service)
        elif choice == "5":
            handle_view_asset_history(service)
        elif choice == "6":
            handle_allocation_report(service)
        elif choice == "7":
            assets = service.list_assets()
            print(f"\n{'Tag':<10} {'Name':<32} {'Category':<14} {'Status':<14} {'Holder'}")
            print("-" * 88)
            for a in assets:
                holder = f"{a['holder_name']} ({a['holder_dept']})" if a.get('holder_name') else "Unassigned"
                print(f"{a['asset_tag']:<10} {a['name'][:30]:<32} {a['category']:<14} {a['status']:<14} {holder}")
        elif choice == "8":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
