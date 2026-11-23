"""
Command-Line Interface for Digital Forensics File Metadata Analyzer.
"""
import sys
import os
from forensics_analyzer import ForensicsAnalyzer


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def create_demo_evidence_folder(target_dir: str = "demo_evidence_folder") -> str:
    os.makedirs(target_dir, exist_ok=True)
    f1 = os.path.join(target_dir, "contract_v1.docx")
    f2 = os.path.join(target_dir, "contract_backup.docx")  # duplicate
    f3 = os.path.join(target_dir, "financial_summary.pdf.exe")  # suspicious double extension
    f4 = os.path.join(target_dir, "incident_response.py")

    with open(f1, "w") as f:
        f.write("Master Service Agreement between Client and Vendor.")
    with open(f2, "w") as f:
        f.write("Master Service Agreement between Client and Vendor.")
    with open(f3, "wb") as f:
        f.write(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00")
    with open(f4, "w") as f:
        f.write("# Forensics script artifact\nprint('Analyzing evidence')\n")

    return target_dir


def main():
    analyzer = ForensicsAnalyzer()

    while True:
        print_banner("Digital Forensics File Metadata Analyzer")
        print("1. Scan & Analyze Target Evidence Directory")
        print("2. Generate Demo Evidence Directory")
        print("3. Verify Evidence Integrity (Anti-Tamper Baseline Check)")
        print("4. Export Forensic Examination Report (JSON)")
        print("0. Exit")

        choice = input("\nSelect an option [0-4]: ").strip()

        if choice == "1":
            target = input("Enter path to target directory: ").strip()
            if not os.path.isdir(target):
                print(f"Directory not found: '{target}'")
                continue
            case_no = input("Enter Case Number (e.g. CASE-2026-001): ").strip() or "CASE-DEMO"
            examiner = input("Examiner Name [Lead Forensic Investigator]: ").strip() or "Lead Forensic Investigator"
            try:
                res = analyzer.scan_directory(target, case_no, examiner)
                print("\n[SUCCESS] Forensic Scan Complete!")
                print(f"Case ID:                 {res['case_id']}")
                print(f"Files Analyzed:          {res['total_files_analyzed']}")
                print(f"Duplicate Files:         {res['duplicate_files_found']}")
                print(f"Suspicious Flags Found:  {res['suspicious_files_flagged']}")

                print("\nEvidence Manifest Summary:")
                for item in res["evidence_items"]:
                    flag_note = f" [FLAGS: {', '.join(item['suspicious_flags'])}]" if item["suspicious_flags"] else ""
                    dup_note = " [DUPLICATE]" if item["is_duplicate"] else ""
                    print(f"  - {item['relative_path']} ({item['size_bytes']} bytes) | SHA-256: {item['sha256'][:16]}...{dup_note}{flag_note}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            folder = create_demo_evidence_folder()
            print(f"\nGenerated synthetic evidence folder at: '{folder}' with 4 test files (including duplicates & suspicious extensions).")

        elif choice == "3":
            case_no = input("Enter Case Number to verify: ").strip()
            try:
                res = analyzer.verify_case_integrity(case_no)
                print("\n" + "-" * 50)
                print(f"INTEGRITY VERIFICATION AUDIT: {case_no}")
                print("-" * 50)
                print(f"Total Evidence Items:  {res['total_evidence_items']}")
                print(f"Intact & Valid:        {res['intact_count']}")
                print(f"Tampered / Modified:   {res['modified_count']}")
                print(f"Missing Evidence:      {res['missing_count']}")
                print(f"Integrity Validated:   {'PASSED (EVIDENCE UNTOUCHED)' if res['is_evidence_intact'] else 'FAILED (TAMPERING DETECTED)'}")

                if res["modified_files"]:
                    print("\n[WARNING] Modified Evidence Detected:")
                    for m in res["modified_files"]:
                        print(f"  - {m['file']} (Original: {m['original_sha256'][:12]}... -> Current: {m['current_sha256'][:12]}...)")

                if res["missing_files"]:
                    print("\n[WARNING] Missing Evidence Files:")
                    for miss in res["missing_files"]:
                        print(f"  - {miss['file']}")
                print("-" * 50)
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            case_no = input("Enter Case Number to export: ").strip()
            out_file = input("Enter output path (or press Enter for auto-named JSON): ").strip() or None
            try:
                saved = analyzer.export_report(case_no, out_file)
                print(f"Forensic Report exported successfully to: '{saved}'")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "0":
            print("Exiting Forensics Analyzer. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()
