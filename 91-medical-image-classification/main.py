"""
Command-Line Interface for AI Medical Image Classification System.
"""
import argparse
import sys
import os
import json
from dataset import generate_sample_medical_dataset, split_dataset, CLASSES
from trainer import MedicalModelTrainer
from classifier import MedicalClassifierService, CLINICAL_SAFETY_DISCLAIMER
import database


def main():
    parser = argparse.ArgumentParser(description="AI-Based Medical Image Classification System")
    parser.add_argument("--generate-samples", type=str, help="Generate synthetic sample dataset into folder")
    parser.add_argument("--samples-count", type=int, default=15, help="Number of samples per class")
    parser.add_argument("--train", type=str, help="Train model using dataset in specified directory")
    parser.add_argument("--epochs", type=int, default=5, help="Training epochs")
    parser.add_argument("--weights-out", type=str, default="medical_cnn_weights.npz", help="Weights output path")
    parser.add_argument("--weights", type=str, default="medical_cnn_weights.npz", help="Weights path for inference")
    parser.add_argument("--predict", type=str, help="Classify an image file")
    parser.add_argument("--notes", type=str, default="", help="Optional notes for prediction log")
    parser.add_argument("--history", action="store_true", help="Print recent prediction history")

    args = parser.parse_args()

    if args.generate_samples:
        print(f"Generating sample radiographic dataset in '{args.generate_samples}'...")
        records = generate_sample_medical_dataset(args.generate_samples, samples_per_class=args.samples_count)
        print(f"Generated {len(records['Normal'])} Normal and {len(records['Pneumonia'])} Pneumonia samples.")
        return

    if args.train:
        print(f"Loading dataset from '{args.train}'...")
        normal_dir = os.path.join(args.train, "Normal")
        pneumonia_dir = os.path.join(args.train, "Pneumonia")

        records = {"Normal": [], "Pneumonia": []}
        if os.path.exists(normal_dir):
            records["Normal"] = [os.path.join(normal_dir, f) for f in os.listdir(normal_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if os.path.exists(pneumonia_dir):
            records["Pneumonia"] = [os.path.join(pneumonia_dir, f) for f in os.listdir(pneumonia_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        train_data, val_data, test_data = split_dataset(records)
        print(f"Dataset split: Train={len(train_data)}, Val={len(val_data)}, Test={len(test_data)}")

        trainer = MedicalModelTrainer()
        res = trainer.train(train_data, val_data, epochs=args.epochs, save_weights_path=args.weights_out)
        print("Training complete!")
        print(f"Final Train Loss: {res['final_train_loss']}")
        print(f"Validation Metrics: {json.dumps(res['validation_metrics'], indent=2)}")
        print(f"Weights saved to: {res['weights_saved_to']}")
        return

    if args.predict:
        service = MedicalClassifierService(weights_path=args.weights if os.path.exists(args.weights) else None)
        result = service.classify_image(args.predict, user_notes=args.notes)
        print("\n" + "=" * 60)
        print("CLINICAL SAFETY ADVISORY:")
        print(result["disclaimer"])
        print("=" * 60)
        if result["success"]:
            print(f"Image: {result['image_name']}")
            print(f"Predicted Class: {result['predicted_class']}")
            print(f"Confidence: {result['confidence_score'] * 100:.2f}%")
            print(f"Probabilities: {result['probabilities']}")
            print(f"Audit Log ID: {result['log_id']}")
        else:
            print(f"Error: {result['error']}")
        return

    if args.history:
        history = database.get_prediction_history(limit=10)
        print(f"Recent Predictions ({len(history)} entries):")
        for row in history:
            print(f"[{row['timestamp']}] ID={row['id']} Image={row['image_name']} Class={row['predicted_class']} Conf={row['confidence_score']}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
