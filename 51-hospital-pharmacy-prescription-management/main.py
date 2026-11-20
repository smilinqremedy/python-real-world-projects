"""
Interactive CLI for Hospital Pharmacy Prescription Management System.
"""
import sys
from datetime import datetime
from pharmacy_service import PharmacyService, PrescriptionError, InsufficientStockError


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: PharmacyService):
    try:
        # Doctors
        service.register_doctor("DOC-01", "Dr. Chidi Okafor", "Internal Medicine", "MDCN-49201", "+2348031112233", "chidi.okafor@hospital.org")
        service.register_doctor("DOC-02", "Dr. Aisha Bello", "Pediatrics & Family Medicine", "MDCN-51829", "+2348022223344", "aisha.bello@hospital.org")

        # Patients
        service.register_patient("PAT-101", "Ibrahim Danladi", "1988-06-14", "M", "+2348051234567", "ibrahim@example.com", "Penicillin")
        service.register_patient("PAT-102", "Grace Adeleke", "1994-03-22", "F", "+2348062345678", "grace@example.com", "None reported")

        # Medicines
        service.add_medicine("MED-001", "Amoxicillin", "Capsule", "500mg", stock_quantity=150, unit_price=120.0, reorder_level=30, manufacturer="Emzor Pharma")
        service.add_medicine("MED-002", "Paracetamol", "Tablet", "500mg", stock_quantity=500, unit_price=25.0, reorder_level=50, manufacturer="Fidson Healthcare")
        service.add_medicine("MED-003", "Metformin HCl", "Tablet", "500mg", stock_quantity=80, unit_price=85.0, reorder_level=20, manufacturer="May & Baker")
        service.add_medicine("MED-004", "Omeprazole", "Capsule", "20mg", stock_quantity=12, unit_price=150.0, reorder_level=25, manufacturer="Chi Pharmaceuticals")
        service.add_medicine("MED-005", "Artemether/Lumefantrine", "Tablet", "80/480mg", stock_quantity=60, unit_price=1800.0, reorder_level=15, manufacturer="Swiss Pharma")
        service.add_medicine("MED-006", "Ciprofloxacin", "Tablet", "500mg", stock_quantity=4, unit_price=450.0, reorder_level=10, manufacturer="Juhel Pharma")

        # Prescriptions
        rx_ref = service.create_prescription("PAT-101", "DOC-01", "Acute Bacterial Pharyngitis & Mild Fever", notes="Patient has documented penicillin allergy; avoid beta-lactams.")
        service.add_prescription_item(rx_ref, "MED-002", 20, "2 tablets three times daily", 3)
        service.add_prescription_item(rx_ref, "MED-005", 6, "1 tablet twice daily with food", 3)

        # Dispense prescription
        service.dispense_prescription(rx_ref, "Pharm. Ngozi Obi (Lead Pharmacist)", notes="Patient counselled on completing full antimalarial course.")
    except Exception:
        pass


def handle_register_patient(service: PharmacyService):
    print_banner("Register Patient")
    try:
        pid = input("Patient ID (e.g. PAT-103): ").strip()
        name = input("Full Name: ").strip()
        dob = input("Date of Birth (YYYY-MM-DD): ").strip()
        gender = input("Gender (M / F / Other): ").strip()
        phone = input("Phone Number: ").strip()
        email = input("Email (optional): ").strip() or None
        allergies = input("Known Drug Allergies (e.g. Penicillin, Sulfa) [None]: ").strip() or "None reported"

        service.register_patient(pid, name, dob, gender, phone, email, allergies)
        print(f"\n[SUCCESS] Patient '{name}' registered successfully.")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_register_doctor(service: PharmacyService):
    print_banner("Register Doctor")
    try:
        did = input("Doctor ID (e.g. DOC-03): ").strip()
        name = input("Full Name (e.g. Dr. John Doe): ").strip()
        spec = input("Medical Specialization: ").strip()
        lic = input("Medical License Number: ").strip()
        phone = input("Phone Number: ").strip()
        email = input("Email (optional): ").strip() or None

        service.register_doctor(did, name, spec, lic, phone, email)
        print(f"\n[SUCCESS] Doctor '{name}' registered.")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_medicines(service: PharmacyService):
    print_banner("Medicine Inventory Management")
    print("1. Add New Medicine")
    print("2. Restock / Update Stock Quantity")
    print("3. View Inventory & Low Stock Alerts")
    choice = input("Choice (1-3): ").strip()

    if choice == "1":
        try:
            mid = input("Medicine ID (e.g. MED-007): ").strip()
            name = input("Generic / Brand Name: ").strip()
            form = input("Dosage Form (Tablet / Syrup / Injection / Inhaler / Capsule): ").strip()
            strength = input("Strength (e.g. 500mg, 100mcg, 250mg/5ml): ").strip()
            qty = int(input("Initial Stock Quantity: ").strip())
            price = float(input("Unit Price (₦): ").strip())
            reorder = int(input("Reorder Warning Level [10]: ").strip() or "10")
            manuf = input("Manufacturer (optional): ").strip() or None

            service.add_medicine(mid, name, form, strength, qty, price, reorder, manuf)
            print(f"\n[SUCCESS] Medicine '{name} {strength}' added to pharmacy stock.")
        except ValueError as e:
            print(f"\n[ERROR] {e}")
    elif choice == "2":
        try:
            mid = input("Medicine ID: ").strip()
            delta = int(input("Units to add (positive) or remove (negative): ").strip())
            new_stock = service.update_stock(mid, delta)
            print(f"\n[SUCCESS] Stock updated. Current stock: {new_stock} units.")
        except ValueError as e:
            print(f"\n[ERROR] {e}")
    elif choice == "3":
        meds = service.list_medicines()
        print(f"\n{'ID':<10} {'Name':<24} {'Form':<10} {'Strength':<12} {'Stock':<8} {'Reorder':<8} {'Price (₦)'}")
        print("-" * 85)
        for m in meds:
            alert = " [LOW STOCK]" if m['stock_quantity'] <= m['reorder_level'] else ""
            print(f"{m['medicine_id']:<10} {m['name']:<24} {m['dosage_form']:<10} {m['strength']:<12} {m['stock_quantity']:<8} {m['reorder_level']:<8} ₦{m['unit_price']:,.2f}{alert}")


