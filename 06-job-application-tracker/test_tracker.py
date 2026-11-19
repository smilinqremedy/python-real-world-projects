"""
Automated Unit Tests for Job Application Tracker
Validates application creation, status updates, interview tracking, company searches,
funnel statistics, input validation, and JSON persistence.
"""

import os
import unittest
import tempfile
from datetime import datetime, timedelta
from tracker import (
    load_data,
    save_data,
    add_application,
    update_application_status,
    update_application_details,
    search_applications_by_company,
    get_upcoming_interviews,
    calculate_application_statistics,
    validate_date_string,
    find_application_by_id
)


class TestJobApplicationTracker(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for isolated test persistence
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.test_path = self.temp_file.name

        self.sample_data = {
            "applications": [
                {
                    "id": 1,
                    "company": "Google",
                    "job_title": "Software Engineer II",
                    "application_date": "2026-11-01",
                    "job_description": "Backend services",
                    "application_link": "https://careers.google.com/1",
                    "status": "Interview",
                    "interview_date": (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d 14:00"),
                    "notes": "Technical screening",
                    "created_at": "2026-11-01 10:00:00",
                    "updated_at": "2026-11-05 12:00:00"
                },
                {
                    "id": 2,
                    "company": "Microsoft",
                    "job_title": "Cloud Architect",
                    "application_date": "2026-11-02",
                    "job_description": "Azure cloud architecture",
                    "application_link": "https://careers.microsoft.com/2",
                    "status": "Applied",
                    "interview_date": None,
                    "notes": "Referred by alum",
                    "created_at": "2026-11-02 11:00:00",
                    "updated_at": "2026-11-02 11:00:00"
                },
                {
                    "id": 3,
                    "company": "Amazon",
                    "job_title": "SDE I",
                    "application_date": "2026-10-15",
                    "job_description": "AWS Lambda team",
                    "application_link": "https://amazon.jobs/3",
                    "status": "Offered",
                    "interview_date": "2026-10-28 10:00",
                    "notes": "Offer letter received",
                    "created_at": "2026-10-15 09:00:00",
                    "updated_at": "2026-11-03 16:00:00"
                },
                {
                    "id": 4,
                    "company": "Netflix",
                    "job_title": "Senior Data Engineer",
                    "application_date": "2026-10-01",
                    "job_description": "Streaming data pipeline",
                    "application_link": "https://jobs.netflix.com/4",
                    "status": "Rejected",
                    "interview_date": None,
                    "notes": "Position filled internally",
                    "created_at": "2026-10-01 14:00:00",
                    "updated_at": "2026-10-10 15:00:00"
                }
            ]
        }

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_save_and_load_persistence(self):
        """Test saving and loading data integrity."""
        self.assertTrue(save_data(self.sample_data, self.test_path))
        loaded = load_data(self.test_path)
        self.assertEqual(len(loaded["applications"]), 4)
        self.assertEqual(loaded["applications"][0]["company"], "Google")

    def test_corrupt_file_recovery(self):
        """Test system safely initializes empty applications when file is corrupted."""
        with open(self.test_path, "w") as f:
            f.write("corrupted json {[[")
        loaded = load_data(self.test_path)
        self.assertEqual(loaded, {"applications": []})

    def test_add_application(self):
        """Features 1-6: Add application with company, title, date, desc, link, status."""
        app = add_application(
            self.sample_data,
            company="Apple",
            job_title="iOS Developer",
            application_date="2026-11-10",
            job_description="Swift UI and CoreData",
            application_link="https://jobs.apple.com/5",
            status="Applied",
            file_path=self.test_path
        )
        self.assertEqual(app["id"], 5)
        self.assertEqual(app["company"], "Apple")
        self.assertEqual(app["status"], "Applied")
        self.assertEqual(len(self.sample_data["applications"]), 5)

    def test_validation_empty_fields_and_bad_dates(self):
        """Test validation rejects empty company or title and invalid dates."""
        with self.assertRaises(ValueError):
            add_application(self.sample_data, company="", job_title="Developer")
        with self.assertRaises(ValueError):
            add_application(self.sample_data, company="Meta", job_title="")
        with self.assertRaises(ValueError):
            validate_date_string("invalid-date-2026")
        with self.assertRaises(ValueError):
            add_application(self.sample_data, company="Meta", job_title="Dev", status="InvalidStatus")

    def test_update_application_status(self):
        """Features 7 & 8: Update status and record interview date."""
        inv_time = "2026-11-28 15:30"
        updated = update_application_status(
            self.sample_data,
            app_id=2,
            new_status="Interview",
            interview_date=inv_time,
            notes="Round 1 Technical Interview",
            file_path=self.test_path
        )
        self.assertEqual(updated["status"], "Interview")
        self.assertEqual(updated["interview_date"], inv_time)
        self.assertEqual(updated["notes"], "Round 1 Technical Interview")

    def test_search_applications_by_company(self):
        """Feature 9: Search applications by company name (case-insensitive substring)."""
        matches1 = search_applications_by_company(self.sample_data["applications"], "google")
        self.assertEqual(len(matches1), 1)
        self.assertEqual(matches1[0]["id"], 1)

        matches2 = search_applications_by_company(self.sample_data["applications"], "o")  # Google, Microsoft, Amazon
        self.assertEqual(len(matches2), 3)

        matches_empty = search_applications_by_company(self.sample_data["applications"], "NonExistentCompany")
        self.assertEqual(len(matches_empty), 0)

    def test_get_upcoming_interviews(self):
        """Feature 10: Display upcoming interviews sorted chronologically."""
        upcoming = get_upcoming_interviews(self.sample_data["applications"])
        self.assertEqual(len(upcoming), 1)
        self.assertEqual(upcoming[0]["company"], "Google")

    def test_calculate_application_statistics(self):
        """Features 11 & 12: Total applications and success statistics."""
        stats = calculate_application_statistics(self.sample_data["applications"])
        self.assertEqual(stats["total_applications"], 4)
        self.assertEqual(stats["status_counts"]["Applied"], 1)
        self.assertEqual(stats["status_counts"]["Interview"], 1)
        self.assertEqual(stats["status_counts"]["Offered"], 1)
        self.assertEqual(stats["status_counts"]["Rejected"], 1)

        # Interview rate: (Interview 1 + Offered 1) / 4 = 50.0%
        self.assertEqual(stats["interview_rate_pct"], 50.0)
        # Offer rate: 1 / 4 = 25.0%
        self.assertEqual(stats["offer_rate_pct"], 25.0)
        # Rejection rate: 1 / 4 = 25.0%
        self.assertEqual(stats["rejection_rate_pct"], 25.0)


if __name__ == "__main__":
    unittest.main()
