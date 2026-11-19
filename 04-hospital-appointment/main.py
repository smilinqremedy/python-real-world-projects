"""
Hospital Appointment Management System - CLI Interface
Provides an interactive command-line interface for clinic receptionists and doctors.
"""

import sys
from datetime import datetime
from database import initialize_database, STANDARD_TIME_SLOTS, DEFAULT_DB_FILE
from service import ClinicService
from exceptions import (
    ValidationError,
    NotFoundError,
    DoctorUnavailableError,
    PatientConflictError,
    InvalidStatusTransitionError
)


def display_menu():
    """
    Displays the interactive main menu.
    """
    print("\n" + "=" * 56)
    print("   HOSPITAL APPOINTMENT MANAGEMENT SYSTEM (CLI)   ")
    print("=" * 56)
    print(" 1. Register New Patient")
    print(" 2. Register New Doctor & Specialty")
    print(" 3. View All Doctors & Specialties")
    print(" 4. Check Doctor Availability")
    print(" 5. Schedule New Appointment")
    print(" 6. Reschedule Appointment")
    print(" 7. Cancel Appointment")
    print(" 8. Mark Appointment as Completed")
    print(" 9. Display Clinic Appointments by Date")
    print(" 10. Search Patient Appointment History")
    print(" 11. View All Registered Patients")
    print(" 12. Exit Application")
    print("=" * 56)


def handle_register_patient(service):
    """Handles patient registration."""
    print("\n--- [Register New Patient] ---")
    name = input("Enter patient full name: ").strip()
    dob = input("Enter date of birth (YYYY-MM-DD): ").strip()
    gender = input("Enter gender (Male/Female/Other): ").strip()
    phone = input("Enter contact phone number: ").strip()
    email = input("Enter email address (optional, press Enter to skip): ").strip()

    patient = service.register_patient(name, dob, gender, phone, email if email else None)
    print(f"\n✓ Patient '{patient['full_name']}' registered successfully!")
    print(f"  Assigned Unique Patient ID: {patient['patient_id']}")


def handle_register_doctor(service):
    """Handles doctor registration."""
    print("\n--- [Register New Doctor] ---")
    name = input("Enter doctor full name (e.g., Dr. Robert Lee): ").strip()
    specialty = input("Enter specialty (e.g., Cardiology, Pediatrics, General Medicine): ").strip()
    phone = input("Enter phone number (optional): ").strip()
    email = input("Enter email (optional): ").strip()

    doctor = service.register_doctor(name, specialty, phone if phone else None, email if email else None)
    print(f"\n✓ Doctor '{doctor['full_name']}' registered with ID: {doctor['doctor_id']} ({doctor['specialty']}).")


def handle_list_doctors(service):
    """Lists all active clinic doctors."""
    doctors = service.list_doctors()
    print("\n" + "=" * 70)
    print(f"{'ID':<5} | {'Doctor Name':<24} | {'Specialty':<20} | {'Phone'}")
    print("-" * 70)
    for d in doctors:
        print(f"{d['doctor_id']:<5} | {d['full_name']:<24} | {d['specialty']:<20} | {d.get('phone_number') or '-'}")
    print("=" * 70)


def handle_check_availability(service):
    """Checks and displays doctor available slots for a given date."""
    print("\n--- [Check Doctor Availability] ---")
    doc_id_str = input("Enter Doctor ID: ").strip()
    if not doc_id_str.isdigit():
        print("[Error] Doctor ID must be a numeric value.")
        return

    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter appointment date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    result = service.check_doctor_availability(int(doc_id_str), date_str)
    doc = result["doctor"]

    print("\n" + "=" * 55)
    print(f" AVAILABILITY FOR {doc['full_name'].upper()} ({doc['specialty']})")
    print(f" Date: {result['date']}")
    print("=" * 55)

    if not result["available_slots"]:
        print(" [FULLY BOOKED] No available slots remaining on this date.")
    else:
        print(f" Available Slots ({len(result['available_slots'])} free):")
        slots_str = ", ".join(result["available_slots"])
        print(f"   {slots_str}")

    if result["booked_slots"]:
        print(f"\n Already Booked ({len(result['booked_slots'])} slots):")
        print(f"   {', '.join(result['booked_slots'])}")
    print("=" * 55)


