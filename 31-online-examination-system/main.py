"""
Command-Line Interface for Online Examination Management System.
"""
import sys
from datetime import datetime
from exam_service import ExamService


def print_header(title):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def seed_demo_data(service):
    try:
        # Users
        service.register_user("ADM-001", "Grace Hopper", "grace@academy.edu", "admin")
        service.register_user("TCH-101", "Dr. Alan Turing", "turing@academy.edu", "teacher")
        service.register_user("STU-101", "Ada Lovelace", "ada@student.edu", "student")
        service.register_user("STU-102", "Charles Babbage", "charles@student.edu", "student")

        # Subject
        service.create_subject("CS101", "Computer Science Principles", "Introduction to Computing", "TCH-101")

        # Exam
        service.create_exam(
            exam_code="CS101-MID",
            subject_code="CS101",
            title="CS101 Midterm Examination",
            duration_minutes=15,
            passing_score=50.0,
            created_by_user_id="TCH-101"
        )

        # Questions
        service.add_question(
            "CS101-MID", 1, "What is the base of the binary number system?",
            "Base 2", "Base 8", "Base 10", "Base 16", "A", 5.0
        )
        service.add_question(
            "CS101-MID", 2, "Which data structure follows First-In, First-Out (FIFO)?",
            "Stack", "Queue", "Tree", "Graph", "B", 5.0
        )
        service.add_question(
            "CS101-MID", 3, "What does HTTP stand for?",
            "HyperText Transfer Protocol", "High Text Transfer Program",
            "Hyper Technical Test Protocol", "Home Tool Transfer Packet", "A", 5.0
        )

        # Publish and assign
        service.publish_exam("CS101-MID")
        service.assign_exam_to_student("CS101-MID", "STU-101")
        service.assign_exam_to_student("CS101-MID", "STU-102")

        print(" Demo data seeded successfully!")
    except Exception as e:
        print(f" Demo seeding notice: {e}")


def handle_take_exam(service):
    print_header("Take Examination (Student Portal)")
    student_id = input("Enter your Student ID (e.g. STU-101): ").strip()
    try:
        assigned = service.list_assigned_exams(student_id)
        if not assigned:
            print(f"No examinations assigned to student {student_id}.")
            return

        print(f"\nAssigned Examinations for {student_id}:")
        print("-" * 65)
        for idx, ex in enumerate(assigned, 1):
            pub = "Published" if ex["is_published"] else "Draft"
            print(f"{idx}. [{ex['exam_code']}] {ex['exam_title']} ({ex['subject_code']})")
            print(f"   Duration: {ex['duration_minutes']} min | Passing Score: {ex['passing_score']}% | Status: {ex['assignment_status']} ({pub})")

        exam_code = input("\nEnter Exam Code to begin/resume: ").strip()
        session_info = service.start_exam(student_id, exam_code)

        session_id = session_info["session_id"]
        expires_at = session_info["expires_at"]
        print(f"\n Exam Session Started (Session #{session_id})")
        print(f"Examination must be completed by: {expires_at}")
        print("Answer each question by typing A, B, C, or D.\n")

        questions = service.get_exam_questions(exam_code, include_correct=False)
        for q in questions:
            print(f"\nQuestion {q['question_number']} ({q['points']} pts): {q['question_text']}")
            print(f"  A) {q['option_a']}")
            print(f"  B) {q['option_b']}")
            print(f"  C) {q['option_c']}")
            print(f"  D) {q['option_d']}")

            ans = input("Your answer (A/B/C/D or Enter to skip): ").strip().upper()
            if ans in ("A", "B", "C", "D"):
                service.answer_question(session_id, q["question_number"], ans)

        confirm = input("\nSubmit examination now? (y/n): ").strip().lower()
        if confirm == "y":
            result = service.submit_exam(session_id)
            print("\n" + "=" * 40)
            print(f" Examination Result: {result['status'].upper()}")
            print(f" Score: {result['score']}/{result['total_points']} ({result['percentage']}%)")
            print(f" Outcome: {'PASSED' if result['passed'] else 'FAILED'}")
            print("=" * 40)
    except Exception as e:
        print(f" Error: {e}")


