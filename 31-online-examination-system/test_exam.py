"""
Unit tests for Online Examination Management System.
"""
import unittest
import os
from datetime import datetime, timedelta
from exam_service import ExamService

TEST_DB = "test_examination.db"


class TestExamSystem(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        self.service = ExamService(TEST_DB)

        # Setup standard users
        self.service.register_user("TCH-101", "Dr. Alan Turing", "turing@uni.edu", "teacher")
        self.service.register_user("ADM-001", "Admin Grace", "grace@uni.edu", "admin")
        self.service.register_user("STU-501", "Alice Student", "alice@student.edu", "student")
        self.service.register_user("STU-502", "Bob Scholar", "bob@student.edu", "student")

        # Setup subject
        self.service.create_subject("CS101", "Computer Science Principles", "Foundations of computing", "TCH-101")

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_user_and_subject_validation(self):
        # Invalid role
        with self.assertRaises(ValueError):
            self.service.register_user("INV-1", "Invalid", "inv@uni.edu", "manager")

        # Invalid email
        with self.assertRaises(ValueError):
            self.service.register_user("INV-2", "Invalid", "not-an-email", "student")

        # Duplicate ID
        with self.assertRaises(ValueError):
            self.service.register_user("STU-501", "Duplicate Alice", "newalice@student.edu", "student")

        # Subject listing
        subjects = self.service.list_subjects()
        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0]["code"], "CS101")
        self.assertEqual(subjects[0]["teacher_name"], "Dr. Alan Turing")

    def test_exam_creation_and_publishing(self):
        self.service.create_exam(
            exam_code="CS101-MID",
            subject_code="CS101",
            title="CS101 Midterm Exam",
            duration_minutes=30,
            passing_score=60.0,
            created_by_user_id="TCH-101"
        )

        # Cannot publish without questions
        with self.assertRaises(ValueError):
            self.service.publish_exam("CS101-MID")

        # Add 2 questions
        self.service.add_question(
            exam_code="CS101-MID",
            question_number=1,
            question_text="What does CPU stand for?",
            option_a="Central Processing Unit",
            option_b="Computer Personal Unit",
            option_c="Central Performance Utility",
            option_d="Core Processing Utility",
            correct_option="A",
            points=2.0
        )
        self.service.add_question(
            exam_code="CS101-MID",
            question_number=2,
            question_text="Which of these is a Python data structure?",
            option_a="Pointer",
            option_b="Dictionary",
            option_c="Segment",
            option_d="Register",
            correct_option="B",
            points=3.0
        )

        # Publish
        self.service.publish_exam("CS101-MID")

        # Questions cannot be added after publish
        with self.assertRaises(ValueError):
            self.service.add_question("CS101-MID", 3, "New Q", "A", "B", "C", "D", "A", 1.0)

        # Questions retrieved for candidate must not leak correct options
        candidate_qs = self.service.get_exam_questions("CS101-MID", include_correct=False)
        self.assertEqual(len(candidate_qs), 2)
        self.assertNotIn("correct_option", candidate_qs[0])

    def test_exam_workflow_and_grading(self):
        # Create and publish exam
        self.service.create_exam("CS101-FINAL", "CS101", "Final Exam", 45, passing_score=50.0)
        self.service.add_question("CS101-FINAL", 1, "Q1 Text", "A1", "B1", "C1", "D1", "A", 10.0)
        self.service.add_question("CS101-FINAL", 2, "Q2 Text", "A2", "B2", "C2", "D2", "C", 10.0)
        self.service.publish_exam("CS101-FINAL")

        # Assign to Alice
        self.service.assign_exam_to_student("CS101-FINAL", "STU-501")

        # Bob is not assigned and cannot start
        with self.assertRaises(ValueError):
            self.service.start_exam("STU-502", "CS101-FINAL")

        # Alice starts exam
        start_time = datetime(2026, 11, 19, 10, 0, 0)
        session = self.service.start_exam("STU-501", "CS101-FINAL", current_time=start_time)
        session_id = session["session_id"]
        self.assertIsNotNone(session_id)

        # Alice answers Q1 correctly and Q2 incorrectly
        self.service.answer_question(session_id, 1, "A", current_time=start_time + timedelta(minutes=5))
        self.service.answer_question(session_id, 2, "B", current_time=start_time + timedelta(minutes=10))

        # Alice submits exam
        submission = self.service.submit_exam(session_id, current_time=start_time + timedelta(minutes=15))
        self.assertEqual(submission["status"], "submitted")
        self.assertEqual(submission["score"], 10.0)
        self.assertEqual(submission["total_points"], 20.0)
        self.assertEqual(submission["percentage"], 50.0)
        self.assertTrue(submission["passed"])

        # Alice cannot retake without authorization
        with self.assertRaises(ValueError):
            self.service.start_exam("STU-501", "CS101-FINAL")

        # Teacher authorizes retake
        self.service.authorize_retake("CS101-FINAL", "STU-501")
        new_session = self.service.start_exam("STU-501", "CS101-FINAL", current_time=start_time + timedelta(hours=2))
        self.assertNotEqual(new_session["session_id"], session_id)

    def test_time_expiry_and_auto_submission(self):
        self.service.create_exam("CS101-QUIZ", "CS101", "Pop Quiz", 10, passing_score=50.0)
        self.service.add_question("CS101-QUIZ", 1, "Fast Q", "A", "B", "C", "D", "A", 5.0)
        self.service.publish_exam("CS101-QUIZ")
        self.service.assign_exam_to_student("CS101-QUIZ", "STU-501")

        start_time = datetime(2026, 11, 19, 9, 0, 0)
        session = self.service.start_exam("STU-501", "CS101-QUIZ", current_time=start_time)
        session_id = session["session_id"]

        # Student answers before expiry
        self.service.answer_question(session_id, 1, "A", current_time=start_time + timedelta(minutes=2))

        # Student tries to submit after expiry (15 mins into 10-min exam)
        result = self.service.submit_exam(session_id, current_time=start_time + timedelta(minutes=15))
        self.assertEqual(result["status"], "auto_submitted")
        self.assertEqual(result["score"], 5.0)
        self.assertEqual(result["percentage"], 100.0)

    def test_exam_performance_report(self):
        self.service.create_exam("STATS-1", "CS101", "Stats Exam", 60, passing_score=50.0)
        self.service.add_question("STATS-1", 1, "Q1", "A", "B", "C", "D", "A", 10.0)
        self.service.add_question("STATS-1", 2, "Q2", "A", "B", "C", "D", "B", 10.0)
        self.service.publish_exam("STATS-1")

        self.service.assign_exam_to_student("STATS-1", "STU-501")
        self.service.assign_exam_to_student("STATS-1", "STU-502")

        t0 = datetime(2026, 11, 19, 14, 0, 0)
        # Alice scores 20/20 (100%)
        s1 = self.service.start_exam("STU-501", "STATS-1", current_time=t0)["session_id"]
        self.service.answer_question(s1, 1, "A", current_time=t0)
        self.service.answer_question(s1, 2, "B", current_time=t0)
        self.service.submit_exam(s1, current_time=t0 + timedelta(minutes=20))

        # Bob scores 0/20 (0%)
        s2 = self.service.start_exam("STU-502", "STATS-1", current_time=t0)["session_id"]
        self.service.answer_question(s2, 1, "C", current_time=t0)
        self.service.answer_question(s2, 2, "C", current_time=t0)
        self.service.submit_exam(s2, current_time=t0 + timedelta(minutes=20))

        report = self.service.generate_exam_report("STATS-1")
        self.assertEqual(report["total_assigned"], 2)
        self.assertEqual(report["total_sat"], 2)
        self.assertEqual(report["passed_count"], 1)
        self.assertEqual(report["failed_count"], 1)
        self.assertEqual(report["pass_rate_pct"], 50.0)
        self.assertEqual(report["average_score_pct"], 50.0)
        self.assertEqual(report["highest_score_pct"], 100.0)
        self.assertEqual(report["lowest_score_pct"], 0.0)

        # Question analytics: Q1 answered correctly by 1 out of 2 (50%)
        q1_stat = next(q for q in report["question_analytics"] if q["question_number"] == 1)
        self.assertEqual(q1_stat["accuracy_pct"], 50.0)


if __name__ == "__main__":
    unittest.main()
