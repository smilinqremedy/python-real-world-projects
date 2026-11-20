"""
Unit tests for Automated Job Application Email Assistant.
"""
import unittest
import os
from assistant_service import EmailAssistantService
from email_generator import EmailGenerator

TEST_DB = "test_assistant.db"
TEST_CV = "test_sample_resume.pdf"


class TestEmailAssistant(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = EmailAssistantService(TEST_DB)
        with open(TEST_CV, "w") as f:
            f.write("Sample Resume Content")

        self.cid = self.service.add_company("Apex Corp", "recruitment@apex.com", "Tech")
        self.vid = self.service.add_vacancy(self.cid, "Python Backend Lead")

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        for p in [TEST_DB, TEST_CV]:
            if os.path.exists(p):
                os.remove(p)

    def test_template_substitution(self):
        tpl_subject = "Application for {job_title} at {company}"
        tpl_body = "Hello {recruiter_name}, I am {candidate_name} with {years_experience} years experience in {candidate_skills}."

        context = {
            "company": "Apex Corp",
            "job_title": "Python Lead",
            "recruiter_name": "Sarah",
            "candidate_name": "Tunde",
            "years_experience": "6",
            "candidate_skills": "Python, Docker, Kubernetes",
        }

        rendered = EmailGenerator.generate_application_email(tpl_subject, tpl_body, context)
        self.assertEqual(rendered["subject"], "Application for Python Lead at Apex Corp")
        self.assertIn("Hello Sarah", rendered["body"])
        self.assertIn("Tunde with 6 years experience", rendered["body"])
        self.assertIn("Python, Docker, Kubernetes", rendered["body"])

    def test_preview_generation_without_sending(self):
        profile = {
            "candidate_name": "Jane Doe",
            "years_experience": "5",
            "candidate_skills": "Django, AWS",
        }

        preview = self.service.preview_application(self.vid, 1, profile, TEST_CV)
        self.assertEqual(preview["company_name"], "Apex Corp")
        self.assertEqual(preview["recipient_email"], "recruitment@apex.com")
        self.assertIn("Python Backend Lead", preview["subject"])
        self.assertIn("Jane Doe", preview["body"])
        self.assertEqual(preview["cv_filename"], TEST_CV)

    def test_mandatory_confirmation_enforcement(self):
        profile = {"candidate_name": "Jane"}
        preview = self.service.preview_application(self.vid, 1, profile, TEST_CV)

        # Calling without confirmation must fail
        with self.assertRaises(PermissionError):
            self.service.send_confirmed_application(preview, user_confirmed=False)

    def test_successful_confirmed_dispatch_and_recording(self):
        profile = {"candidate_name": "Jane Doe", "years_experience": "4"}
        preview = self.service.preview_application(self.vid, 1, profile, TEST_CV)

        # Dispatch with confirmation
        res = self.service.send_confirmed_application(preview, user_confirmed=True, dry_run=True)
        self.assertTrue(res["success"])
        self.assertIn("application_id", res)

        # Verify application recorded and vacancy marked Applied
        rep = self.service.get_applications_report()
        self.assertEqual(rep["total_applications"], 1)

        vacancies = self.service.list_vacancies(status="Applied")
        self.assertEqual(len(vacancies), 1)

    def test_missing_cv_file_error(self):
        profile = {"candidate_name": "Jane Doe"}
        with self.assertRaises(FileNotFoundError):
            self.service.preview_application(self.vid, 1, profile, cv_path="non_existent_file.pdf")


if __name__ == "__main__":
    unittest.main()