def main():
    service = ExamService()
    seed_demo_data(service)

    while True:
        print_header("Online Examination Management System")
        print("1. Register User (Student / Teacher / Admin)")
        print("2. Create Subject")
        print("3. Create Examination")
        print("4. Add Multiple-Choice Questions")
        print("5. Publish Examination")
        print("6. Assign Examination to Student")
        print("7. Take Examination (Student Mode)")
        print("8. View Examination Result by Session ID")
        print("9. Authorize Retake for a Student")
        print("10. Generate Examination Performance Report")
        print("11. List Subjects and Exams")
        print("0. Exit")

        choice = input("\nEnter selection (0-11): ").strip()

        if choice == "1":
            uid = input("User ID (e.g. STU-201, TCH-201): ")
            name = input("Full Name: ")
            email = input("Email Address: ")
            role = input("Role (student/teacher/admin): ")
            try:
                service.register_user(uid, name, email, role)
                print(f" User {uid} registered successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "2":
            code = input("Subject Code (e.g. BIO101): ")
            title = input("Subject Title: ")
            desc = input("Description: ")
            tid = input("Teacher User ID (optional): ")
            try:
                service.create_subject(code, title, desc, tid if tid else None)
                print(f" Subject {code} created successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "3":
            ecode = input("Exam Code (e.g. BIO101-MID): ")
            subcode = input("Subject Code: ")
            title = input("Exam Title: ")
            try:
                dur = int(input("Duration in minutes (e.g. 60): "))
                pass_score = float(input("Passing Score % (default 50.0): ") or "50.0")
                start_w = input("Start Window ISO (YYYY-MM-DDTHH:MM:SS or Enter to skip): ").strip()
                end_w = input("End Window ISO (YYYY-MM-DDTHH:MM:SS or Enter to skip): ").strip()
                service.create_exam(ecode, subcode, title, dur, pass_score,
                                   start_w if start_w else None,
                                   end_w if end_w else None)
                print(f" Examination {ecode} created successfully.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "4":
            ecode = input("Exam Code: ")
            try:
                qnum = int(input("Question Number: "))
                qtext = input("Question Text: ")
                oa = input("Option A: ")
                ob = input("Option B: ")
                oc = input("Option C: ")
                od = input("Option D: ")
                corr = input("Correct Option (A/B/C/D): ")
                pts = float(input("Points (default 1.0): ") or "1.0")
                service.add_question(ecode, qnum, qtext, oa, ob, oc, od, corr, pts)
                print(f" Question #{qnum} added.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "5":
            ecode = input("Exam Code to publish: ")
            try:
                service.publish_exam(ecode)
                print(f" Exam {ecode} is now published and active.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "6":
            ecode = input("Exam Code: ")
            sid = input("Student User ID: ")
            try:
                service.assign_exam_to_student(ecode, sid)
                print(f" Exam {ecode} assigned to student {sid}.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "7":
            handle_take_exam(service)

        elif choice == "8":
            try:
                sess_id = int(input("Enter Session ID: "))
                res = service.get_session_result(sess_id)
                print(f"\n--- Result for {res['student_name']} ({res['student_code']}) ---")
                print(f"Exam: {res['exam_title']} ({res['exam_code']})")
                print(f"Status: {res['status']} | Outcome: {'PASSED' if res['passed'] else 'FAILED'}")
                print(f"Score: {res['score']}/{res['total_points']} ({res['percentage']}%)")
                print("\nQuestion Breakdown:")
                for a in res["answers"]:
                    verdict = "CORRECT" if a["is_correct"] else "INCORRECT"
                    print(f" Q{a['question_number']}: Selected: {a['selected_option'] or 'None'} | Correct: {a['correct_option']} -> {verdict} ({a['points_awarded']} pts)")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "9":
            ecode = input("Exam Code: ")
            sid = input("Student User ID: ")
            try:
                service.authorize_retake(ecode, sid)
                print(f" Retake authorized for student {sid} on exam {ecode}.")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "10":
            ecode = input("Exam Code: ")
            try:
                rep = service.generate_exam_report(ecode)
                print_header(f"Performance Report: {rep['exam_title']} ({rep['exam_code']})")
                print(f"Subject: {rep['subject']}")
                print(f"Total Assigned: {rep['total_assigned']} | Total Sat: {rep['total_sat']}")
                print(f"Passed: {rep['passed_count']} | Failed: {rep['failed_count']} | Pass Rate: {rep['pass_rate_pct']}%")
                print(f"Average Score: {rep['average_score_pct']}% | High: {rep['highest_score_pct']}% | Low: {rep['lowest_score_pct']}%")

                if rep["question_analytics"]:
                    print("\nQuestion Difficulty Breakdown:")
                    print(f"{'Q#':<5} {'Points':<8} {'Answered':<10} {'Correct':<10} {'Accuracy':<10}")
                    for qa in rep["question_analytics"]:
                        print(f"{qa['question_number']:<5} {qa['points']:<8} {qa['total_answered']:<10} {qa['correct_count']:<10} {qa['accuracy_pct']:<10}%")
            except Exception as e:
                print(f" Error: {e}")

        elif choice == "11":
            print("\n--- Subjects ---")
            for s in service.list_subjects():
                print(f"[{s['code']}] {s['title']} (Teacher: {s['teacher_name'] or 'None'})")

        elif choice == "0":
            print("Exiting Online Examination System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice, please select 0-11.")


if __name__ == "__main__":
    main()
