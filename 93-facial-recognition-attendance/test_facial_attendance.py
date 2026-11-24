"""
Automated unit and integration tests for AI-Powered Facial Recognition Attendance System.
"""
import unittest
import os
import shutil
import tempfile
import numpy as np
from PIL import Image, ImageDraw

from auth import hash_password, verify_password
from biometrics import (
    extract_face_embedding,
    compute_cosine_similarity,
    match_embedding_against_gallery,
    BiometricConsentError
)
import database
from attendance_service import AttendanceService
from reporter import AttendanceReporter


class TestFacialRecognitionAttendance(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_attendance.db")
        self.service = AttendanceService(db_path=self.db_path)
        self.reporter = AttendanceReporter(db_path=self.db_path)

        # Create two distinct synthetic face images
        self.face_alice = Image.new("RGB", (96, 96), color=(220, 200, 180))
        d_a = ImageDraw.Draw(self.face_alice)
        d_a.ellipse([24, 24, 40, 36], fill=(50, 40, 30))  # Left eye
        d_a.ellipse([56, 24, 72, 36], fill=(50, 40, 30))  # Right eye
        d_a.line([(48, 40), (48, 56)], fill=(120, 90, 80), width=3)  # Nose
        d_a.arc([32, 60, 64, 76], start=0, end=180, fill=(180, 50, 50), width=3)  # Mouth

        self.face_bob = Image.new("RGB", (96, 96), color=(180, 160, 140))
        d_b = ImageDraw.Draw(self.face_bob)
        d_b.rectangle([20, 20, 44, 32], fill=(20, 20, 20))  # Glasses left
        d_b.rectangle([52, 20, 76, 32], fill=(20, 20, 20))  # Glasses right
        d_b.line([(48, 38), (48, 62)], fill=(90, 60, 50), width=4)
        d_b.line([(30, 70), (66, 70)], fill=(150, 40, 40), width=4)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_auth_hashing_and_verification(self):
        pwd = "SecurePassword@123"
        h, salt = hash_password(pwd)
        self.assertTrue(verify_password(pwd, h, salt))
        self.assertFalse(verify_password("WrongPassword", h, salt))

    def test_biometric_embedding_extraction_and_matching(self):
        emb_a1 = extract_face_embedding(self.face_alice)
        emb_a2 = extract_face_embedding(self.face_alice)  # Same image
        emb_b = extract_face_embedding(self.face_bob)     # Different person

        self.assertEqual(len(emb_a1), 128)
        # Cosine similarity with self must be 1.0
        self.assertAlmostEqual(compute_cosine_similarity(emb_a1, emb_a2), 1.0, places=4)

        # Similarity between Alice and Bob should be lower than identical match
        sim_ab = compute_cosine_similarity(emb_a1, emb_b)
        self.assertLess(sim_ab, 0.99)

        gallery = [(1, "Alice", emb_a1), (2, "Bob", emb_b)]
        match = match_embedding_against_gallery(emb_a2, gallery, similarity_threshold=0.85)
        self.assertIsNotNone(match)
        self.assertEqual(match[0], 1)
        self.assertEqual(match[1], "Alice")

    def test_participant_registration_and_consent_enforcement(self):
        # 1. Attempt registration WITHOUT consent must raise BiometricConsentError
        with self.assertRaises(BiometricConsentError):
            self.service.register_participant(
                employee_id="EMP-001",
                full_name="Alice",
                department="R&D",
                email="alice@example.com",
                consent_granted=False,
                opt_in_biometrics=True,
                face_image=self.face_alice
            )

        # 2. Registration WITH consent and biometric opt-in
        res = self.service.register_participant(
            employee_id="EMP-001",
            full_name="Alice",
            department="R&D",
            email="alice@example.com",
            consent_granted=True,
            opt_in_biometrics=True,
            face_image=self.face_alice
        )
        self.assertTrue(res["success"])

        # 3. Registration WITH consent but OPTING OUT of biometrics (Manual alternative)
        res_bob = self.service.register_participant(
            employee_id="EMP-002",
            full_name="Bob",
            department="Sales",
            email="bob@example.com",
            consent_granted=True,
            opt_in_biometrics=False,
            face_image=None
        )
        self.assertTrue(res_bob["success"])

    def test_duplicate_prevention_and_attendance_recording(self):
        self.service.register_participant(
            employee_id="EMP-001",
            full_name="Alice",
            department="R&D",
            email="alice@example.com",
            consent_granted=True,
            opt_in_biometrics=True,
            face_image=self.face_alice
        )

        session_code = "SESSION_TEST_01"
        self.service.create_session(session_code, "Morning Session", "2026-11-24", "admin")

        # First check-in: Should succeed
        res1 = self.service.record_attendance_by_face(session_code, self.face_alice, actor="kiosk")
        self.assertTrue(res1["success"])
        self.assertEqual(res1["participant_name"], "Alice")
        self.assertEqual(res1["method"], "facial_biometric")

        # Second check-in in same session: MUST be rejected as duplicate
        res2 = self.service.record_attendance_by_face(session_code, self.face_alice, actor="kiosk")
        self.assertFalse(res2["success"])
        self.assertIn("Duplicate attendance", res2["error"])

    def test_manual_alternative_and_admin_correction(self):
        self.service.register_participant(
            employee_id="EMP-002",
            full_name="Bob",
            department="Sales",
            email="bob@example.com",
            consent_granted=True,
            opt_in_biometrics=False
        )

        session_code = "SESSION_TEST_02"
        self.service.create_session(session_code, "Afternoon Session", "2026-11-24", "admin")

        # Manual check-in
        res = self.service.record_attendance_manual(session_code, "EMP-002", "admin", "Opted out of biometrics")
        self.assertTrue(res["success"])
        self.assertEqual(res["method"], "manual_alternative")
        rec_id = res["record_id"]

        # Admin correction with valid justification
        ok = self.service.correct_attendance_record(rec_id, "excused", "Authorized medical appointment", "admin")
        self.assertTrue(ok)

        # Correction without justification should fail
        with self.assertRaises(ValueError):
            self.service.correct_attendance_record(rec_id, "present", "", "admin")

    def test_reporter_and_csv_export(self):
        self.service.register_participant("EMP-001", "Alice", "R&D", "alice@test.com", True, True, self.face_alice)
        self.service.create_session("SESSION_REP", "Report Session", "2026-11-24", "admin")
        self.service.record_attendance_by_face("SESSION_REP", self.face_alice)

        records = self.reporter.get_session_attendance("SESSION_REP")
        self.assertEqual(len(records), 1)

        csv_text = self.reporter.export_to_csv(records)
        self.assertIn("EMP-001", csv_text)
        self.assertIn("Alice", csv_text)
        self.assertIn("facial_biometric", csv_text)

        period_rep = self.reporter.generate_report_by_period("2026-11-01", "2026-11-30")
        self.assertEqual(period_rep["total_check_ins"], 1)
        self.assertEqual(period_rep["biometric_check_ins"], 1)


if __name__ == "__main__":
    unittest.main()
