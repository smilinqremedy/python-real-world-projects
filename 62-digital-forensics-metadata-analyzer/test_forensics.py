"""
Automated unit tests for Digital Forensics File Metadata Analyzer.
"""
import unittest
import os
import tempfile
import hashlib
from forensics_analyzer import ForensicsAnalyzer


class TestForensicsAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.analyzer = ForensicsAnalyzer(self.db_path)

        self.evidence_dir = tempfile.TemporaryDirectory()
        self.base_path = self.evidence_dir.name

        # Create sample evidence files
        self.file1 = os.path.join(self.base_path, "confidential_memo.txt")
        with open(self.file1, "wb") as f:
            f.write(b"Strictly confidential internal audit findings.")

        # Exact copy of file1 with different name (duplicate)
        self.file2 = os.path.join(self.base_path, "memo_copy.txt")
        with open(self.file2, "wb") as f:
            f.write(b"Strictly confidential internal audit findings.")

        # Suspicious double extension
        self.file_suspicious = os.path.join(self.base_path, "urgent_invoice.pdf.exe")
        with open(self.file_suspicious, "wb") as f:
            f.write(b"MZ\x90\x00\x03\x00\x00\x00")

    def tearDown(self):
        self.evidence_dir.cleanup()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_metadata_extraction_and_hashing(self):
        item = self.analyzer.analyze_file(self.file1)
        expected_sha = hashlib.sha256(b"Strictly confidential internal audit findings.").hexdigest()
        self.assertEqual(item["sha256"], expected_sha)
        self.assertEqual(item["size_bytes"], len(b"Strictly confidential internal audit findings."))
        self.assertEqual(item["filename"], "confidential_memo.txt")
        self.assertIn("modified_time", item)

    def test_duplicate_file_detection(self):
        scan_result = self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-001")
        self.assertEqual(scan_result["total_files_analyzed"], 3)
        self.assertEqual(scan_result["duplicate_files_found"], 1)

        duplicates = [e for e in scan_result["evidence_items"] if e["is_duplicate"]]
        self.assertEqual(len(duplicates), 2)
        self.assertEqual(duplicates[0]["sha256"], duplicates[1]["sha256"])

    def test_suspicious_double_extension_detection(self):
        scan_result = self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-002")
        suspicious_items = [e for e in scan_result["evidence_items"] if "urgent_invoice.pdf.exe" in e["filename"]]
        self.assertEqual(len(suspicious_items), 1)
        self.assertTrue(any("double extension" in flag for flag in suspicious_items[0]["suspicious_flags"]))

    def test_evidence_integrity_verification_intact(self):
        self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-003")
        verify_result = self.analyzer.verify_case_integrity("CASE-2026-003")
        self.assertTrue(verify_result["is_evidence_intact"])
        self.assertEqual(verify_result["modified_count"], 0)
        self.assertEqual(verify_result["missing_count"], 0)
        self.assertEqual(verify_result["intact_count"], 3)

    def test_evidence_integrity_verification_tampered(self):
        self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-004")

        # Tamper with file1
        with open(self.file1, "ab") as f:
            f.write(b"\nTampered modification by adversary.")

        verify_result = self.analyzer.verify_case_integrity("CASE-2026-004")
        self.assertFalse(verify_result["is_evidence_intact"])
        self.assertEqual(verify_result["modified_count"], 1)
        self.assertEqual(verify_result["modified_files"][0]["file"], "confidential_memo.txt")

    def test_evidence_integrity_verification_missing(self):
        self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-005")

        # Delete file2
        os.remove(self.file2)

        verify_result = self.analyzer.verify_case_integrity("CASE-2026-005")
        self.assertFalse(verify_result["is_evidence_intact"])
        self.assertEqual(verify_result["missing_count"], 1)
        self.assertEqual(verify_result["missing_files"][0]["file"], "memo_copy.txt")

    def test_export_report(self):
        self.analyzer.scan_directory(self.base_path, case_number="CASE-2026-006")
        out_file = os.path.join(self.base_path, "case_report.json")
        saved = self.analyzer.export_report("CASE-2026-006", output_path=out_file)
        self.assertTrue(os.path.exists(saved))
        self.assertGreater(os.path.getsize(saved), 100)


if __name__ == "__main__":
    unittest.main()
