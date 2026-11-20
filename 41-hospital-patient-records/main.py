"""
Interactive Command-Line Interface for Hospital Patient Records Management System.
"""
import sys
from datetime import datetime
from hospital_service import HospitalService
from security import AccessDeniedError, mask_phone, mask_email


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: HospitalService):
    """Seed system with realistic fictional healthcare data."""
    try:
        # Create administrative account directly (bootstrap context)
        admin_ctx = None
        service.register_user(
            admin_ctx, "ADM-001", "admin", "AdminPass123!", "Hospital Super Admin",
            "admin@stmarys-clinic.org", "admin", "Administration"
        )
        admin_user = service.authenticate_user("admin", "AdminPass123!")

        # Create staff accounts
        service.register_user(
            admin_user, "DOC-101", "dr.chidi", "DoctorPass123!", "Dr. Chidi Okafor, MD",
            "chidi.okafor@stmarys-clinic.org", "doctor", "Cardiology"
        )
        service.register_user(
            admin_user, "DOC-102", "dr.aisha", "DoctorPass123!", "Dr. Aisha Bello, MD",
            "aisha.bello@stmarys-clinic.org", "doctor", "General Medicine"
        )
        service.register_user(
            admin_user, "NUR-201", "nurse.amaka", "NursePass123!", "Nurse Amaka Okonkwo, RN",
            "amaka.o@stmarys-clinic.org", "nurse", "Outpatient Triage"
        )
        service.register_user(
            admin_user, "REC-301", "rec.fatima", "RecepPass123!", "Fatima Aliyu",
            "fatima.aliyu@stmarys-clinic.org", "receptionist", "Front Desk"
        )
        service.register_user(
            admin_user, "BIL-401", "bill.emeka", "BillingPass123!", "Emeka Eze",
            "emeka.eze@stmarys-clinic.org", "billing", "Accounts & Invoicing"
        )

        rec_user = service.authenticate_user("rec.fatima", "RecepPass123!")

        # Register fictional patients
        p1_id = service.register_patient(
            rec_user, "Ibrahim", "Danladi", "1985-04-12", "M", "O+",
            "+2348031234567", "ibrahim.d@example.ng", "14 Crescent Way, Victoria Island, Lagos",
            "Zainab Danladi", "+2348039876543", "Penicillin", "Hypertension"
        )

        p2_id = service.register_patient(
            rec_user, "Ngozi", "Adeleke", "1992-09-24", "F", "B+",
            "+2348025550192", "ngozi.ade@example.ng", "8 Palm Grove Avenue, Ikeja, Lagos",
            "Olu Adeleke", "+2348025550193", "None reported", "Mild Asthma"
        )

        p3_id = service.register_patient(
            rec_user, "Babatunde", "Balogun", "1978-11-03", "M", "A+",
            "+2348187770011", "babatunde.b@example.ng", "22 Marina Road, Lagos",
            "Kemi Balogun", "+2348187770022", "Sulfa drugs", "Type 2 Diabetes"
        )

        # Schedule appointments
        apt_today = datetime.now().strftime("%Y-%m-%d")
        apt1_ref = service.register_appointment(
            rec_user, p1_id, "DOC-101", "Cardiology",
            apt_today, "10:00", "Routine hypertension follow-up consultation"
        )
        apt2_ref = service.register_appointment(
            rec_user, p2_id, "DOC-102", "General Medicine",
            apt_today, "11:30", "Persistent dry cough and seasonal allergies"
        )

        # Record clinical visit encounters
        vst1_ref = service.record_visit(
            rec_user, p1_id, "Outpatient", "DOC-101", "Elevated blood pressure monitoring", apt1_ref
        )

        # Record vital signs (Nurse)
        nurse_user = service.authenticate_user("nurse.amaka", "NursePass123!")
        service.record_vital_signs(
            nurse_user, vst1_ref,
            systolic_bp=135, diastolic_bp=88, heart_rate=76,
            temperature_c=36.8, respiratory_rate=16, spo2_percent=98.5,
            weight_kg=82.5, height_cm=178.0, notes="Patient feels well, no dizziness."
        )

        # Record clinical consultation notes (Doctor)
        doc_user = service.authenticate_user("dr.chidi", "DoctorPass123!")
        service.record_clinical_note(
            doc_user, vst1_ref, "Consultation",
            subjective_observations="Patient reports adherence to low-sodium diet; complains of occasional fatigue.",
            objective_observations="BP 135/88 mmHg, HR 76 regular. Heart sounds S1, S2 normal, no murmurs. Chest clear.",
            clinical_assessment="Stage 1 primary hypertension, moderately controlled.",
            care_plan="Reinforce lifestyle modifications (aerobic exercise, dietary sodium restriction). Schedule follow-up in 6 weeks."
        )

        # Billing
        bill_user = service.authenticate_user("bill.emeka", "BillingPass123!")
        inv_ref = service.create_billing_invoice(
            bill_user, p1_id, "Cardiology Outpatient Consultation & Vital Signs Check", 25000.0, vst1_ref
        )
        service.record_payment(bill_user, inv_ref, 25000.0)

    except Exception:
        pass  # Already seeded or exists


