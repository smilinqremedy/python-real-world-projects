"""
Command-Line Interface for Phishing Email Detection & Analysis Tool.
"""
import sys
import os
from phishing_detector import PhishingDetector
from sample_emails import create_benign_email, create_credential_phish_email, create_macro_invoice_phish


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_analysis(res: dict):
    print("\n" + "-" * 60)
    print(f"FILE:           {res['filename']}")
    print(f"SUBJECT:        {res['subject']}")
    print(f"FROM:           {res['sender_display']} <{res['sender_email']}>")
    if res.get("reply_to"):
        print(f"REPLY-TO:       {res['reply_to']}")
    print(f"PHISHING SCORE: {res['risk_score']} / 100")
    print(f"VERDICT:        [{res['verdict'].upper()}]")
    print("-" * 60)

    if res["indicators"]:
        print("\nIdentified Threat Indicators:")
        for idx, ind in enumerate(res["indicators"], 1):
            print(f"  #{idx} [{ind['severity'].upper()}] {ind['category']}:")
            print(f"     {ind['description']}")
    else:
        print("\nNo obvious phishing indicators detected.")

    print(f"\nRecommendation: {res['recommendation']}")
    print("-" * 60)


def generate_sample_emls() -> dict:
    folder = "sample_eml_files"
    os.makedirs(folder, exist_ok=True)
    p1 = os.path.join(folder, "benign_newsletter.eml")
    p2 = os.path.join(folder, "credential_paypal_phish.eml")
    p3 = os.path.join(folder, "overdue_invoice_macro.eml")

    with open(p1, "wb") as f:
        f.write(create_benign_email())
    with open(p2, "wb") as f:
        f.write(create_credential_phish_email())
    with open(p3, "wb") as f:
        f.write(create_macro_invoice_phish())

    return {"benign": p1, "phish": p2, "macro": p3}


def main():
    detector = PhishingDetector()

    while True:
        print_banner("Phishing Email Detection & Analysis Tool")
        print("1. Analyze Custom .EML File")
        print("2. Test Offline Sample: Benign Engineering Digest")
        print("3. Test Offline Sample: Credential Harvesting Phish (PayPal Spoof)")
        print("4. Test Offline Sample: Macro Weaponized Invoice Phish")
        print("5. Generate Sample .EML Files to Disk")
        print("6. View Analysis History from Database")
        print("0. Exit")

        choice = input("\nSelect an option [0-6]: ").strip()

        if choice == "1":
            path = input("Enter path to .eml file: ").strip()
            if not os.path.exists(path):
                print(f"File not found: '{path}'")
                continue
            try:
                res = detector.analyze_eml_file(path)
                display_analysis(res)
            except Exception as e:
                print(f"Analysis failed: {e}")

        elif choice == "2":
            res = detector.analyze_eml_bytes(create_benign_email(), "benign_digest.eml")
            display_analysis(res)

        elif choice == "3":
            res = detector.analyze_eml_bytes(create_credential_phish_email(), "credential_phish.eml")
            display_analysis(res)

        elif choice == "4":
            res = detector.analyze_eml_bytes(create_macro_invoice_phish(), "macro_invoice.eml")
            display_analysis(res)

        elif choice == "5":
            paths = generate_sample_emls()
            print("\nGenerated 3 test .eml files in 'sample_eml_files/':")
            for k, p in paths.items():
                print(f"  - [{k}]: {p}")

        elif choice == "6":
            print_banner("Database History")
            hist = detector.get_analysis_history()
            if not hist:
                print("No emails analyzed yet.")
            else:
                for h in hist:
                    print(f"[{h['analyzed_at']}] [{h['verdict']}] (Score: {h['risk_score']}) {h['subject'][:40]}... (From: {h['sender_email']})")

        elif choice == "0":
            print("Exiting Phishing Analyzer. Stay vigilant against social engineering!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
