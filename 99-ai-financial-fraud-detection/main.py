"""
Command-Line Interface for AI Financial Fraud Detection System.
"""
import argparse
import sys
import os
import csv
import json
import numpy as np

from dataset import generate_synthetic_transactions, robust_scale
from models import SupervisedFraudClassifier, IsolationForestAnomalyDetector, calculate_risk_score
from evaluator import evaluate_fraud_model
import database


def main():
    parser = argparse.ArgumentParser(description="AI Financial Fraud Detection System")
    parser.add_argument("--generate-data", type=str, help="Generate synthetic transaction CSV file")
    parser.add_argument("--n-samples", type=int, default=1000, help="Number of transaction samples")
    parser.add_argument("--fraud-ratio", type=float, default=0.03, help="Proportion of fraudulent transactions")
    parser.add_argument("--train-eval", action="store_true", help="Train and benchmark fraud detection models")
    parser.add_argument("--score-csv", type=str, help="Score transactions in a CSV file and export results")
    parser.add_argument("--output-report", type=str, default="fraud_risk_report.csv", help="Output report CSV")

    args = parser.parse_args()

    if args.generate_data:
        print(f"Generating {args.n_samples} transactions (fraud ratio: {args.fraud_ratio * 100:.1f}%)...")
        generate_synthetic_transactions(output_csv=args.generate_data, n_samples=args.n_samples, fraud_ratio=args.fraud_ratio)
        print(f"Dataset saved to: {args.generate_data}")
        return

    if args.train_eval:
        print("Generating benchmark dataset...")
        X, y, _ = generate_synthetic_transactions(n_samples=1200, fraud_ratio=0.03, seed=42)
        X_scaled, medians, iqrs = robust_scale(X)

        from dataset import stratified_split
        X_tr, y_tr, X_te, y_te = stratified_split(X_scaled, y, test_ratio=0.25)
        print(f"Train split: {len(y_tr)} (Fraud={np.sum(y_tr)}), Test split: {len(y_te)} (Fraud={np.sum(y_te)})")

        print("Training Weighted Supervised Classifier...")
        clf = SupervisedFraudClassifier(fraud_weight=25.0)
        clf.train(X_tr, y_tr, epochs=20)

        print("Fitting Unsupervised Isolation Forest Anomaly Detector...")
        iso = IsolationForestAnomalyDetector(n_trees=20)
        iso.fit(X_tr)

        test_probs = clf.forward(X_te)
        metrics = evaluate_fraud_model(y_te, test_probs, threshold=0.50)

        print("\n" + "=" * 60)
        print("MODEL PERFORMANCE ON IMBALANCED TEST SPLIT:")
        print("=" * 60)
        print(f"Accuracy (Baseline): {metrics['accuracy'] * 100:.2f}%")
        print(f"PR-AUC (Primary Imbalance Metric): {metrics['pr_auc'] * 100:.2f}%")
        print(f"ROC-AUC: {metrics['roc_auc'] * 100:.2f}%")
        print(f"Fraud Recall (Sensitivity): {metrics['recall'] * 100:.2f}%")
        print(f"Precision: {metrics['precision'] * 100:.2f}%")
        print(f"F1-Score: {metrics['f1_score'] * 100:.2f}%")
        print("\nConfusion Matrix [ [TN, FP], [FN, TP] ]:")
        print(f"  True Negatives: {metrics['true_negatives_legit_cleared']}")
        print(f"  False Positives (Customer Friction): {metrics['false_positives_customer_friction']}")
        print(f"  False Negatives (Missed Fraud): {metrics['false_negatives_missed_fraud']}")
        print(f"  True Positives (Caught Fraud): {metrics['true_positives_detected']}")
        return

    if args.score_csv:
        if not os.path.exists(args.score_csv):
            print(f"File not found: {args.score_csv}", file=sys.stderr)
            sys.exit(1)

        # Quick calibration
        X_calib, y_calib, _ = generate_synthetic_transactions(n_samples=800, fraud_ratio=0.03)
        X_sc, medians, iqrs = robust_scale(X_calib)
        clf = SupervisedFraudClassifier()
        clf.train(X_sc, y_calib, epochs=15)
        iso = IsolationForestAnomalyDetector()
        iso.fit(X_sc)

        results = []
        with open(args.score_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tid = row["transaction_id"]
                amt = float(row["amount"])
                vec = np.array([
                    amt, float(row["time_step"]), float(row["v1"]), float(row["v2"]),
                    float(row["v3"]), float(row["v4"]), float(row["v5"]), float(row["v6"]),
                    float(row["v7"]), float(row["v8"])
                ], dtype=np.float32)

                scaled = (vec - medians) / iqrs
                prob = float(clf.forward(np.expand_dims(scaled, axis=0))[0])
                anom = float(iso.score_anomalies(np.expand_dims(scaled, axis=0))[0])
                score, tier, action = calculate_risk_score(prob, anom)

                database.log_transaction_risk(tid, amt, prob, anom, score, tier)
                results.append([tid, amt, round(score, 1), tier, action])

        with open(args.output_report, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.writer(out_f)
            writer.writerow(["Transaction ID", "Amount ($)", "Risk Score (0-100)", "Risk Tier", "Recommended Action"])
            writer.writerows(results)

        print(f"Scored {len(results)} transactions. Output report saved to: {args.output_report}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
