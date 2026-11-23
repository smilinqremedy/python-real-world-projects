"""
Unit Tests for Email Spam Classification System.
"""
import unittest
import os
from dataset import generate_spam_dataset
from preprocessor import clean_text, extract_spam_keywords
from model_trainer import SpamModelTrainer
from classifier import SpamClassifierService
import database


class TestSpamClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_spam.db"
        cls.test_csv = "test_spam.csv"
        cls.df = generate_spam_dataset(n_samples=400, seed=101, output_csv=cls.test_csv)
        cls.trainer = SpamModelTrainer()
        cls.results = cls.trainer.train_and_compare(cls.df)
        cls.service = SpamClassifierService(trainer=cls.trainer, db_path=cls.test_db)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.test_db, cls.test_csv, "spam_dataset.csv", "spam_scans.db"]:
            if os.path.exists(f):
                os.remove(f)

    def test_text_cleaning(self):
        raw = "Hello! Win $5,000 at https://free-cash.xyz immediately!!"
        cleaned = clean_text(raw)
        self.assertNotIn("https://", cleaned)
        self.assertIn("urltoken", cleaned)
        self.assertIn("moneytoken", cleaned)
        self.assertNotIn("!", cleaned)

    def test_keyword_extraction(self):
        text = "URGENT: Claim your lottery prize and Bitcoin wire transfer today!"
        kw = extract_spam_keywords(text)
        self.assertIn("urgent", kw)
        self.assertIn("lottery", kw)
        self.assertIn("bitcoin", kw)
        self.assertIn("wire", kw)

    def test_model_training_and_metrics(self):
        metrics = self.results["model_metrics"]
        self.assertIn("Multinomial Naive Bayes", metrics)
        self.assertIn("Logistic Regression", metrics)
        for name, m in metrics.items():
            self.assertGreater(m["accuracy"], 0.85)
            self.assertGreater(m["f1_score"], 0.80)

    def test_spam_detection(self):
        spam_msg = "Exclusive lottery winner! Claim your $50,000 cash wire transfer now with no fees."
        res = self.service.classify_email(spam_msg, subject="WINNER NOTICE", persist=True)
        self.assertTrue(res["is_spam"])
        self.assertEqual(res["classification"], "SPAM")
        self.assertGreater(res["spam_probability"], 0.50)

    def test_ham_detection(self):
        ham_msg = "Hi Sarah, please find the quarterly financial budget attached for our review meeting tomorrow at 10 AM."
        res = self.service.classify_email(ham_msg, subject="Budget Review", persist=True)
        self.assertFalse(res["is_spam"])
        self.assertEqual(res["classification"], "HAM (Legitimate)")
        self.assertLess(res["spam_probability"], 0.50)

    def test_database_persistence(self):
        database.save_scan(
            subject="Test Subject 1",
            body="Test body sample message 1",
            is_spam=True,
            spam_probability=0.92,
            flagged_keywords=["urgent", "prize"],
            db_path=self.test_db
        )
        database.save_scan(
            subject="Test Subject 2",
            body="Test body sample message 2",
            is_spam=False,
            spam_probability=0.08,
            flagged_keywords=[],
            db_path=self.test_db
        )
        history = database.get_scan_history(self.test_db)
        self.assertGreaterEqual(len(history), 2)
        stats = database.get_scan_stats(self.test_db)
        self.assertGreaterEqual(stats["total_scanned"], 2)


if __name__ == "__main__":
    unittest.main()
