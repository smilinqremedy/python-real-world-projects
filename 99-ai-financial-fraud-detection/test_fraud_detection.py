"""
Automated unit tests for AI Financial Fraud Detection System.
"""
import unittest
import os
import shutil
import tempfile
import numpy as np

from dataset import (
    generate_synthetic_transactions,
    robust_scale,
    stratified_split,
    FEATURE_NAMES
)
from models import (
    SupervisedFraudClassifier,
    IsolationForestAnomalyDetector,
    calculate_risk_score
)
from evaluator import evaluate_fraud_model, compute_pr_auc, compute_roc_auc
import database


class TestFinancialFraudDetection(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_fraud.db")

        # Generate mini synthetic dataset
        self.X, self.y, self.tx_ids = generate_synthetic_transactions(
            output_csv=None,
            n_samples=400,
            fraud_ratio=0.04,
            seed=42
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_synthetic_transactions_and_imbalance(self):
        self.assertEqual(len(self.X), 400)
        self.assertEqual(self.X.shape[1], 10)
        self.assertEqual(len(self.y), 400)

        # Imbalance check
        n_fraud = int(np.sum(self.y))
        self.assertEqual(n_fraud, 16)  # 4% of 400
        self.assertLess(n_fraud / len(self.y), 0.05)

    def test_robust_scaling(self):
        X_scaled, medians, iqrs = robust_scale(self.X)
        self.assertEqual(X_scaled.shape, self.X.shape)
        # Median of scaled data should be approximately 0.0
        np.testing.assert_allclose(np.median(X_scaled, axis=0), 0.0, atol=1e-5)

    def test_stratified_split(self):
        X_tr, y_tr, X_te, y_te = stratified_split(self.X, self.y, test_ratio=0.25, seed=42)
        self.assertEqual(len(y_tr) + len(y_te), 400)

        # Both train and test splits must contain positive fraud cases
        self.assertGreater(np.sum(y_tr), 0)
        self.assertGreater(np.sum(y_te), 0)
        self.assertAlmostEqual(np.mean(y_tr), np.mean(y_te), delta=0.02)

    def test_supervised_classifier_training(self):
        X_scaled, _, _ = robust_scale(self.X)
        clf = SupervisedFraudClassifier(input_dim=10, fraud_weight=15.0)
        clf.train(X_scaled, self.y, epochs=10)

        probs = clf.forward(X_scaled[:5])
        self.assertEqual(len(probs), 5)
        self.assertTrue(np.all(probs >= 0.0))
        self.assertTrue(np.all(probs <= 1.0))

    def test_isolation_forest_anomaly_detection(self):
        X_scaled, _, _ = robust_scale(self.X)
        iso = IsolationForestAnomalyDetector(n_trees=10, max_depth=6)
        iso.fit(X_scaled)

        scores = iso.score_anomalies(X_scaled[:10])
        self.assertEqual(len(scores), 10)
        self.assertTrue(np.all(scores >= 0.0))
        self.assertTrue(np.all(scores <= 1.0))

    def test_risk_scoring_and_tiers(self):
        # Low risk
        score1, tier1, action1 = calculate_risk_score(0.05, 0.1)
        self.assertLessEqual(score1, 30.0)
        self.assertEqual(tier1, "LOW")
        self.assertIn("Approve", action1)

        # Moderate risk
        score2, tier2, action2 = calculate_risk_score(0.50, 0.50)
        self.assertEqual(tier2, "MODERATE")
        self.assertIn("MFA", action2)

        # High risk
        score3, tier3, action3 = calculate_risk_score(0.95, 0.90)
        self.assertGreaterEqual(score3, 71.0)
        self.assertEqual(tier3, "HIGH")
        self.assertIn("Analyst Review", action3)

    def test_evaluator_metrics_pr_auc_and_roc_auc(self):
        y_true = np.array([0] * 95 + [1] * 5)
        # High scores for fraud
        y_scores = np.concatenate([np.random.uniform(0.01, 0.2, 95), np.random.uniform(0.7, 0.99, 5)])

        metrics = evaluate_fraud_model(y_true, y_scores, threshold=0.5)
        self.assertIn("pr_auc", metrics)
        self.assertIn("roc_auc", metrics)
        self.assertIn("confusion_matrix", metrics)

        self.assertGreaterEqual(metrics["roc_auc"], 0.8)
        self.assertGreaterEqual(metrics["pr_auc"], 0.7)

    def test_database_logging_and_analyst_review(self):
        log_id = database.log_transaction_risk(
            transaction_id="TXN-TEST-001",
            amount=3200.0,
            supervised_prob=0.92,
            anomaly_score=0.88,
            risk_score=90.5,
            risk_tier="HIGH",
            db_path=self.db_path
        )
        self.assertGreater(log_id, 0)

        flagged = database.get_transactions_by_status("flagged", db_path=self.db_path)
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["transaction_id"], "TXN-TEST-001")

        # Update analyst disposition
        updated = database.update_analyst_disposition(
            transaction_id="TXN-TEST-001",
            disposition="confirmed_fraud",
            notes="Unauthorized foreign IP velocity spike",
            db_path=self.db_path
        )
        self.assertTrue(updated)

        confirmed = database.get_transactions_by_status("confirmed_fraud", db_path=self.db_path)
        self.assertEqual(len(confirmed), 1)
        self.assertEqual(confirmed[0]["analyst_notes"], "Unauthorized foreign IP velocity spike")


if __name__ == "__main__":
    unittest.main()
