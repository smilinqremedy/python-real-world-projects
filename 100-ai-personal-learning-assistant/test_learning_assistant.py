"""
Automated unit tests for AI-Powered Personal Learning Assistant.
"""
import unittest
import os
import shutil
import tempfile
import csv

from auth import hash_password, verify_password
from content_processor import ContentProcessor, GeneratedQuestion
from learning_engine import LearningEngine
import database


class TestPersonalLearningAssistant(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_learning.db")
        self.engine = LearningEngine(db_path=self.db_path)

        # Create sample study notes file
        self.sample_txt = os.path.join(self.test_dir, "quantum_notes.txt")
        with open(self.sample_txt, "w", encoding="utf-8") as f:
            f.write(
                "Superposition is a fundamental principle of quantum mechanics where physical systems exist in multiple states simultaneously. "
                "Quantum entanglement refers to particles whose physical states cannot be described independently of each other. "
                "Qubits are the basic unit of quantum information analogous to classical binary bits."
            )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_auth_hashing_and_verification(self):
        h, salt = hash_password("LearnerPass@2026")
        self.assertTrue(verify_password("LearnerPass@2026", h, salt))
        self.assertFalse(verify_password("WrongPassword", h, salt))

    def test_user_and_subject_management(self):
        uid = self.engine.register_user("student_alex", "Pass@123")
        self.assertIsNotNone(uid)

        # Duplicate username should return None
        dup_uid = self.engine.register_user("student_alex", "Pass@456")
        self.assertIsNone(dup_uid)

        # Login
        user = self.engine.authenticate_user("student_alex", "Pass@123")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "student_alex")

        # Create subject
        sid = self.engine.add_subject(uid, "Physics", "Quantum mechanics and thermodynamics")
        self.assertIsNotNone(sid)
        subjects = self.engine.get_subjects(uid)
        self.assertEqual(len(subjects), 1)
        self.assertEqual(subjects[0]["title"], "Physics")

    def test_content_processing_and_grounded_questions(self):
        content = ContentProcessor.extract_text_from_file(self.sample_txt)
        self.assertIn("Superposition", content)

        summary = ContentProcessor.generate_topic_summary(content, max_sentences=2)
        self.assertTrue(len(summary) > 20)

        questions = ContentProcessor.generate_grounded_questions(content, num_questions=3)
        self.assertGreater(len(questions), 0)

        for q in questions:
            self.assertIsInstance(q, GeneratedQuestion)
            self.assertIn(q.question_type, ["mcq", "short_answer"])
            self.assertTrue(len(q.correct_answer) > 0)
            self.assertTrue(len(q.source_excerpt) > 0)
            if q.question_type == "mcq":
                self.assertEqual(len(q.options), 4)
                self.assertIn(q.correct_answer, q.options)

    def test_topic_creation_and_quiz_grading(self):
        uid = self.engine.register_user("student_bella", "Pass@123")
        sid = self.engine.add_subject(uid, "Quantum Physics")

        with open(self.sample_txt, "r", encoding="utf-8") as f:
            notes = f.read()

        topic_res = self.engine.add_topic_with_content(uid, sid, "Superposition & Qubits", notes)
        tid = topic_res["topic_id"]
        self.assertGreater(tid, 0)

        questions = self.engine.get_questions_for_topic(tid)
        self.assertGreater(len(questions), 0)

        # Submit perfect answers
        perfect_answers = {q["id"]: q["correct_answer"] for q in questions}
        grade_res = self.engine.grade_quiz(uid, tid, perfect_answers)
        self.assertEqual(grade_res["score_pct"], 100.0)
        self.assertEqual(grade_res["correct_count"], len(questions))

    def test_weak_topic_detection_and_revision_recommendation(self):
        uid = self.engine.register_user("student_charlie", "Pass@123")
        sid = self.engine.add_subject(uid, "Quantum Physics")

        with open(self.sample_txt, "r", encoding="utf-8") as f:
            notes = f.read()

        topic_res = self.engine.add_topic_with_content(uid, sid, "Difficult Concept", notes)
        tid = topic_res["topic_id"]
        questions = self.engine.get_questions_for_topic(tid)

        # Intentionally submit incorrect answers to trigger weak topic alert (< 70%)
        wrong_answers = {q["id"]: "Completely Wrong Answer" for q in questions}
        grade_res = self.engine.grade_quiz(uid, tid, wrong_answers)
        self.assertLess(grade_res["score_pct"], 70.0)

        # Verify weak topic detection
        weak = self.engine.identify_weak_topics(uid, threshold_pct=70.0)
        self.assertEqual(len(weak), 1)
        self.assertEqual(weak[0]["topic_id"], tid)
        self.assertLess(weak[0]["avg_score"], 70.0)

        # Verify recommendation
        recs = self.engine.get_revision_recommendations(uid)
        self.assertEqual(len(recs), 1)
        self.assertIn("Difficult Concept", recs[0]["topic"])

    def test_progress_report_export(self):
        uid = self.engine.register_user("student_david", "Pass@123")
        sid = self.engine.add_subject(uid, "Computer Science")
        self.engine.add_topic_with_content(uid, sid, "Data Structures", "Arrays are contiguous memory blocks. Linked lists consist of nodes.")

        out_csv = os.path.join(self.test_dir, "progress.csv")
        csv_data = self.engine.export_progress_report(uid, out_csv)

        self.assertTrue(os.path.exists(out_csv))
        self.assertIn("Computer Science", csv_data)
        self.assertIn("Data Structures", csv_data)


if __name__ == "__main__":
    unittest.main()
