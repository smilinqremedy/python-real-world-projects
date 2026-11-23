"""
Email Spam Classification System - Interactive CLI
"""
import os
import sys
from dataset import generate_spam_dataset
from model_trainer import SpamModelTrainer
from classifier import SpamClassifierService
import database


def print_header(title: str):
    print("\n" + "=" * 65)
    print(f" {title}")
    print("=" * 65)


def display_model_comparison(trainer: SpamModelTrainer):
    results = trainer.train_and_compare()
    print_header("Model Evaluation & Comparison Results")
    print(f"{'Model':<25} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 75)
    for model_name, m in results["model_metrics"].items():
        print(f"{model_name:<25} | {m['accuracy']:<10.4f} | {m['precision']:<10.4f} | {m['recall']:<10.4f} | {m['f1_score']:<10.4f}")

    print(f"\nBest Model: {results['best_model_name']} (F1: {results['best_f1_score']:.4f})")


def interactive_scan(service: SpamClassifierService):
    print_header("Scan Email Message for Spam / Phishing")
    subject = input("Email Subject (optional): ").strip()
    print("Paste Email Body (End with empty line):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    body = "\n".join(lines).strip()

    if not body:
        print("[!] No body content entered. Using sample email.")
        body = "Congratulations! You have won $10,000 cash prize in our holiday lottery. Click here to claim your reward immediately!"

    result = service.classify_email(text=body, subject=subject, persist=True)

    print("\n" + "-" * 65)
    print(f" Result: {result['classification']}")
    print(f" Spam Probability: {result['spam_probability']*100:.1f}% (Confidence: {result['confidence_percent']}%)")
    if result["flagged_keywords"]:
        print(f" Flagged Trigger Words: {', '.join(result['flagged_keywords'])}")
    else:
        print(" Flagged Trigger Words: None detected")
    print("-" * 65)


def view_history():
    print_header("Historical Scanned Emails (SQLite)")
    history = database.get_scan_history()
    if not history:
        print("No emails scanned yet.")
        return

    print(f"{'ID':<4} | {'Subject':<20} | {'Verdict':<8} | {'Prob':<6} | {'Keywords':<20}")
    print("-" * 70)
    for r in history[:15]:
        subj = (r["subject"] or "No Subject")[:18]
        verdict = "SPAM" if r["is_spam"] else "HAM"
        kw = (r["flagged_keywords"] or "")[:20]
        print(f"{r['id']:<4} | {subj:<20} | {verdict:<8} | {r['spam_probability']:<6.2f} | {kw:<20}")

    stats = database.get_scan_stats()
    print(f"\nTotal Scans: {stats['total_scanned']} | Spam: {stats['spam_detected']} | Ham: {stats['ham_detected']}")


def main():
    csv_file = "spam_dataset.csv"
    if not os.path.exists(csv_file):
        print(f"[*] Generating training dataset ({csv_file})...")
        generate_spam_dataset(n_samples=1000, output_csv=csv_file)

    trainer = SpamModelTrainer()
    trainer.train_and_compare()
    service = SpamClassifierService(trainer=trainer)

    while True:
        print_header("Email Spam Classification System")
        print("1. Compare Classifier Algorithms")
        print("2. Scan Custom Email Message")
        print("3. View Historical Scans (SQLite)")
        print("4. Regenerate Synthetic Dataset")
        print("5. Exit")
        choice = input("\nSelect an option (1-5): ").strip()

        if choice == "1":
            display_model_comparison(trainer)
        elif choice == "2":
            interactive_scan(service)
        elif choice == "3":
            view_history()
        elif choice == "4":
            generate_spam_dataset(n_samples=1500, output_csv=csv_file)
            print("[+] Dataset refreshed.")
            trainer.train_and_compare()
        elif choice == "5":
            print("Exiting Spam Classification System. Goodbye!")
            sys.exit(0)
        else:
            print("[!] Invalid option. Try again.")


if __name__ == "__main__":
    main()