def handle_patient_registration(service: HospitalService, user: dict):
    print_banner("Register New Patient")
    try:
        first_name = input("First Name: ").strip()
        last_name = input("Last Name: ").strip()
        dob = input("Date of Birth (YYYY-MM-DD): ").strip()
        gender = input("Gender (M / F / Other): ").strip()
        blood_group = input("Blood Group (A+, A-, B+, B-, AB+, AB-, O+, O-, Unknown): ").strip()
        phone = input("Phone Number: ").strip()
        email = input("Email (optional): ").strip()
        address = input("Residential Address: ").strip()
        emergency_name = input("Emergency Contact Name: ").strip()
        emergency_phone = input("Emergency Contact Phone: ").strip()
        allergies = input("Known Allergies (or press Enter): ").strip() or "None reported"
        chronic = input("Chronic Conditions (or press Enter): ").strip() or "None reported"

        pid = service.register_patient(
            user, first_name, last_name, dob, gender, blood_group,
            phone, email, address, emergency_name, emergency_phone,
            allergies, chronic
        )
        print(f"\n[SUCCESS] Patient registered successfully with Unique ID: {pid}")
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_patient_search(service: HospitalService, user: dict):
    print_banner("Search Patient Records")
    q = input("Enter search term (Patient ID, Name, Phone, or DOB): ").strip()
    try:
        results = service.search_patients(user, q)
        if not results:
            print("No matching patient records found.")
            return

        print(f"\nFound {len(results)} record(s):")
        print("-" * 85)
        print(f"{'Patient ID':<20} {'Name':<22} {'DOB':<12} {'Gender':<8} {'Blood':<7} {'Phone'}")
        print("-" * 85)
        for p in results:
            full_name = f"{p['first_name']} {p['last_name']}"
            masked_p = mask_phone(p['phone']) if user['role'] not in ('admin', 'receptionist') else p['phone']
            print(f"{p['patient_id']:<20} {full_name:<22} {p['date_of_birth']:<12} {p['gender']:<8} {p.get('blood_group','-'):<7} {masked_p}")
        print("-" * 85)

        detail_id = input("\nEnter Patient ID to view full chart (or press Enter to return): ").strip()
        if detail_id:
            show_patient_chart(service, user, detail_id)
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def show_patient_chart(service: HospitalService, user: dict, patient_id: str):
    try:
        p = service.get_patient(user, patient_id)
        print_banner(f"Patient Chart: {p['first_name']} {p['last_name']} ({p['patient_id']})")
        print(f"Date of Birth: {p['date_of_birth']}  |  Gender: {p['gender']}  |  Blood Group: {p['blood_group']}")
        print(f"Phone: {p['phone']}  |  Email: {p.get('email') or 'N/A'}")
        print(f"Address: {p.get('address') or 'N/A'}")
        print(f"Emergency Contact: {p.get('emergency_name') or 'N/A'} ({p.get('emergency_phone') or 'N/A'})")
        print(f"Allergies: {p.get('allergies')}")
        print(f"Chronic Conditions: {p.get('chronic_conditions')}")

        # Vitals History
        if p.get("vital_signs"):
            print("\n--- Recent Vital Signs ---")
            for v in p["vital_signs"][:3]:
                print(f"[{v['recorded_at']}] BP: {v['systolic_bp']}/{v['diastolic_bp']} mmHg | HR: {v['heart_rate']} bpm | Temp: {v['temperature_c']}°C | BMI: {v['bmi']} | By: {v['recorded_by_name']}")

        # Clinical Notes
        if p.get("clinical_notes"):
            print("\n--- Authorized Clinical Notes ---")
            for cn in p["clinical_notes"][:3]:
                print(f"\n[{cn['created_at']}] {cn['note_type']} by {cn['author_name']}:")
                print(f"  Subjective: {cn['subjective_observations']}")
                print(f"  Objective:  {cn['objective_observations']}")
                print(f"  Assessment: {cn['clinical_assessment']}")
                print(f"  Care Plan:  {cn['care_plan']}")

        # Appointments
        if p.get("appointments"):
            print("\n--- Appointment History ---")
            for a in p["appointments"][:5]:
                print(f"[{a['appointment_date']} {a['appointment_time']}] Ref: {a['appointment_ref']} | Dr: {a['doctor_name']} | Dept: {a['department']} | Status: {a['status']}")

    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_schedule_appointment(service: HospitalService, user: dict):
    print_banner("Schedule Patient Appointment")
    try:
        pid = input("Patient ID (e.g. PAT-20261120-XXXX): ").strip()
        doc_id = input("Doctor Staff User ID (e.g. DOC-101): ").strip()
        dept = input("Hospital Department: ").strip()
        apt_date = input("Appointment Date (YYYY-MM-DD): ").strip()
        apt_time = input("Appointment Time (HH:MM, 24-hr): ").strip()
        reason = input("Reason for Consultation: ").strip()
        notes = input("Preparation Notes (optional): ").strip() or None

        ref = service.register_appointment(user, pid, doc_id, dept, apt_date, apt_time, reason, notes)
        print(f"\n[SUCCESS] Appointment confirmed! Reference Number: {ref}")
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_record_vitals(service: HospitalService, user: dict):
    print_banner("Record Patient Vital Signs")
    try:
        vst_ref = input("Visit Reference (e.g. VST-20261120-XXXX): ").strip()
        sbp = int(input("Systolic BP (mmHg, e.g. 120): ").strip())
        dbp = int(input("Diastolic BP (mmHg, e.g. 80): ").strip())
        hr = int(input("Heart Rate (bpm, e.g. 72): ").strip())
        temp = float(input("Body Temperature (°C, e.g. 36.6): ").strip())
        rr = int(input("Respiratory Rate (breaths/min, e.g. 16): ").strip())
        spo2 = float(input("Oxygen Saturation SpO2 (%, e.g. 98.0): ").strip())
        wt = float(input("Weight (kg, e.g. 70.0): ").strip())
        ht = float(input("Height (cm, e.g. 175.0): ").strip())
        notes = input("Nurse Observations (optional): ").strip() or None

        vid = service.record_vital_signs(user, vst_ref, sbp, dbp, hr, temp, rr, spo2, wt, ht, notes)
        height_m = ht / 100.0
        bmi = round(wt / (height_m * height_m), 2)
        print(f"\n[SUCCESS] Vital signs recorded (ID: {vid})! Calculated BMI: {bmi}")
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_clinical_notes(service: HospitalService, user: dict):
    print_banner("Record Authorized Clinical Note")
    print("NOTE: System strictly avoids automated diagnosis or automated prescription.")
    print("Please record structured professional clinical documentation (SOAP format).")
    try:
        vst_ref = input("Visit Reference (e.g. VST-20261120-XXXX): ").strip()
        ntype = input("Note Type (Consultation / Progress Note / Nursing Note / Discharge Summary): ").strip()
        subj = input("Subjective (Symptoms reported by patient): ").strip()
        obj = input("Objective (Physical examination & clinical findings): ").strip()
        assess = input("Clinical Assessment (Physician diagnostic impression): ").strip()
        plan = input("Care & Management Plan (Non-prescriptive follow-up, lifestyle, referrals): ").strip()

        cid = service.record_clinical_note(user, vst_ref, ntype, subj, obj, assess, plan)
        print(f"\n[SUCCESS] Clinical note saved securely (Record #{cid}).")
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_reports(service: HospitalService, user: dict):
    print_banner("Hospital Administrative & Analytics Reports")
    try:
        rep = service.generate_administrative_reports(user)
        print(f"\nTotal Registered Patients: {rep['total_patients']}")

        print("\n--- Appointments by Department ---")
        for d in rep["appointments_by_department"]:
            print(f"  {d['department']:<25}: {d['count']} appointments")

        print("\n--- Appointments by Status ---")
        for s in rep["appointments_by_status"]:
            print(f"  {s['status']:<20}: {s['count']}")

        print("\n--- Physician Consultation Workload ---")
        for doc in rep["doctor_workload"]:
            print(f"  {doc['doctor_name']} ({doc.get('department','General')}): {doc['total_appointments']} consultations")

        print("\n--- Patient Visits Breakdown ---")
        for v in rep["visits_by_type"]:
            print(f"  {v['visit_type']:<20}: {v['count']} visits")

        b = rep["billing_summary"]
        print("\n--- Financial Invoicing Summary ---")
        print(f"  Total Invoices Created : {b['total_invoices']}")
        print(f"  Total Billed           : ₦{b['total_billed']:,.2f}")
        print(f"  Total Collected        : ₦{b['total_collected']:,.2f}")
        print(f"  Outstanding Balance    : ₦{b['outstanding_balance']:,.2f}")

    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def handle_audit_logs(service: HospitalService, user: dict):
    print_banner("System Security & Access Audit Trail")
    try:
        logs = service.get_audit_trail(user, limit=25)
        print("-" * 80)
        print(f"{'Timestamp':<20} {'User':<12} {'Action':<8} {'Resource':<14} {'Target':<14}")
        print("-" * 80)
        for log in logs:
            print(f"{log['timestamp']:<20} {log['username']:<12} {log['action']:<8} {log['resource_type']:<14} {log['resource_id']:<14}")
            if log.get("details"):
                print(f"  Details: {log['details']}")
        print("-" * 80)
    except (ValueError, AccessDeniedError) as e:
        print(f"\n[ERROR] {e}")