def handle_schedule_appointment(service):
    """Schedules an appointment with conflict avoidance."""
    print("\n--- [Schedule New Appointment] ---")
    patient_id = input("Enter Patient ID (e.g. PAT-2026-001): ").strip().upper()
    doc_id_str = input("Enter Doctor ID: ").strip()
    if not doc_id_str.isdigit():
        print("[Error] Doctor ID must be numeric.")
        return

    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    # Show available slots first
    avail = service.check_doctor_availability(int(doc_id_str), date_str)
    if not avail["available_slots"]:
        print(f"\n[Notice] {avail['doctor']['full_name']} is fully booked on {date_str}. Please choose another date.")
        return

    print(f"\nAvailable Slots for {avail['doctor']['full_name']}:")
    for idx, slot in enumerate(avail["available_slots"], start=1):
        print(f"  {idx}. {slot}")

    slot_choice = input("Enter time slot (e.g. 09:30) or number from list: ").strip()
    if slot_choice.isdigit() and 1 <= int(slot_choice) <= len(avail["available_slots"]):
        selected_slot = avail["available_slots"][int(slot_choice) - 1]
    else:
        selected_slot = slot_choice

    reason = input("Enter appointment reason/notes [General Consultation]: ").strip()
    if not reason:
        reason = "General Consultation"

    app = service.schedule_appointment(patient_id, int(doc_id_str), date_str, selected_slot, reason)
    print("\n" + "=" * 55)
    print("            APPOINTMENT CONFIRMATION")
    print("=" * 55)
    print(f" Appointment ID:   {app['appointment_id']}")
    print(f" Patient:          {app['patient_name']} ({app['patient_id']})")
    print(f" Doctor:           {app['doctor_name']} ({app['doctor_specialty']})")
    print(f" Date & Time:      {app['appointment_date']} at {app['time_slot']}")
    print(f" Reason:           {app['reason']}")
    print(f" Status:           {app['status'].upper()}")
    print("=" * 55)


def handle_reschedule(service):
    """Reschedules an existing appointment."""
    print("\n--- [Reschedule Appointment] ---")
    app_id_str = input("Enter Appointment ID: ").strip()
    if not app_id_str.isdigit():
        print("[Error] Appointment ID must be numeric.")
        return

    app = service.get_appointment_by_id(int(app_id_str))
    print(f"\nCurrent Appointment: ID {app['appointment_id']} | {app['patient_name']} with {app['doctor_name']}")
    print(f"Currently booked on: {app['appointment_date']} at {app['time_slot']} (Status: {app['status']})")

    new_date = input("Enter new date (YYYY-MM-DD): ").strip()
    print("Standard time slots: " + ", ".join(STANDARD_TIME_SLOTS))
    new_slot = input("Enter new time slot (HH:MM): ").strip()

    updated = service.reschedule_appointment(int(app_id_str), new_date, new_slot)
    print(f"\n✓ Appointment ID {updated['appointment_id']} successfully rescheduled to {updated['appointment_date']} at {updated['time_slot']}!")


def handle_cancel_appointment(service):
    """Cancels an appointment."""
    print("\n--- [Cancel Appointment] ---")
    app_id_str = input("Enter Appointment ID to cancel: ").strip()
    if not app_id_str.isdigit():
        print("[Error] Appointment ID must be numeric.")
        return

    app = service.cancel_appointment(int(app_id_str))
    print(f"\n✓ Appointment ID {app['appointment_id']} for {app['patient_name']} has been CANCELLED.")
    print("  The time slot has been freed for other patients.")


def handle_complete_appointment(service):
    """Marks an appointment as completed."""
    print("\n--- [Complete Appointment] ---")
    app_id_str = input("Enter Appointment ID to mark completed: ").strip()
    if not app_id_str.isdigit():
        print("[Error] Appointment ID must be numeric.")
        return

    app = service.complete_appointment(int(app_id_str))
    print(f"\n✓ Appointment ID {app['appointment_id']} marked as COMPLETED.")


