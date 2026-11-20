"""
Interactive CLI for Personal Password Security Audit Tool.
"""
import sys
import getpass
from password_auditor import PasswordSecurityAuditor


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def display_report(rep):
    print_banner("Password Security Evaluation Report")
    print(f"Password Length       : {rep.length} characters")
    print(f"Character Diversity   : Lowercase: {'YES' if rep.has_lowercase else 'NO'}, Uppercase: {'YES' if rep.has_uppercase else 'NO'}")
    print(f"                        Digits: {'YES' if rep.has_digits else 'NO'}, Symbols: {'YES' if rep.has_symbols else 'NO'}")
    print(f"Character Pool Size   : {rep.character_set_size} possible glyphs")
    print(f"Estimated Entropy     : {rep.estimated_entropy_bits:.1f} bits")
    print(f"Common Weak Word?     : {'YES (Vulnerable)' if rep.is_common_weak else 'NO'}")
    print(f"Repeated Characters?  : {'YES (Detected)' if rep.has_repeated_characters else 'NO'}")

    if rep.detected_sequences:
        print("\nIdentified Predictable Sequences:")
        for s in rep.detected_sequences:
            print(f"  ! {s}")

    print("-" * 70)
    print(f"OVERALL STRENGTH SCORE: {rep.strength_score} / 100")
    print(f"SECURITY RATING       : {rep.rating.upper()}")
    print("-" * 70)

    print("\nActionable Recommendations:")
    for idx, r in enumerate(rep.recommendations, 1):
        print(f"  {idx}. {r}")

    print("\n" + "*" * 70)
    print("CYBERSECURITY NOTICE & LIMITATIONS:")
    print("  * This tool performs 100% offline, local analysis in volatile memory.")
    print("  * No submitted passwords are ever written to disk or sent across the network.")
    print("  * Mathematical entropy estimates offline brute-force attack complexity;")
    print("    it does not protect against malware, keyloggers, or third-party database breaches.")
    print("*" * 70)


def main():
    print_banner("Personal Password Security Audit Tool")
    print("Analyze password resilience, character diversity, and vulnerability to dictionary attacks.")

    while True:
        print("\nOptions:")
        print("1. Audit Password (Masked Input)")
        print("2. Audit Password (Visible Input)")
        print("3. Audit Preset Examples")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()
        if choice == "1":
            pwd = getpass.getpass("Enter password to analyze (input hidden): ")
            rep = PasswordSecurityAuditor.audit(pwd)
            display_report(rep)
        elif choice == "2":
            pwd = input("Enter password to analyze: ")
            rep = PasswordSecurityAuditor.audit(pwd)
            display_report(rep)
        elif choice == "3":
            print("\nPreset Test Passwords:")
            samples = [
                ("Weak 1", "password123"),
                ("Weak 2", "12345678"),
                ("Fair", "Summer2026!"),
                ("Strong", "K!7mP#9xQ$2wL@5v"),
                ("Passphrase", "correct-horse-battery-staple-2026"),
            ]
            for label, sample in samples:
                r = PasswordSecurityAuditor.audit(sample)
                print(f"  [{label}] '{sample}' -> Score: {r.strength_score}/100 ({r.rating})")
        elif choice == "4":
            print("Exiting tool. Stay secure!")
            sys.exit(0)


if __name__ == "__main__":
    main()
