"""
Unit tests for Job Recruitment and Applicant Tracking System.
"""
import unittest
import os
import shutil
from recruitment_service import RecruitmentService, AccessControlError, VALID_APPLICATION_STATUSES

TEST_DB = "test_recruitment.db"
TEST_UPLOADS = "test_uploads"


class TestRecruitmentTracker(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = RecruitmentService(TEST_DB, TEST_UPLOADS)

        # Register admin & recruiter
        self.service.register_user(None, "ADM-01", "superadmin", "AdminPass123!", "Super Admin", "admin@agency.com", "admin")
        self.admin = self.service.authenticate_user("superadmin", "AdminPass123!")

        self.service.register_user(self.admin, "REC-01", "recruiter1", "Recruiter123!", "Jane Recruiter", "jane@agency.com", "recruiter")
        self.recruiter = self.service.authenticate_user("recruiter1", "Recruiter123!")

        self.service.register_user(self.admin, "HM-01", "manager1", "Manager123!", "Bob Manager", "bob@client.com", "hiring_manager")
        self.manager = self.service.authenticate_user("manager1", "Manager123!")

        # Setup standard company & vacancy
        self.service.register_company(
            self.recruiter, "COMP-01", "Acme Corporation", "Software",
            "Alice Smith", "alice@acme.com", "+2348011112222", "Lagos"
        )
        self.service.create_vacancy(
            self.recruiter, "VAC-101", "COMP-01", "Python Developer", "Engineering",
            "Full-time", "Lagos", 2.0, "Python, SQL, Django",
            "Build robust APIs", "2+ years experience in Python",
            salary_min=5000000.0, salary_max=8000000.0
        )

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_UPLOADS):
            shutil.rmtree(TEST_UPLOADS, ignore_errors=True)

    # ==================== User & Authorization Tests ====================

    def test_user_authentication_and_rbac(self):
        u = self.service.authenticate_user("recruiter1", "Recruiter123!")
        self.assertEqual(u["role"], "recruiter")

        # Hiring manager cannot create vacancies
        with self.assertRaises(AccessControlError):
            self.service.create_vacancy(
                self.manager, "VAC-999", "COMP-01", "Sales Rep", "Sales",
                "Full-time", "Lagos", 1.0, "Sales", "Desc", "Reqs"
            )

    # ==================== Company & Vacancy Tests ====================

    def test_vacancy_validation(self):
        # Salary max < min
        with self.assertRaises(ValueError):
            self.service.create_vacancy(
                self.recruiter, "VAC-102", "COMP-01", "Dev", "Eng",
                "Full-time", "Lagos", 2.0, "Python", "Desc", "Reqs",
                salary_min=500000.0, salary_max=200000.0
            )

        # Invalid employment type
        with self.assertRaises(ValueError):
            self.service.create_vacancy(
                self.recruiter, "VAC-103", "COMP-01", "Dev", "Eng",
                "Volunteer", "Lagos", 2.0, "Python", "Desc", "Reqs"
            )

    # ==================== Candidate & Search Tests ====================

    def test_candidate_registration_and_search(self):
        c1 = self.service.register_candidate(
            "Chidi Obi", "chidi@example.com", "+2348022223333", "Lagos",
            "Backend Engineer", 4.5, "Python, FastAPI, Docker, PostgreSQL"
        )
        c2 = self.service.register_candidate(
            "Aisha Garba", "aisha@example.com", "+2348033334444", "Abuja",
            "Frontend Engineer", 3.0, "JavaScript, React, TypeScript, CSS"
        )

        # Search by skill
        python_candidates = self.service.search_candidates(skill_query="Python")
        self.assertEqual(len(python_candidates), 1)
        self.assertEqual(python_candidates[0]["candidate_code"], c1)

        # Search by minimum experience
        experienced = self.service.search_candidates(min_years_exp=4.0)
        self.assertEqual(len(experienced), 1)
        self.assertEqual(experienced[0]["candidate_code"], c1)

    # ==================== Job Application & Duplicate Prevention ====================

    def test_application_submission_and_duplicate_prevention(self):
        cand = self.service.register_candidate(
            "Emeka Ike", "emeka@example.com", "+2348044445555", "Lagos",
            "Python Dev", 3.0, "Python, Django"
        )

        app_ref = self.service.apply_to_vacancy(cand, "VAC-101", "Cover letter text")
        self.assertTrue(app_ref.startswith("APP-"))

        # Verify initial status is Submitted
        details = self.service.get_application_details(app_ref)
        self.assertEqual(details["status"], "Submitted")

        # Attempt duplicate application to same vacancy must fail
        with self.assertRaises(ValueError) as ctx:
            self.service.apply_to_vacancy(cand, "VAC-101", "Second attempt")
        self.assertIn("Duplicate application", str(ctx.exception))

    # ==================== CV Upload & Validation ====================

    def test_cv_upload_validation(self):
        cand = self.service.register_candidate(
            "Bola Tinubu", "bola@example.com", "+2348055556666", "Lagos",
            "Python Dev", 5.0, "Python, SQL"
        )
        app_ref = self.service.apply_to_vacancy(cand, "VAC-101")

        # Unsupported file extension (.exe)
        with self.assertRaises(ValueError) as ctx:
            self.service.upload_candidate_cv(app_ref, "malicious.exe", b"fake binary data")
        self.assertIn("Unsupported file format", str(ctx.exception))

        # Empty file (0 bytes)
        with self.assertRaises(ValueError) as ctx:
            self.service.upload_candidate_cv(app_ref, "empty_cv.pdf", b"")
        self.assertIn("empty", str(ctx.exception))

        # Oversized file (> 5MB)
        oversized = b"X" * (6 * 1024 * 1024)
        with self.assertRaises(ValueError) as ctx:
            self.service.upload_candidate_cv(app_ref, "huge_cv.pdf", oversized)
        self.assertIn("exceeds maximum allowable limit", str(ctx.exception))

        # Valid PDF file
        valid_bytes = b"%PDF-1.4 sample resume content for testing purposes"
        meta = self.service.upload_candidate_cv(app_ref, "my_resume.pdf", valid_bytes)
        self.assertEqual(meta["file_type"], "pdf")
        self.assertTrue(os.path.exists(meta["file_path"]))

    # ==================== Application Status Workflow ====================

    def test_application_status_transitions_and_history(self):
        cand = self.service.register_candidate(
            "Funke Akindele", "funke@example.com", "+2348066667777", "Lagos",
            "Python Dev", 3.5, "Python, SQL"
        )
        app_ref = self.service.apply_to_vacancy(cand, "VAC-101")

        # Transition through valid statuses
        statuses = ["Under Review", "Shortlisted", "Accepted"]
        for st in statuses:
            self.service.update_application_status(self.recruiter, app_ref, st, notes=f"Moved to {st}")

        # Invalid status must be rejected
        with self.assertRaises(ValueError):
            self.service.update_application_status(self.recruiter, app_ref, "Hired-Pending")

        # Check full history
        history = self.service.get_application_history(app_ref)
        self.assertEqual(len(history), 4)  # 1 initial Submitted + 3 updates
        self.assertEqual(history[-1]["new_status"], "Accepted")

    # ==================== Interview & Feedback Tests ====================

    def test_interview_scheduling_and_feedback(self):
        cand = self.service.register_candidate(
            "Segun Arinze", "segun@example.com", "+2348077778888", "Lagos",
            "Python Dev", 4.0, "Python, Docker"
        )
        app_ref = self.service.apply_to_vacancy(cand, "VAC-101")

        # Schedule interview
        int_ref = self.service.schedule_interview(
            self.recruiter, app_ref, "Technical Interview",
            "2026-12-10 11:00", "Bob Manager", "https://meet.google.com/test"
        )
        self.assertTrue(int_ref.startswith("INT-"))

        # Verify application status automatically updated to 'Interview Scheduled'
        details = self.service.get_application_details(app_ref)
        self.assertEqual(details["status"], "Interview Scheduled")

        # Record feedback
        fid = self.service.record_interview_feedback(
            self.manager, int_ref,
            rating_overall=4, technical_score=4, communication_score=5, problem_solving_score=4,
            strengths="Great system design", areas_for_improvement="Unit test coverage",
            recommendation="Hire", notes="Solid fit"
        )
        self.assertGreater(fid, 0)

    def test_invalid_interview_feedback_scores(self):
        cand = self.service.register_candidate(
            "Test Candidate", "test.cand@example.com", "+2348000001111", "Lagos",
            "Dev", 2.0, "Python"
        )
        app_ref = self.service.apply_to_vacancy(cand, "VAC-101")
        int_ref = self.service.schedule_interview(
            self.recruiter, app_ref, "Phone Screen",
            "2026-12-15 10:00", "Interviewer", "Remote Link"
        )

        # Score out of bounds (> 5)
        with self.assertRaises(ValueError):
            self.service.record_interview_feedback(
                self.manager, int_ref,
                rating_overall=6, technical_score=5, communication_score=5, problem_solving_score=5,
                strengths="Great", areas_for_improvement="None", recommendation="Hire"
            )

        # Invalid recommendation
        with self.assertRaises(ValueError):
            self.service.record_interview_feedback(
                self.manager, int_ref,
                rating_overall=4, technical_score=4, communication_score=4, problem_solving_score=4,
                strengths="Good", areas_for_improvement="None", recommendation="Instant CEO"
            )

    def test_candidate_validation_errors(self):
        # Invalid email
        with self.assertRaises(ValueError):
            self.service.register_candidate(
                "Bad Email", "not-an-email", "+2348000002222", "Lagos",
                "Dev", 2.0, "Python"
            )

        # Negative years of experience
        with self.assertRaises(ValueError):
            self.service.register_candidate(
                "Negative Exp", "neg@example.com", "+2348000002222", "Lagos",
                "Dev", -2.0, "Python"
            )

    # ==================== Reporting Tests ====================

    def test_recruitment_reports(self):
        rep = self.service.generate_recruitment_reports()
        self.assertIn("total_companies", rep)
        self.assertIn("total_vacancies", rep)
        self.assertIn("pipeline_funnel", rep)


if __name__ == "__main__":
    unittest.main()