def handle_display_by_date(service):
    """Displays all clinic appointments for a specified date."""
    print("\n--- [Clinic Schedule by Date] ---")
    today_str = datetime.today().strftime("%Y-%m-%d")
    date_str = input(f"Enter target date (YYYY-MM-DD) [default: {today_str}]: ").strip()
    if not date_str:
        date_str = today_str

    appointments = service.get_appointments_by_date(date_str)
    print("\n" + "=" * 85)
    print(f"                  APPOINTMENTS SCHEDULE FOR {date_str}")
    print("=" * 85)
    print(f"{'ID':<5} | {'Time':<7} | {'Patient Name':<20} | {'Doctor Name':<22} | {'Specialty':<14} | {'Status'}")
    print("-" * 85)

    if not appointments:
        print("  No appointments scheduled for this date.")
    else:
        for a in appointments:
            print(f"{a['appointment_id']:<5} | {a['time_slot']:<7} | {a['patient_name']:<20} | {a['doctor_name']:<22} | {a['doctor_specialty']:<14} | {a['status'].upper()}")

    print("=" * 85)


def handle_patient_history(service):
    """Searches and displays appointment history for a patient."""
    print("\n--- [Patient Appointment History] ---")
    pat_id = input("Enter Patient ID (e.g. PAT-2026-001): ").strip().upper()
    data = service.get_patient_appointment_history(pat_id)
    patient = data["patient"]
    history = data["history"]

    print("\n" + "=" * 80)
    print(f" APPOINTMENT HISTORY FOR {patient['full_name'].upper()} ({patient['patient_id']})")
    print(f" DOB: {patient['date_of_birth']} | Phone: {patient['phone_number']}")
    print("=" * 80)
    print(f"{'App ID':<7} | {'Date':<10} | {'Time':<7} | {'Doctor':<22} | {'Specialty':<16} | {'Status'}")
    print("-" * 80)

    if not history:
        print("  No appointment history found for this patient.")
    else:
        for h in history:
            print(f"{h['appointment_id']:<7} | {h['appointment_date']:<10} | {h['time_slot']:<7} | {h['doctor_name']:<22} | {h['doctor_specialty']:<16} | {h['status'].upper()}")

    print("=" * 80)


def handle_list_patients(service):
    """Displays all registered patients."""
    patients = service.list_patients()
    print("\n" + "=" * 75)
    print(f"{'Patient ID':<14} | {'Full Name':<22} | {'DOB':<10} | {'Gender':<8} | {'Phone'}")
    print("-" * 75)
    for p in patients:
        print(f"{p['patient_id']:<14} | {p['full_name']:<22} | {p['date_of_birth']:<10} | {p['gender']:<8} | {p['phone_number']}")
    print("=" * 75)


def main():
    """Main CLI execution loop."""
    print("\nInitializing Hospital Appointment Database...")
    initialize_database(DEFAULT_DB_FILE)
    service = ClinicService(DEFAULT_DB_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-12): ").strip()

            if choice == "1":
                handle_register_patient(service)
            elif choice == "2":
                handle_register_doctor(service)
            elif choice == "3":
                handle_list_doctors(service)
            elif choice == "4":
                handle_check_availability(service)
            elif choice == "5":
                handle_schedule_appointment(service)
            elif choice == "6":
                handle_reschedule(service)
            elif choice == "7":
                handle_cancel_appointment(service)
            elif choice == "8":
                handle_complete_appointment(service)
            elif choice == "9":
                handle_display_by_date(service)
            elif choice == "10":
                handle_patient_history(service)
            elif choice == "11":
                handle_list_patients(service)
            elif choice == "12":
                print("\nExiting Hospital Appointment Management System. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 12.")

        except (ValidationError, NotFoundError, DoctorUnavailableError, PatientConflictError, InvalidStatusTransitionError) as err:
            print(f"\n[Operation Failed] {err}")
        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
