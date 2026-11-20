"""
Unit tests for Personal Password Security Audit Tool.
"""
import unittest
from password_auditor import PasswordSecurityAuditor


class TestPasswordAuditor(unittest.TestCase):
    def test_empty_password(self):
        rep = PasswordSecurityAuditor.audit("")
        self.assertEqual(rep.length, 0)
        self.assertEqual(rep.strength_score, 0)
        self.assertEqual(rep.rating, "Very Weak")

    def test_common_weak_passwords(self):
        rep = PasswordSecurityAuditor.audit("password123")
        self.assertTrue(rep.is_common_weak)
        self.assertLessEqual(rep.strength_score, 25)

    def test_sequential_patterns(self):
        rep = PasswordSecurityAuditor.audit("qwerty123456")
        self.assertGreaterEqual(len(rep.detected_sequences), 1)
        self.assertTrue(any("123456" in s or "qwerty" in s for s in rep.detected_sequences))

    def test_repeated_characters(self):
        rep = PasswordSecurityAuditor.audit("aaaaabbbbb")
        self.assertTrue(rep.has_repeated_characters)

    def test_character_diversity(self):
        rep = PasswordSecurityAuditor.audit("Abc1!")
        self.assertTrue(rep.has_lowercase)
        self.assertTrue(rep.has_uppercase)
        self.assertTrue(rep.has_digits)
        self.assertTrue(rep.has_symbols)
        self.assertEqual(rep.character_set_size, 26 + 26 + 10 + 33)

    def test_strong_complex_password(self):
        rep = PasswordSecurityAuditor.audit("X#8kL$9pW!2mQ@4z")
        self.assertGreaterEqual(rep.strength_score, 75)
        self.assertIn(rep.rating, ("Strong", "Very Strong"))
        self.assertFalse(rep.is_common_weak)
        self.assertFalse(rep.has_repeated_characters)
        self.assertGreaterEqual(rep.estimated_entropy_bits, 80.0)

    def test_diceware_passphrase(self):
        rep = PasswordSecurityAuditor.audit("correct-horse-battery-staple")
        self.assertGreaterEqual(rep.length, 25)
        self.assertGreaterEqual(rep.strength_score, 70)


if __name__ == "__main__":
    unittest.main()
