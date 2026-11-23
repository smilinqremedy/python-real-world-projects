"""
Command-Line Interface for Cloud Storage Security Configuration Auditor.
"""
import sys
import os
from auditor import CloudStorageSecurityAuditor
from sample_configs import INSECURE_PUBLIC_BUCKET, HARDENED_ENTERPRISE_BUCKET, PARTIAL_RISK_BUCKET


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_audit_results(res: dict):
    print("\n" + "-" * 60)
    print(f"BUCKET AUDITED:       {res['bucket_name']}")
    print(f"SECURITY POSTURE:     {res['security_posture']}")
    print(f"COMPLIANCE SCORE:     {res['compliance_percentage']}% ({res['passed_checks']}/{res['total_checks']} checks passed)")
    print("-" * 60)

    print("\nFindings by Severity:")
    for sev, count in res["severity_summary"].items():
        if count > 0:
            print(f"  - [{sev.upper()}]: {count} finding(s)")

    if not res["findings"]:
        print("\n[EXCELLENT] No security vulnerabilities detected. Configuration adheres to best practices.")
    else:
        print("\nIdentified Security Deficiencies:")
        for idx, f in enumerate(res["findings"], 1):
            print(f"\n  #{idx} [{f['severity'].upper()}] {f['check_id']} - {f['title']}")
            print(f"     Description: {f['description']}")
            print(f"     Remediation: {f['remediation']}")
    print("-" * 60)


def main():
    auditor = CloudStorageSecurityAuditor()

    while True:
        print_banner("Cloud Storage Security Configuration Auditor")
        print("1. Audit AWS S3 Configuration File (JSON / YAML)")
        print("2. Test Offline Benchmark: Hardened Enterprise S3 Bucket")
        print("3. Test Offline Benchmark: Insecure Public S3 Bucket")
        print("4. Test Offline Benchmark: Partially Secured S3 Bucket")
        print("0. Exit")

        choice = input("\nSelect an option [0-4]: ").strip()

        if choice == "1":
            path = input("Enter path to S3 configuration file (.json / .yaml): ").strip()
            if not os.path.exists(path):
                print(f"File not found: '{path}'")
                continue
            try:
                config_data = auditor.load_config_file(path)
                res = auditor.audit_bucket(config_data)
                display_audit_results(res)

                export = input("\nExport findings to JSON report? (y/n) [n]: ").strip().lower()
                if export == "y":
                    saved = auditor.export_report(res)
                    print(f"Saved audit report to: '{saved}'")
            except Exception as e:
                print(f"Audit failed: {e}")

        elif choice == "2":
            res = auditor.audit_bucket(HARDENED_ENTERPRISE_BUCKET)
            display_audit_results(res)

        elif choice == "3":
            res = auditor.audit_bucket(INSECURE_PUBLIC_BUCKET)
            display_audit_results(res)

        elif choice == "4":
            res = auditor.audit_bucket(PARTIAL_RISK_BUCKET)
            display_audit_results(res)

        elif choice == "0":
            print("Exiting Cloud Storage Auditor. Keep your buckets secure!")
            sys.exit(0)
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()
