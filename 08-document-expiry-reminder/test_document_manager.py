"""
Automated Unit Tests for Personal Document Expiry Reminder System
Validates document registration, date parsing, day calculations, status evaluations,
upcoming/expired filtering, document updates, and expiry reports.
"""

import os
import unittest
import tempfile
from datetime import date, timedelta
from document_manager import (
    load_data,
    save_data,
    register_document,
    update_document,
    delete_document,
    calculate_days_remaining,
    evaluate_document_status,
    get_expired_documents,
    get_documents_expiring_within,
    search_documents,
    generate_expiry_report_data,
    parse_date,
    find_document_by_id
)


class TestDocumentExpiryReminder(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for isolated test persistence
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.test_path = self.temp_file.name

        self.fixed_today = date(2026, 11, 19)

        # Build sample documents relative to fixed_today
        self.sample_data = {
            "documents": [
                {
                    "id": 1,
                    "name": "International Passport",
                    "category": "Travel",
                    "document_number": "A12345678",
                    "issue_date": "2017-06-15",
                    "expiry_date": (self.fixed_today + timedelta(days=500)).strftime("%Y-%m-%d"),
                    "issuing_authority": "Immigration Bureau",
                    "notes": "10-year e-Passport",
                    "created_at": "2026-11-01 10:00:00",
                    "updated_at": "2026-11-01 10:00:00"
                },
                {
                    "id": 2,
                    "name": "Vehicle Insurance",
                    "category": "Vehicle",
                    "document_number": "POL-9988",
                    "issue_date": "2025-11-23",
                    "expiry_date": (self.fixed_today + timedelta(days=4)).strftime("%Y-%m-%d"), # Critical <= 7d
                    "issuing_authority": "Alliance Insurance",
                    "notes": "Comprehensive coverage",
                    "created_at": "2026-11-01 10:00:00",
                    "updated_at": "2026-11-01 10:00:00"
                },
                {
                    "id": 3,
                    "name": "Driver's License",
                    "category": "Identification",
                    "document_number": "DL-4455",
                    "issue_date": "2022-12-10",
                    "expiry_date": (self.fixed_today + timedelta(days=21)).strftime("%Y-%m-%d"), # Expiring soon <= 30d
                    "issuing_authority": "DMV",
                    "notes": "Class C",
                    "created_at": "2026-11-01 10:00:00",
                    "updated_at": "2026-11-01 10:00:00"
                },
                {
                    "id": 4,
                    "name": "National Health Insurance",
                    "category": "Health & Insurance",
                    "document_number": "NHI-1122",
                    "issue_date": "2024-10-01",
                    "expiry_date": (self.fixed_today - timedelta(days=15)).strftime("%Y-%m-%d"), # Expired 15 days ago
                    "issuing_authority": "Ministry of Health",
                    "notes": "Annual card",
                    "created_at": "2026-11-01 10:00:00",
                    "updated_at": "2026-11-01 10:00:00"
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
        self.assertEqual(len(loaded["documents"]), 4)
        self.assertEqual(loaded["documents"][0]["name"], "International Passport")

    def test_corrupt_file_recovery(self):
        """Test safe recovery when JSON file is corrupted."""
        with open(self.test_path, "w") as f:
            f.write("invalid json content [[[")
        loaded = load_data(self.test_path)
        self.assertEqual(loaded, {"documents": []})

    def test_register_document(self):
        """Features 1-4: Register document with name, category, issue & expiry dates."""
        doc = register_document(
            self.sample_data,
            name="Scuba Diving Certification",
            category="Professional & Certifications",
            issue_date_str="2020-05-10",
            expiry_date_str="2028-05-10",
            document_number="PADI-9900",
            file_path=self.test_path
        )
        self.assertEqual(doc["id"], 5)
        self.assertEqual(doc["name"], "Scuba Diving Certification")
        self.assertEqual(len(self.sample_data["documents"]), 5)

    def test_date_validation_and_chronology(self):
        """Test validation rejects invalid dates and when expiry is before or on issue date."""
        with self.assertRaises(ValueError):
            parse_date("not-a-valid-date")
        with self.assertRaises(ValueError):
            # Expiry date before issue date
            register_document(self.sample_data, "Bad Doc", "Other", "2026-10-10", "2025-10-10")
        with self.assertRaises(ValueError):
            # Empty name
            register_document(self.sample_data, "", "Other", "2025-01-01", "2026-01-01")

    def test_days_remaining_and_status_evaluation(self):
        """Feature 5: Calculate days remaining and evaluate status tags."""
        # Expired document (15 days ago)
        exp_days = calculate_days_remaining((self.fixed_today - timedelta(days=15)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(exp_days, -15)
        eval_exp = evaluate_document_status((self.fixed_today - timedelta(days=15)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(eval_exp["status"], "EXPIRED")

        # Critical document (4 days left)
        crit_days = calculate_days_remaining((self.fixed_today + timedelta(days=4)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(crit_days, 4)
        eval_crit = evaluate_document_status((self.fixed_today + timedelta(days=4)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(eval_crit["status"], "CRITICAL")

        # Expiring soon (21 days left)
        eval_soon = evaluate_document_status((self.fixed_today + timedelta(days=21)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(eval_soon["status"], "EXPIRING_SOON")

        # Healthy (500 days left)
        eval_valid = evaluate_document_status((self.fixed_today + timedelta(days=500)).strftime("%Y-%m-%d"), self.fixed_today)
        self.assertEqual(eval_valid["status"], "VALID")

    def test_identify_expired_documents(self):
        """Feature 6: Identify expired documents."""
        expired = get_expired_documents(self.sample_data["documents"], reference_date=self.fixed_today)
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]["name"], "National Health Insurance")
        self.assertEqual(expired[0]["days_remaining"], -15)

    def test_documents_expiring_within_7_and_30_days(self):
        """Features 7 & 8: Filter documents expiring within 7 days and 30 days."""
        # Within 7 days
        critical_7d = get_documents_expiring_within(self.sample_data["documents"], max_days=7, reference_date=self.fixed_today)
        self.assertEqual(len(critical_7d), 1)
        self.assertEqual(critical_7d[0]["name"], "Vehicle Insurance")

        # Within 30 days (Includes Vehicle Insurance at 4d and Driver's License at 21d)
        expiring_30d = get_documents_expiring_within(self.sample_data["documents"], max_days=30, reference_date=self.fixed_today)
        self.assertEqual(len(expiring_30d), 2)
        self.assertEqual(expiring_30d[0]["name"], "Vehicle Insurance") # sorted most urgent first
        self.assertEqual(expiring_30d[1]["name"], "Driver's License")

    def test_update_document_information(self):
        """Feature 9: Update document information."""
        new_exp = (self.fixed_today + timedelta(days=365)).strftime("%Y-%m-%d")
        updated = update_document(
            self.sample_data,
            doc_id=4,
            name="Renewed National Health Insurance",
            expiry_date_str=new_exp,
            notes="Renewed via online portal",
            file_path=self.test_path
        )
        self.assertEqual(updated["name"], "Renewed National Health Insurance")
        self.assertEqual(updated["expiry_date"], new_exp)
        self.assertEqual(updated["notes"], "Renewed via online portal")

    def test_generate_expiry_reports(self):
        """Feature 10: Generate expiry audit reports."""
        rep = generate_expiry_report_data(self.sample_data["documents"], reference_date=self.fixed_today)
        self.assertEqual(rep["total_documents"], 4)
        self.assertEqual(rep["counts"]["expired"], 1)
        self.assertEqual(rep["counts"]["critical_7d"], 1)
        self.assertEqual(rep["counts"]["expiring_30d"], 1)
        self.assertEqual(rep["counts"]["valid"], 1)
        self.assertEqual(len(rep["category_counts"]), 4)


if __name__ == "__main__":
    unittest.main()
