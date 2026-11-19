"""
Unit Tests for Student Result Management System
Tests registration, score recording, input validation, grading, ranking,
top/lowest student determination, search, and JSON persistence.
"""

import os
import unittest
import tempfile
from result_manager import (
    load_data,
    save_data,
    register_student,
    validate_score,
    record_subject_score,
    assign_grade,
    calculate_student_metrics,
    rank_students,
    get_highest_performing_student,
    get_lowest_performing_student,
    search_student_by_reg_number,
    search_students_by_query
)


class TestResultManager(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        self.test_path = self.temp_file.name

        self.sample_data = {
            "grading_scale": [
                {"min_score": 70.0, "grade": "A", "remark": "Distinction"},
                {"min_score": 60.0, "grade": "B", "remark": "Very Good"},
                {"min_score": 50.0, "grade": "C", "remark": "Credit"},
                {"min_score": 45.0, "grade": "D", "remark": "Pass"},
                {"min_score": 40.0, "grade": "E", "remark": "Fair"},
                {"min_score": 0.0,  "grade": "F", "remark": "Fail"}
            ],
            "students": [
                {
                    "reg_number": "REG-2026-001",
                    "name": "Alice Johnson",
                    "class_level": "SS 3",
                    "scores": {
                        "Mathematics": 85.0,
                        "English Language": 75.0,
                        "Physics": 90.0
                    }
                },
                {
                    "reg_number": "REG-2026-002",
                    "name": "Bob Smith",
                    "class_level": "SS 3",
                    "scores": {
                        "Mathematics": 50.0,
                        "English Language": 55.0,
                        "Physics": 45.0
                    }
                },
                {
                    "reg_number": "REG-2026-003",
                    "name": "Charlie Brown",
                    "class_level": "SS 3",
                    "scores": {
                        "Mathematics": 95.0,
                        "English Language": 90.0,
                        "Physics": 98.0
                    }
                }
            ]
        }

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_save_and_load_persistence(self):
        """Test data saving and loading integrity."""
        self.assertTrue(save_data(self.sample_data, self.test_path))
        loaded = load_data(self.test_path)
        self.assertEqual(len(loaded["students"]), 3)
        self.assertEqual(loaded["students"][0]["name"], "Alice Johnson")

    def test_corrupted_file_recovery(self):
        """Test system initializes safe defaults when file is corrupt."""
        with open(self.test_path, "w") as f:
            f.write("corrupted json content [[{")
        loaded = load_data(self.test_path)
        self.assertEqual(loaded["students"], [])
        self.assertIn("grading_scale", loaded)

    def test_register_student_unique_reg_no(self):
        """Test student registration assigns unique formatted registration numbers."""
        new_student = register_student(self.sample_data, "Diana Prince", "SS 2", self.test_path)
        self.assertEqual(new_student["reg_number"], "REG-2026-004")
        self.assertEqual(new_student["name"], "Diana Prince")
        self.assertEqual(len(self.sample_data["students"]), 4)

    def test_validate_score_range(self):
        """Test validation rejects scores below 0, above 100, and non-numeric inputs."""
        valid, val = validate_score(75.5)
        self.assertTrue(valid)
        self.assertEqual(val, 75.5)

        # Boundary scores
        self.assertTrue(validate_score(0)[0])
        self.assertTrue(validate_score(100)[0])

        # Invalid scores
        self.assertFalse(validate_score(-5)[0])
        self.assertFalse(validate_score(105)[0])
        self.assertFalse(validate_score("invalid_score")[0])

    def test_record_subject_score(self):
        """Test recording valid score updates student scores dict."""
        success, msg = record_subject_score(self.sample_data, "REG-2026-001", "Chemistry", 88.0, self.test_path)
        self.assertTrue(success)
        student = search_student_by_reg_number(self.sample_data["students"], "REG-2026-001")
        self.assertEqual(student["scores"]["Chemistry"], 88.0)

    def test_assign_grade(self):
        """Test grade assignment against configurable scale."""
        scale = self.sample_data["grading_scale"]
        grade_a, _ = assign_grade(85.0, scale)
        grade_b, _ = assign_grade(65.0, scale)
        grade_c, _ = assign_grade(52.0, scale)
        grade_f, _ = assign_grade(30.0, scale)

        self.assertEqual(grade_a, "A")
        self.assertEqual(grade_b, "B")
        self.assertEqual(grade_c, "C")
        self.assertEqual(grade_f, "F")

    def test_calculate_student_metrics(self):
        """Test total score and average score calculations."""
        # Alice: 85 + 75 + 90 = 250. Average = 250 / 3 = 83.33 -> Grade A
        alice = self.sample_data["students"][0]
        metrics = calculate_student_metrics(alice, self.sample_data["grading_scale"])
        self.assertEqual(metrics["total_score"], 250.0)
        self.assertEqual(metrics["average_score"], 83.33)
        self.assertEqual(metrics["overall_grade"], "A")

    def test_highest_and_lowest_performing_students(self):
        """Test determining highest and lowest academic performers."""
        # Charlie: (95 + 90 + 98)/3 = 94.33 (Highest)
        # Bob: (50 + 55 + 45)/3 = 50.0 (Lowest)
        highest_student, high_metrics = get_highest_performing_student(self.sample_data["students"])
        lowest_student, low_metrics = get_lowest_performing_student(self.sample_data["students"])

        self.assertEqual(highest_student["name"], "Charlie Brown")
        self.assertEqual(high_metrics["average_score"], 94.33)

        self.assertEqual(lowest_student["name"], "Bob Smith")
        self.assertEqual(low_metrics["average_score"], 50.0)

    def test_search_student_by_reg_number(self):
        """Test exact search by registration number."""
        found = search_student_by_reg_number(self.sample_data["students"], "reg-2026-002")
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Bob Smith")

        not_found = search_student_by_reg_number(self.sample_data["students"], "REG-9999-999")
        self.assertIsNone(not_found)

    def test_search_students_by_query(self):
        """Test partial search by name or registration number."""
        results = search_students_by_query(self.sample_data["students"], "Johnson")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["reg_number"], "REG-2026-001")


if __name__ == "__main__":
    unittest.main()
