"""
Facial Expression Recognition System - Interactive CLI
"""
import os
import sys
import cv2
from dataset import create_expression_dataloaders, EXPRESSION_CLASSES, synthesize_face_image
from trainer import FERModelTrainer
from classifier import FacialExpressionClassifier


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def display_model_evaluation(trainer: FERModelTrainer, test_loader):
    metrics = trainer.evaluate_model(test_loader)
    print_header("CNN Facial Expression Model Performance")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f} (weighted)")
    print(f"  Recall:    {metrics['recall']:.4f} (weighted)")
    print(f"  F1-Score:  {metrics['f1_score']:.4f} (weighted)")

    print("\nConfusion Matrix:")
    print("Pred ->   " + "  ".join([c[:4] for c in EXPRESSION_CLASSES]))
    for i, row in enumerate(metrics["confusion_matrix"]):
        row_str = "    ".join([f"{val:>2}" for val in row])
        print(f"{EXPRESSION_CLASSES[i][:8]:<8} [{row_str}]")


def test_sample_image(classifier: FacialExpressionClassifier):
    print_header("Test Facial Expression on Synthetic Samples")
    print("Available categories: 1) Happy  2) Sad  3) Surprise  4) Angry  5) Neutral")
    choice = input("Select an expression to synthesize and classify [1]: ").strip() or "1"
    mapping = {"1": "Happy", "2": "Sad", "3": "Surprise", "4": "Angry", "5": "Neutral"}
    target_expr = mapping.get(choice, "Happy")

    test_img = synthesize_face_image(target_expr, seed=12345)
    sample_path = "sample_test_face.png"
    cv2.imwrite(sample_path, test_img)

    result = classifier.predict(sample_path)
    print(f"\nGround Truth Expression: {target_expr}")
    print(f"Predicted Expression:    {result['predicted_expression']} ({result['confidence_percentage']}%)")
    print("\nClass Probabilities:")
    for expr, prob in result["probability_distribution"].items():
        bar = "█" * int(prob / 4)
        print(f"  {expr:<10}: {prob:>5.1f}% {bar}")

    print(f"\nAdvisory Note:\n{result['ethics_notice']}")


def main():
    print_header("Facial Expression Recognition System (PyTorch CNN)")
    weights_path = "facial_expression_model.pth"

    train_loader, test_loader, _, _ = create_expression_dataloaders(samples_per_class=100, batch_size=32)
    trainer = FERModelTrainer()

    if not os.path.exists(weights_path):
        print("[*] Training CNN model on facial expression dataset (8 epochs)...")
        trainer.train_model(train_loader, epochs=8)
        trainer.save_weights(weights_path)
        print("[+] Model trained and saved.")
    else:
        trainer.load_weights(weights_path)

    classifier = FacialExpressionClassifier(weights_path=weights_path)

    while True:
        print_header("Facial Expression Recognition Menu")
        print("1. View Model Evaluation Metrics & Confusion Matrix")
        print("2. Test Sample Facial Expression Image")
        print("3. Retrain CNN Model")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            display_model_evaluation(trainer, test_loader)
        elif choice == "2":
            test_sample_image(classifier)
        elif choice == "3":
            print("[*] Retraining CNN model...")
            trainer.train_model(train_loader, epochs=10)
            trainer.save_weights(weights_path)
            classifier = FacialExpressionClassifier(weights_path=weights_path)
            print("[+] Retraining complete.")
        elif choice == "4":
            print("Exiting Facial Expression Recognition System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
