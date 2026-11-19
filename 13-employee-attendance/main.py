#!/usr/bin/env python3
"""
Interactive Command-Line Interface for Employee Attendance Management System.
"""

import sys
from attendance_service import AttendanceService


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def main():
    service = AttendanceService()

    while True:
        print("\n" + "#" * 65)
        print("  EMPLOYEE ATTENDANCE MANAGEMENT SYSTEM - MAIN MENU")
        print("#" * 65)
        print(" 1. Register Employee")
        print(" 2. Record Daily Check-In")
        print(" 3. Record Daily Check-Out")
        print(" 4. Record Absence")
        print(" 5. View Late Arrivals")
        print(" 6. Search Attendance by Employee")
        print(" 7. Generate Weekly / Monthly Attendance Report")
        print(" 8. List All Registered Employees")
        print(" 9. Exit")
        print("-" * 65)

        choice = input("Enter choice (1-9): ").strip()

        if choice == "1":
            print_header("REGISTER EMPLOYEE")
            code = input("Enter employee code (e.g. EMP-001): ").strip()
            name = input("Enter full name: ").strip()
            dept = input("Enter department (e.g. Engineering, Sales, HR): ").strip()
            pos = input("Enter position / title: ").strip()
            shift = input("Enter shift start time (HH:MM, default 09:00): ").strip() or "09:00"
            try:
                emp = service.register_employee(code, name, dept, pos, shift)
                print(f"\n[Success] Employee '{emp['name']}' ({emp['emp_code']}) registered! Shift: {emp['shift_start_time']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "2":
            print_header("RECORD CHECK-IN")
            code = input("Enter employee code: ").strip()
            att_date = input("Enter date (YYYY-MM-DD or Enter for today): ").strip()
            check_in_time = input("Enter check-in time (HH:MM or Enter for current time): ").strip()
            notes = input("Enter notes (optional): ").strip()
            try:
                record = service.record_check_in(code, check_in_time or None, att_date or None, notes)
                late_msg = f" [LATE by {record['minutes_late']} minutes!]" if record['is_late'] else " [On-Time]"
                print(f"\n[Success] Check-in logged for {record['name']} at {record['check_in_time']}{late_msg}")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "3":
            print_header("RECORD CHECK-OUT")
            code = input("Enter employee code: ").strip()
            att_date = input("Enter date (YYYY-MM-DD or Enter for today): ").strip()
            check_out_time = input("Enter check-out time (HH:MM or Enter for current time): ").strip()
            try:
                record = service.record_check_out(code, check_out_time or None, att_date or None)
                print(f"\n[Success] Check-out logged for {record['name']} at {record['check_out_time']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "4":
            print_header("RECORD ABSENCE")
            code = input("Enter employee code: ").strip()
            att_date = input("Enter absence date (YYYY-MM-DD): ").strip()
            reason = input("Enter reason for absence: ").strip()
            try:
                record = service.record_absence(code, att_date, reason)
                print(f"\n[Success] Absence recorded for {record['name']} on {record['attendance_date']}.")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "5":
            print_header("LATE ARRIVALS REPORT")
            d_filter = input("Enter date filter (YYYY-MM-DD or Enter for all): ").strip()
            lates = service.get_late_arrivals(d_filter or None)
            if not lates:
                print("No late arrivals recorded.")
            else:
                print(f"{'Date':<12} {'Code':<9} {'Name':<18} {'Dept':<14} {'Shift':<7} {'In':<10} {'Late (Mins)':>11}")
                print("-" * 85)
                for l in lates:
                    print(f"{l['attendance_date']:<12} {l['emp_code']:<9} {l['name'][:17]:<18} {l['department'][:13]:<14} {l['shift_start_time']:<7} {l['check_in_time']:<10} {l['minutes_late']:>11}")

        elif choice == "6":
            print_header("SEARCH ATTENDANCE BY EMPLOYEE")
            code = input("Enter employee code: ").strip()
            history = service.get_employee_history(code)
            if not history:
                print(f"No records found for employee '{code}'.")
            else:
                emp_name = history[0]["name"]
                print(f"\nAttendance History for {emp_name} ({code.upper()}):")
                print(f"{'Date':<12} {'Status':<10} {'Check-In':<10} {'Check-Out':<10} {'Late?':<7} {'Mins':>5} {'Notes':<18}")
                print("-" * 76)
                for h in history:
                    c_in = h['check_in_time'] or "--:--:--"
                    c_out = h['check_out_time'] or "--:--:--"
                    is_late = "Yes" if h['is_late'] else "No"
                    notes = (h['notes'] or "")[:17]
                    print(f"{h['attendance_date']:<12} {h['status']:<10} {c_in:<10} {c_out:<10} {is_late:<7} {h['minutes_late']:>5} {notes:<18}")

        elif choice == "7":
            print_header("ATTENDANCE REPORT")
            start = input("Enter start date (YYYY-MM-DD): ").strip()
            end = input("Enter end date (YYYY-MM-DD): ").strip()
            try:
                report = service.generate_attendance_report(start, end)
                print(f"\n--- Attendance Summary: {report['start_date']} to {report['end_date']} ---")
                print(f"Active Employees:            {report['total_employees']:>8}")
                print(f"Total Present Days:          {report['total_present']:>8}")
                print(f"Total Absences:              {report['total_absent']:>8}")
                print(f"Total Late Incidents:        {report['total_late_incidents']:>8}")
                print(f"Overall Attendance Rate:     {report['overall_attendance_rate']:>7.1f}%")

                if report["employee_summaries"]:
                    print("\nEmployee Breakdown:")
                    print(f"{'Code':<9} {'Name':<18} {'Dept':<14} {'Present':>8} {'Absent':>8} {'Late':>6} {'Rate':>7}")
                    print("-" * 74)
                    for e in report["employee_summaries"]:
                        print(f"{e['emp_code']:<9} {e['name'][:17]:<18} {e['department'][:13]:<14} {e['present_days']:>8} {e['absent_days']:>8} {e['late_days']:>6} {e['attendance_rate']:>6.1f}%")
            except ValueError as e:
                print(f"\n[Error] {e}")

        elif choice == "8":
            print_header("REGISTERED EMPLOYEES")
            emps = service.list_employees()
            if not emps:
                print("No employees registered.")
            else:
                print(f"{'Code':<9} {'Name':<20} {'Department':<16} {'Position':<18} {'Shift Start':<10}")
                print("-" * 75)
                for e in emps:
                    print(f"{e['emp_code']:<9} {e['name'][:19]:<20} {e['department'][:15]:<16} {e['position'][:17]:<18} {e['shift_start_time']:<10}")

        elif choice == "9":
            print("\nExiting Employee Attendance Management System. Goodbye!")
            sys.exit(0)
        else:
            print("\n[Invalid Option] Please enter a number between 1 and 9.")


if __name__ == "__main__":
    main()
