"""
Student Result Management System - CLI Interface
Entry point for managing secondary school student grades and academic reports.
"""

import sys
from result_manager import (
    load_data,
    save_data,
    register_student,
    record_subject_score,
    search_student_by_reg_number,
    search_students_by_query,
    generate_individual_report_card,
    generate_class_performance_summary,
    display_all_students_table,
    get_highest_performing_student,
    get_lowest_performing_student,
    rank_students,
    get_valid_score,
    get_non_empty_string,
    DEFAULT_SUBJECTS,
    DATA_FILE
)


def display_menu():
    """
    Displays the interactive main menu.
    """
    print("\n" + "=" * 54)
    print("   STUDENT RESULT MANAGEMENT SYSTEM (CLI)   ")
    print("=" * 54)
    print(" 1. Register New Student")
    print(" 2. Record / Update Subject Scores")
    print(" 3. Search Student by Registration Number")
    print(" 4. Generate Individual Student Report Card")
    print(" 5. View Class Performance Summary")
    print(" 6. View Top & Lowest Performing Students")
    print(" 7. Display All Students Roster")
    print(" 8. View / Configure Grading Scale")
    print(" 9. Exit System")
    print("=" * 54)


def handle_register_student(data):
    """
    Registers a new student.
    """
    print("\n--- [Register New Student] ---")
    name = get_non_empty_string("Enter student full name: ")
    class_level = get_non_empty_string("Enter class (e.g. SS 1, SS 2, SS 3)", default="SS 1")

    student = register_student(data, name, class_level, DATA_FILE)
    print(f"\n✓ Student '{student['name']}' successfully registered!")
    print(f"  Assigned Registration Number: {student['reg_number']}")


def handle_record_scores(data):
    """
    Records or updates scores for a student.
    """
    print("\n--- [Record / Update Subject Scores] ---")
    if not data["students"]:
        print("No students registered. Please register a student first.")
        return

    reg_no = input("Enter Student Registration Number (e.g. REG-2026-001): ").strip()
    student = search_student_by_reg_number(data["students"], reg_no)
    if not student:
        print(f"[Error] Student with Reg No '{reg_no}' not found.")
        return

    print(f"\nRecording scores for: {student['name']} ({student['reg_number']})")
    print(f"Current scores: {student['scores'] if student['scores'] else 'None'}")

    while True:
        print("\nSelect Subject Option:")
        for idx, subj in enumerate(DEFAULT_SUBJECTS, start=1):
            print(f"  {idx}. {subj}")
        print(f"  {len(DEFAULT_SUBJECTS) + 1}. [Custom Subject]")
        print("  0. Done recording scores")

        choice = input(f"Choose option (0-{len(DEFAULT_SUBJECTS) + 1}): ").strip()
        if choice == "0":
            break

        if choice.isdigit() and 1 <= int(choice) <= len(DEFAULT_SUBJECTS):
            subject_name = DEFAULT_SUBJECTS[int(choice) - 1]
        elif choice == str(len(DEFAULT_SUBJECTS) + 1):
            subject_name = get_non_empty_string("Enter custom subject name: ")
        else:
            print("  [Error] Invalid choice.")
            continue

        score = get_valid_score(f"Enter score for {subject_name} (0-100): ")
        success, msg = record_subject_score(data, student["reg_number"], subject_name, score, DATA_FILE)
        if success:
            print(f"  ✓ {msg}")
        else:
            print(f"  [Error] {msg}")

        more = input("\nRecord score for another subject? (y/n, default: y): ").strip().lower()
        if more == "n":
            break


def handle_search_student(data):
    """
    Searches for a student by registration number or name.
    """
    print("\n--- [Search Student] ---")
    if not data["students"]:
        print("No students in database.")
        return

    query = input("Enter Registration Number or Name to search: ").strip()
    if not query:
        print("[Error] Search query cannot be empty.")
        return

    matches = search_students_by_query(data["students"], query)
    if not matches:
        print(f"No student matching '{query}' found.")
        return

    print(f"\nFound {len(matches)} match(es):")
    print("-" * 60)
    for s in matches:
        score_count = len(s.get("scores", {}))
        print(f" Reg No: {s['reg_number']:<16} | Name: {s['name']:<22} | Class: {s.get('class_level', '-'):<6} | Subjects: {score_count}")
    print("-" * 60)