def main():
    service = HospitalService()
    seed_demo_data(service)

    current_user = None

    while True:
        if not current_user:
            print_banner("Hospital Patient Records Management System")
            print("1. Login")
            print("2. Demo Accounts Information")
            print("3. Exit")
            choice = input("\nSelect option (1-3): ").strip()

            if choice == "1":
                uname = input("Username: ").strip()
                pwd = input("Password: ").strip()
                try:
                    current_user = service.authenticate_user(uname, pwd)
                    print(f"\n[SUCCESS] Welcome, {current_user['full_name']} (Role: {current_user['role'].upper()})")
                except ValueError as e:
                    print(f"\n[ERROR] {e}")
            elif choice == "2":
                print("\nDemo Accounts:")
                print("  Admin:        admin / AdminPass123!")
                print("  Doctor:       dr.chidi / DoctorPass123!")
                print("  Nurse:        nurse.amaka / NursePass123!")
                print("  Receptionist: rec.fatima / RecepPass123!")
                print("  Billing:      bill.emeka / BillingPass123!")
            elif choice == "3":
                print("Goodbye.")
                sys.exit(0)
        else:
            role = current_user["role"]
            print_banner(f"Main Menu - Logged in as {current_user['full_name']} [{role.upper()}]")
            print("1. Search Patient Records / View Patient Chart")
            print("2. Register New Patient")
            print("3. Schedule Patient Appointment")
            print("4. Check-in Patient / Record Visit Date")
            print("5. Record Patient Vital Signs & Calculate BMI")
            print("6. Record Authorized Clinical Consultation Notes")
            print("7. View Administrative & Workload Reports")
            print("8. View Security Audit Trail (Admin only)")
            print("9. Logout")

            choice = input("\nSelect option (1-9): ").strip()
            if choice == "1":
                handle_patient_search(service, current_user)
            elif choice == "2":
                handle_patient_registration(service, current_user)
            elif choice == "3":
                handle_schedule_appointment(service, current_user)
            elif choice == "4":
                print_banner("Record Patient Visit Encounter")
                try:
                    pid = input("Patient ID: ").strip()
                    vtype = input("Visit Type (Outpatient/Inpatient/Emergency/Follow-up): ").strip()
                    staff = input("Attending Staff User ID (e.g. DOC-101): ").strip()
                    complaint = input("Chief Complaint: ").strip()
                    aref = input("Appointment Ref (or Enter if walk-in): ").strip() or None
                    vref = service.record_visit(current_user, pid, vtype, staff, complaint, aref)
                    print(f"\n[SUCCESS] Patient encounter recorded with Visit Ref: {vref}")
                except (ValueError, AccessDeniedError) as e:
                    print(f"\n[ERROR] {e}")
            elif choice == "5":
                handle_record_vitals(service, current_user)
            elif choice == "6":
                handle_clinical_notes(service, current_user)
            elif choice == "7":
                handle_reports(service, current_user)
            elif choice == "8":
                handle_audit_logs(service, current_user)
            elif choice == "9":
                print(f"\nLogged out successfully.")
                current_user = None


if __name__ == "__main__":
    main()
