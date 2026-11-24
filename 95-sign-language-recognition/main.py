"""
Command-Line Interface for Sign Language Recognition System.
"""
import argparse
import sys
import os
import json
import numpy as np
from sign_dictionary import SIGN_DICTIONARY, SUPPORTED_SIGNS, ETHICAL_LINGUISTIC_DISCLAIMER
from hand_detector import (
    get_canonical_sign_landmarks,
    normalize_landmarks,
    generate_landmark_dataset
)
from classifier import SignClassifier
from evaluator import SignEvaluator


def main():
    parser = argparse.ArgumentParser(description="AI Sign Language Recognition System")
    parser.add_argument("--list-signs", action="store_true", help="List supported sign dictionary")
    parser.add_argument("--train", action="store_true", help="Train landmark classification model")
    parser.add_argument("--epochs", type=int, default=15, help="Training epochs")
    parser.add_argument("--weights-out", type=str, default="sign_model_weights.npz", help="Weights save path")
    parser.add_argument("--weights", type=str, default="sign_model_weights.npz", help="Weights path")
    parser.add_argument("--evaluate", action="store_true", help="Evaluate model accuracy on synthetic test split")
    parser.add_argument("--predict-sign", type=str, choices=SUPPORTED_SIGNS, help="Predict on canonical sign")

    args = parser.parse_args()

    if args.list_signs:
        print("Supported Sign Dictionary:")
        for name, data in SIGN_DICTIONARY.items():
            print(f"[{data['class_id']}] {name}: {data['description']}")
        print("\n" + ETHICAL_LINGUISTIC_DISCLAIMER)
        return

    if args.train:
        print("Generating training dataset (21 landmarks * 3 coords = 63 features)...")
        X_train, y_train = generate_landmark_dataset(samples_per_sign=30, seed=42)
        print(f"Dataset shape: {X_train.shape}, classes: {len(SUPPORTED_SIGNS)}")
        clf = SignClassifier()
        res = clf.train(X_train, y_train, epochs=args.epochs, save_path=args.weights_out)
        print(f"Training completed! Final Loss: {res['final_loss']}")
        print(f"Saved weights to: {args.weights_out}")
        return

    if args.evaluate:
        print("Evaluating classification performance...")
        X_test, y_test = generate_landmark_dataset(samples_per_sign=20, seed=123)
        clf = SignClassifier()
        if args.weights and os.path.exists(args.weights):
            clf.load_weights(args.weights)
        else:
            X_tr, y_tr = generate_landmark_dataset(samples_per_sign=30, seed=42)
            clf.train(X_tr, y_tr, epochs=args.epochs)

        preds = [clf.predict(X_test[i])["predicted_class_id"] for i in range(len(y_test))]
        metrics = SignEvaluator.evaluate(y_test, np.array(preds))
        print("Evaluation Metrics:")
        print(f"  Accuracy: {metrics['accuracy'] * 100:.2f}%")
        print(f"  Macro Precision: {metrics['macro_precision'] * 100:.2f}%")
        print(f"  Macro F1-Score: {metrics['macro_f1'] * 100:.2f}%")
        print("\nPer-Class Breakdown:")
        for sign, data in metrics["per_class"].items():
            print(f"  - {sign}: Precision={data['precision']:.2f}, Recall={data['recall']:.2f}, F1={data['f1_score']:.2f}")
        return

    if args.predict_sign:
        clf = SignClassifier()
        # Train quick model or load
        X_tr, y_tr = generate_landmark_dataset(samples_per_sign=25, seed=42)
        clf.train(X_tr, y_tr, epochs=10)

        canonical = get_canonical_sign_landmarks(args.predict_sign)
        feat = normalize_landmarks(canonical)
        res = clf.predict(feat)
        print(f"Target Sign: {args.predict_sign}")
        print(f"Predicted Sign: {res['predicted_sign']} (Confidence: {res['confidence'] * 100:.1f}%)")
        print("Top 3 Candidates:")
        for c in res["top_candidates"]:
            print(f"  - {c['sign']}: {c['confidence'] * 100:.1f}%")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