def handle_create_prescription(service: PharmacyService):
    print_banner("Create New Prescription")
    try:
        pid = input("Patient ID: ").strip()
        did = input("Doctor ID: ").strip()
        diag = input("Clinical Diagnosis: ").strip()
        notes = input("Clinical / Allergy Warning Notes (optional): ").strip() or None

        rx_ref = service.create_prescription(pid, did, diag, notes=notes)
        print(f"\n[SUCCESS] Prescription created! Reference: {rx_ref}")

        # Add initial medicines
        while True:
            add_more = input("\nAdd medication item to prescription? (y/n) [y]: ").strip().lower()
            if add_more == "n":
                break
            mid = input("Medicine ID (e.g. MED-001): ").strip()
            qty = int(input("Quantity Prescribed: ").strip())
            dosage = input("Dosage Instructions (e.g. '1 tab twice daily'): ").strip()
            days = int(input("Duration (days): ").strip())
            service.add_prescription_item(rx_ref, mid, qty, dosage, days)
            print(f"[SUCCESS] Added {qty} units of {mid} to prescription.")

    except (ValueError, PrescriptionError) as e:
        print(f"\n[ERROR] {e}")


def handle_check_availability(service: PharmacyService):
    print_banner("Check Prescription Medicine Availability")
    rx_ref = input("Enter Prescription Reference (e.g. RX-20261120-XXXX): ").strip()
    try:
        avail = service.check_prescription_availability(rx_ref)
        print(f"\nPrescription Reference : {avail['prescription_ref']}")
        print(f"Current Status         : {avail['status']}")
        print(f"Dispensing Permitted   : {'YES' if avail['can_dispense'] else 'NO (Stock Deficit or Inactive)'}")
        print(f"Total Medication Cost  : ₦{avail['total_estimated_cost']:,.2f}")

        print(f"\n{'Medicine':<24} {'Strength':<10} {'Prescribed':<12} {'In Stock':<10} {'Status'}")
        print("-" * 75)
        for it in avail["items"]:
            status_str = "AVAILABLE" if it["is_available"] else f"DEFICIT (-{it['deficit']})"
            print(f"{it['medicine_name']:<24} {it['strength']:<10} {it['prescribed_qty']:<12} {it['available_qty']:<10} {status_str}")
        print("-" * 75)
    except PrescriptionError as e:
        print(f"\n[ERROR] {e}")


def handle_dispense_prescription(service: PharmacyService):
    print_banner("Dispense Prescription")
    rx_ref = input("Enter Prescription Reference: ").strip()
    pharm = input("Dispensing Pharmacist Name: ").strip()
    notes = input("Dispensing Notes (optional): ").strip() or None

    try:
        res = service.dispense_prescription(rx_ref, pharm, notes)
        print(f"\n[SUCCESS] Medication successfully dispensed!")
        print(f"Dispense Reference : {res['dispense_ref']}")
        print(f"Prescription Ref   : {res['prescription_ref']}")
        print(f"Pharmacist         : {res['pharmacist_name']}")
        print(f"Timestamp          : {res['dispensed_at']}")
        print(f"Total Amount Billed: ₦{res['total_amount']:,.2f}")
        print("\nDispensed Items:")
        for item in res["items"]:
            print(f"  - {item['name']} ({item['medicine_id']}): {item['quantity']} units (₦{item['subtotal']:,.2f})")
    except (PrescriptionError, InsufficientStockError, ValueError) as e:
        print(f"\n[DISPENSE BLOCKED] {e}")


