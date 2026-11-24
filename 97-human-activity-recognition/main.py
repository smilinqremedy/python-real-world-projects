"""
Command-Line Interface for Human Activity Recognition System.
"""
import argparse
import sys
import os
import csv
import json
import numpy as np

from dataset import (
    ACTIVITIES,
    CHANNELS,
    generate_synthetic_har_dataset,
    load_subject_data,
    create_sliding_windows
)
from model import HAR1DCNN
from trainer import HARTrainer
from evaluator import HAREvaluator
from visualizer import format_confusion_matrix_ascii


def main():
    parser = argparse.ArgumentParser(description="Human Activity Recognition System (1D-CNN)")
    parser.add_argument("--generate-data", type=str, help="Generate synthetic HAR dataset into directory")
    parser.add_argument("--train", type=str, help="Train 1D-CNN on subject dataset directory")
    parser.add_argument("--epochs", type=int, default=8, help="Training epochs")
    parser.add_argument("--weights-out", type=str, default="har_model_weights.npz", help="Weights save path")
    parser.add_argument("--weights", type=str, default="har_model_weights.npz", help="Weights path")
    parser.add_argument("--evaluate", type=str, help="Evaluate model on test subject directory")
    parser.add_argument("--predict", type=str, help="Predict activity for a sensor CSV file")

    args = parser.parse_args()

    if args.generate_data:
        print(f"Generating synthetic HAR sensor dataset in '{args.generate_data}'...")
        files = generate_synthetic_har_dataset(args.generate_data, num_subjects=6, samples_per_activity=150)
        print(f"Generated {len(files)} activity recording files across 6 subjects.")
        return

    if args.train:
        print(f"Loading training data from '{args.train}'...")
        # Subject-based split: subjects 1-4 for train, subject 5 for val
        subjs = sorted([d for d in os.listdir(args.train) if os.path.isdir(os.path.join(args.train, d))])
        if len(subjs) < 2:
            print("Error: Dataset directory must contain at least 2 subject subdirectories.", file=sys.stderr)
            sys.exit(1)

        train_subjs = subjs[:-1]
        val_subjs = [subjs[-1]]
        print(f"Subject Partitioning (Anti-Leakage): Train={train_subjs}, Val={val_subjs}")

        X_train_list, y_train_list = [], []
        for s in train_subjs:
            d, l = load_subject_data(os.path.join(args.train, s))
            xw, yw = create_sliding_windows(d, l, window_size=64, step_size=20)
            X_train_list.append(xw)
            y_train_list.append(yw)

        X_train = np.vstack(X_train_list)
        y_train = np.concatenate(y_train_list)

        d_v, l_v = load_subject_data(os.path.join(args.train, val_subjs[0]))
        X_val, y_val = create_sliding_windows(d_v, l_v, window_size=64, step_size=32)

        print(f"Training windows: {X_train.shape}, Validation windows: {X_val.shape}")

        model = HAR1DCNN(in_channels=6, window_size=64)
        trainer = HARTrainer(model)
        res = trainer.train(X_train, y_train, X_val, y_val, epochs=args.epochs, save_path=args.weights_out)

        print("Training Complete!")
        print(f"Final Train Loss: {res['final_train_loss']}")
        print(f"Validation Metrics:\n{json.dumps(res['validation_metrics'], indent=2)}")
        print(f"Weights saved to: {args.weights_out}")
        return

    if args.evaluate:
        if not os.path.exists(args.weights):
            print(f"Weights file not found: {args.weights}. Train first with --train.", file=sys.stderr)
            sys.exit(1)

        model = HAR1DCNN(in_channels=6, window_size=64)
        model.load_weights(args.weights)

        d_test, l_test = load_subject_data(args.evaluate)
        X_test, y_test = create_sliding_windows(d_test, l_test, window_size=64, step_size=32)

        preds, _ = model.predict(X_test)
        metrics = HAREvaluator.evaluate(y_test, preds)

        print("\nEvaluation Results on Test Subject:")
        print(f"Accuracy: {metrics['accuracy'] * 100:.2f}%")
        print(f"Macro F1-Score: {metrics['macro_f1'] * 100:.2f}%")
        print("\nConfusion Matrix:")
        print(format_confusion_matrix_ascii(metrics["confusion_matrix"]))
        return

    if args.predict:
        model = HAR1DCNN(in_channels=6, window_size=64)
        if os.path.exists(args.weights):
            model.load_weights(args.weights)

        data_rows = []
        with open(args.predict, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data_rows.append([
                    float(row["acc_x"]), float(row["acc_y"]), float(row["acc_z"]),
                    float(row["gyro_x"]), float(row["gyro_y"]), float(row["gyro_z"])
                ])

        arr = np.array(data_rows, dtype=np.float32)
        if len(arr) < 64:
            print("Error: Input CSV must contain at least 64 sequential sensor timesteps.", file=sys.stderr)
            sys.exit(1)

        window = arr[:64].T
        preds, probs = model.predict(np.expand_dims(window, axis=0))
        act_name = ACTIVITIES[int(preds[0])]
        conf = float(probs[0, int(preds[0])]) * 100
        print(f"\nPredicted Activity: {act_name} ({conf:.1f}% confidence)")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
