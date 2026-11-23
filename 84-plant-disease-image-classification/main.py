"""
Plant Disease Image Classification System - Interactive CLI
"""
import os
import sys
import cv2
from dataset import create_plant_dataloaders, DISEASE_CLASSES, synthesize_leaf_image
from trainer import PlantDiseaseTrainer
from classifier import PlantDiseaseClassifier


def print_header(title: str):
    print("\n" + "=" * 68)
    print(f" {title}")
    print("=" * 68)


def display_model_evaluation(trainer: PlantDiseaseTrainer, test_loader):
    metrics = trainer.evaluate_model(test_loader)
    print_header("Plant Disease CNN Classification Benchmark")
    print(f"  Test Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Precision:     {metrics['precision']:.4f} (weighted)")
    print(f"  Recall:        {metrics['recall']:.4f} (weighted)")
    print(f"  F1-Score:      {metrics['f1_score']:.4f} (weighted)")

    print("\nConfusion Matrix:")
    print("Pred ->      " + "  ".join([c[:6] for c in DISEASE_CLASSES]))
    for i, row in enumerate(metrics["confusion_matrix"]):
        row_str = "    ".join([f"{val:>2}" for val in row])
        print(f"{DISEASE_CLASSES[i][:11]:<11} [{row_str}]")


def test_sample_leaf(classifier: PlantDiseaseClassifier):
    print_header("Diagnose Sample Plant Leaf Image")
    print("Select a disease category to synthesize:")
    for idx, d in enumerate(DISEASE_CLASSES, 1):
        print(f"  {idx}) {d}")

    choice = input("\nSelect disease [1]: ").strip() or "1"
    try:
        target_disease = DISEASE_CLASSES[int(choice) - 1]
    except Exception:
        target_disease = "Healthy Leaf"

    test_img = synthesize_leaf_image(target_disease, seed=54321)
    sample_path = "sample_leaf_test.png"
    cv2.imwrite(sample_path, test_img)

    result = classifier.predict(sample_path)
    print("\n" + "-" * 68)
    print(f" Ground Truth Category: {target_disease}")
    print(f" Predicted Pathology:    {result['predicted_disease']} ({result['confidence_percentage']}%)")
    print("\nConfidence Distribution:")
    for d, prob in result["probability_distribution"].items():
        bar = "█" * int(prob / 3.5)
        print(f"  {d:<18}: {prob:>5.1f}% {bar}")

    print(f"\nObserved Symptoms: {result['symptoms']}")
    print(f"Recommended Treatment: {result['treatment_recommendation']}")
    print(f"Preventative Action:   {result['preventative_measures']}")
    print(f"\n[!] {result['specialist_disclaimer']}")
    print("-" * 68)


def main():
    print_header("Plant Disease Image Classification System (PyTorch CNN)")
    weights_path = "plant_disease_model.pth"

    train_loader, test_loader, _, _ = create_plant_dataloaders(samples_per_class=100, batch_size=32)
    trainer = PlantDiseaseTrainer()

    if not os.path.exists(weights_path):
        print("[*] Training CNN on leaf pathology dataset with augmentations (8 epochs)...")
        trainer.train_model(train_loader, epochs=8)
        trainer.save_weights(weights_path)
        print("[+] Model trained and saved.")
    else:
        trainer.load_weights(weights_path)

    classifier = PlantDiseaseClassifier(weights_path=weights_path)

    while True:
        print_header("Plant Disease Diagnostics Menu")
        print("1. View CNN Evaluation Metrics & Confusion Matrix")
        print("2. Test Sample Plant Leaf Diagnosis")
        print("3. Retrain CNN Model")
        print("4. Exit")
        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            display_model_evaluation(trainer, test_loader)
        elif choice == "2":
            test_sample_leaf(classifier)
        elif choice == "3":
            print("[*] Retraining model...")
            trainer.train_model(train_loader, epochs=10)
            trainer.save_weights(weights_path)
            classifier = PlantDiseaseClassifier(weights_path=weights_path)
            print("[+] Retraining complete.")
        elif choice == "4":
            print("Exiting Plant Pathology Diagnostic System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