def handle_view_prescription(service: PharmacyService):
    print_banner("Prescription Details & Patient History")
    print("1. View Specific Prescription Reference")
    print("2. View Patient Prescription History")
    choice = input("Choice (1-2): ").strip()

    if choice == "1":
        rx_ref = input("Prescription Reference: ").strip()
        try:
            rx = service.get_prescription(rx_ref)
            print(f"\nReference      : {rx['prescription_ref']}  [{rx['status'].upper()}]")
            print(f"Patient        : {rx['patient_name']} ({rx['patient_id']}) - Allergies: {rx['patient_allergies']}")
            print(f"Doctor         : {rx['doctor_name']} ({rx['doctor_specialization']})")
            print(f"Prescribed Date: {rx['prescribed_date']}")
            print(f"Diagnosis      : {rx['diagnosis']}")
            if rx.get("notes"):
                print(f"Clinical Notes : {rx['notes']}")

            print("\nPrescribed Items:")
            for it in rx["items"]:
                print(f"  * {it['medicine_name']} {it['strength']} - Qty: {it['quantity_prescribed']} ({it['dosage_instructions']}, {it['duration_days']} days)")

            if rx.get("dispense_record"):
                d = rx["dispense_record"]
                print(f"\nDispense Info: Ref {d['dispense_ref']} by {d['pharmacist_name']} at {d['dispensed_at']} (Total: ₦{d['total_amount']:,.2f})")
        except PrescriptionError as e:
            print(f"\n[ERROR] {e}")
    elif choice == "2":
        pid = input("Patient ID: ").strip()
        try:
            history = service.get_patient_prescription_history(pid)
            if not history:
                print("No prescriptions on record for this patient.")
                return
            print(f"\nPrescription History for {pid}:")
            print(f"{'Date':<12} {'Ref':<18} {'Doctor':<22} {'Status':<12} {'Diagnosis'}")
            print("-" * 85)
            for h in history:
                print(f"{h['prescribed_date']:<12} {h['prescription_ref']:<18} {h['doctor_name']:<22} {h['status']:<12} {h['diagnosis']}")
        except ValueError as e:
            print(f"\n[ERROR] {e}")


def handle_daily_report(service: PharmacyService):
    print_banner("Daily Pharmacy Dispensing Report")
    tdate = input("Report Date (YYYY-MM-DD) [Enter for Today]: ").strip() or None
    try:
        rep = service.generate_daily_dispensing_report(tdate)
        print(f"\nReport Date         : {rep['report_date']}")
        print(f"Total Prescriptions : {rep['total_dispenses']}")
        print(f"Total Revenue       : ₦{rep['total_revenue']:,.2f}")

        if rep["items_dispensed"]:
            print("\n--- Medications Dispensed Breakdown ---")
            for item in rep["items_dispensed"]:
                print(f"  * {item['name']} ({item['strength']}): {item['total_units']} units dispensed (₦{item['total_cost']:,.2f})")

        if rep["low_stock_alerts"]:
            print("\n--- [CRITICAL ALERT] Low Stock / Reorder Needed ---")
            for a in rep["low_stock_alerts"]:
                print(f"  ! {a['name']} ({a['medicine_id']}): {a['stock_quantity']} units remaining (Reorder Level: {a['reorder_level']})")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def main():
    service = PharmacyService()
    seed_demo_data(service)

    while True:
        print_banner("Hospital Pharmacy Prescription Management System")
        print("1. Register Patient")
        print("2. Register Doctor")
        print("3. Medicine Inventory Management")
        print("4. Create New Prescription")
        print("5. Check Prescription Medicine Availability")
        print("6. Dispense Prescription & Record Dispensing")
        print("7. View Prescription Details & Patient History")
        print("8. Generate Daily Dispensing Report")
        print("9. Exit")

        choice = input("\nSelect an option (1-9): ").strip()
        if choice == "1":
            handle_register_patient(service)
        elif choice == "2":
            handle_register_doctor(service)
        elif choice == "3":
            handle_medicines(service)
        elif choice == "4":
            handle_create_prescription(service)
        elif choice == "5":
            handle_check_availability(service)
        elif choice == "6":
            handle_dispense_prescription(service)
        elif choice == "7":
            handle_view_prescription(service)
        elif choice == "8":
            handle_daily_report(service)
        elif choice == "9":
            print("Exiting application. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