def handle_individual_report(data):
    """
    Generates and prints a student result card with class rank.
    """
    print("\n--- [Generate Student Result Report] ---")
    if not data["students"]:
        print("No students registered.")
        return

    reg_no = input("Enter Student Registration Number: ").strip()
    student = search_student_by_reg_number(data["students"], reg_no)
    if not student:
        print(f"[Error] Student '{reg_no}' not found.")
        return

    # Determine rank
    ranked = rank_students(data["students"], data.get("grading_scale"))
    student_rank = "-"
    total_scored = len([item for item in ranked if item[1] != "-"])

    for s, r, _ in ranked:
        if s["reg_number"] == student["reg_number"]:
            student_rank = r
            break

    generate_individual_report_card(student, student_rank, total_scored, data.get("grading_scale"))


def handle_top_and_lowest_students(data):
    """
    Displays the top and lowest performing students in the school.
    """
    print("\n--- [Academic Performance Extremes] ---")
    if not data["students"]:
        print("No students registered.")
        return

    top = get_highest_performing_student(data["students"], data.get("grading_scale"))
    low = get_lowest_performing_student(data["students"], data.get("grading_scale"))

    if not top or not low:
        print("No student results have been recorded yet.")
        return

    top_s, top_m = top
    low_s, low_m = low

    print("\n" + "=" * 55)
    print("               TOP PERFORMING STUDENT")
    print("=" * 55)
    print(f" Name:            {top_s['name']}")
    print(f" Reg Number:      {top_s['reg_number']}")
    print(f" Class:           {top_s.get('class_level', 'N/A')}")
    print(f" Total Score:     {top_m['total_score']:.1f}")
    print(f" Average Score:   {top_m['average_score']:.2f}% (Grade: {top_m['overall_grade']})")
    print(f" Remark:          {top_m['overall_remark']}")
    print("=" * 55)

    print("\n" + "=" * 55)
    print("             LOWEST PERFORMING STUDENT")
    print("=" * 55)
    print(f" Name:            {low_s['name']}")
    print(f" Reg Number:      {low_s['reg_number']}")
    print(f" Class:           {low_s.get('class_level', 'N/A')}")
    print(f" Total Score:     {low_m['total_score']:.1f}")
    print(f" Average Score:   {low_m['average_score']:.2f}% (Grade: {low_m['overall_grade']})")
    print(f" Remark:          {low_m['overall_remark']}")
    print("=" * 55)


def handle_grading_scale(data):
    """
    Displays current grading rules and allows modification.
    """
    print("\n--- [Configurable Grading Scale] ---")
    scale = data.get("grading_scale", [])
    print(f"{'Min Score':<12} | {'Grade':<8} | {'Remark'}")
    print("-" * 35)
    for rule in sorted(scale, key=lambda r: r["min_score"], reverse=True):
        print(f"{rule['min_score']:>8.1f}%   | {rule['grade']:<8} | {rule['remark']}")
    print("-" * 35)


def main():
    """
    Main application execution loop.
    """
    print("\nStarting Student Result Management System...")
    data = load_data(DATA_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-9): ").strip()

            if choice == "1":
                handle_register_student(data)
            elif choice == "2":
                handle_record_scores(data)
            elif choice == "3":
                handle_search_student(data)
            elif choice == "4":
                handle_individual_report(data)
            elif choice == "5":
                generate_class_performance_summary(data["students"], data.get("grading_scale"))
            elif choice == "6":
                handle_top_and_lowest_students(data)
            elif choice == "7":
                display_all_students_table(data["students"], data.get("grading_scale"))
            elif choice == "8":
                handle_grading_scale(data)
            elif choice == "9":
                print("\nExiting Student Result Management System. Goodbye!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid choice. Please enter a number between 1 and 9.")

        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
