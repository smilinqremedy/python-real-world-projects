"""
Unit tests for CSV Data Cleaning & Validation Tool.
"""
import unittest
import os
import tempfile
import pandas as pd
from csv_cleaner import CSVCleaner


class TestCSVCleaner(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
            "name": ["  amara okonkwo  ", "CHIDI EZE", "bayo adeleke", "  amara okonkwo  ", "Ngozi Obi"],
            "email": ["Amara@Domain.COM", "invalid-email@", "bayo@company.ng", "Amara@Domain.COM", "ngozi@web.org"],
            "phone": ["08031234567", "+234 802 987 6543", "(0809) 111-2233", "08031234567", "invalid_phone"],
            "city": ["Lagos", "Abuja", None, "Lagos", "Port Harcourt"],
        }
        self.df = pd.DataFrame(self.sample_data)

    def test_duplicate_removal(self):
        cleaner = CSVCleaner(df=self.df)
        self.assertEqual(len(cleaner.df), 5)
        removed = cleaner.remove_duplicates()
        self.assertEqual(removed, 1)
        self.assertEqual(len(cleaner.df), 4)
        self.assertEqual(cleaner.get_quality_report()["duplicate_rows_removed"], 1)

    def test_missing_values_detection_and_filling(self):
        cleaner = CSVCleaner(df=self.df)
        missing = cleaner.detect_missing()
        self.assertEqual(missing["city"], 1)

        cleaner.handle_missing(fill_defaults={"city": "Unknown City"})
        self.assertEqual(cleaner.df["city"].isnull().sum(), 0)
        self.assertIn("Unknown City", cleaner.df["city"].values)

    def test_missing_values_drop_column(self):
        cleaner = CSVCleaner(df=self.df)
        cleaner.handle_missing(drop_columns=["city"])
        self.assertEqual(len(cleaner.df), 4)

    def test_text_normalization(self):
        cleaner = CSVCleaner(df=self.df)
        cleaner.normalize_text("name", casing="title", strip=True)
        self.assertEqual(cleaner.df["name"].iloc[0], "Amara Okonkwo")
        self.assertEqual(cleaner.df["name"].iloc[1], "Chidi Eze")
        self.assertEqual(cleaner.df["name"].iloc[2], "Bayo Adeleke")

    def test_email_validation_and_normalization(self):
        cleaner = CSVCleaner(df=self.df)
        res = cleaner.validate_and_normalize_emails("email")
        self.assertEqual(res["invalid_count"], 1)
        self.assertIn(1, res["invalid_indices"])  # 'invalid-email@'
        # Check lowercased
        self.assertEqual(cleaner.df["email"].iloc[0], "amara@domain.com")

    def test_phone_standardization(self):
        # Format checks
        self.assertEqual(CSVCleaner.format_phone_number("08031234567"), "+2348031234567")
        self.assertEqual(CSVCleaner.format_phone_number("+234 802 987 6543"), "+2348029876543")
        self.assertEqual(CSVCleaner.format_phone_number("(0809) 111-2233"), "+2348091112233")
        self.assertEqual(CSVCleaner.format_phone_number("2348031234567"), "+2348031234567")
        self.assertIsNone(CSVCleaner.format_phone_number("invalid_phone"))

        cleaner = CSVCleaner(df=self.df)
        res = cleaner.standardize_phones("phone")
        self.assertEqual(res["standardized_count"], 4)
        self.assertEqual(res["invalid_count"], 1)
        self.assertEqual(cleaner.df["phone"].iloc[0], "+2348031234567")

    def test_export_preserves_original(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_path = os.path.join(tmpdir, "original_data.csv")
            self.df.to_csv(orig_path, index=False)

            cleaner = CSVCleaner(filepath=orig_path)
            cleaner.run_standard_pipeline(fill_defaults={"city": "Lagos"})
            out_file = cleaner.export_cleaned()

            # Ensure original still exists and output has different name
            self.assertTrue(os.path.exists(orig_path))
            self.assertTrue(os.path.exists(out_file))
            self.assertNotEqual(os.path.abspath(orig_path), os.path.abspath(out_file))

            cleaned_df = pd.read_csv(out_file)
            self.assertEqual(len(cleaned_df), 4)  # 1 duplicate dropped

    def test_complete_pipeline_and_report(self):
        cleaner = CSVCleaner(df=self.df)
        report = cleaner.run_standard_pipeline(fill_defaults={"city": "Lagos"})
        self.assertEqual(report["duplicate_rows_removed"], 1)
        self.assertEqual(report["invalid_emails_count"], 1)
        self.assertEqual(report["invalid_phones_count"], 1)
        self.assertEqual(report["final_rows"], 4)


if __name__ == "__main__":
    unittest.main()
