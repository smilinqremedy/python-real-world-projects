"""
Command-Line Interface for Web Security Header Scanner.
"""
import sys
from scanner import WebSecurityHeaderScanner
from sample_responses import SECURE_HARDENED_SITE, VULNERABLE_LEGACY_SITE, MISCONFIGURED_SITE


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_report(res: dict):
    print("\n" + "-" * 55)
    print(f"AUDIT TARGET: {res['target']}")
    print(f"SECURITY SCORE: {res['score']} / 100 | GRADE: {res['grade']}")
    print("-" * 55)

    print("\nEvaluated Security Headers:")
    for h in res["evaluated_headers"]:
        status_tag = f"[{h['status'].upper()}]"
        print(f"  {status_tag:<20} {h['header']} ({h['importance']} Impact)")
        if h["value"]:
            print(f"    Value: {h['value'][:70]}...")
        if h["issues"]:
            for iss in h["issues"]:
                print(f"    ! Issue: {iss}")

    if res["information_leakage"]:
        print("\nSensitive Information Disclosure Headers Detected:")
        for leak in res["information_leakage"]:
            print(f"  ! {leak['header']}: {leak['value']} -> {leak['recommendation']}")

    print("\nSummary Breakdown:")
    s = res["summary"]
    print(f"  - Valid & Present:  {s['valid']}")
    print(f"  - Missing Headers:  {s['missing']}")
    print(f"  - Misconfigured:    {s['misconfigured']}")
    print(f"  - Leaking Headers:  {s['info_leak']}")
    print("-" * 55)


def main():
    scanner = WebSecurityHeaderScanner()

    while True:
        print_banner("Web Security Header Scanner")
        print("1. Scan Authorized Live Website URL")
        print("2. Test Offline Profile: Secure Hardened Site")
        print("3. Test Offline Profile: Vulnerable Legacy Site")
        print("4. Test Offline Profile: Misconfigured Site")
        print("0. Exit")

        choice = input("\nSelect an option [0-4]: ").strip()

        if choice == "1":
            url = input("Enter target URL (e.g. https://example.com): ").strip()
            if not scanner.validate_url(url):
                print("Invalid URL. Must begin with http:// or https://")
                continue
            try:
                print(f"Sending safe HTTP request to {url} ...")
                res = scanner.scan_url(url)
                display_report(res)

                export = input("\nExport report to JSON/HTML? (y/n) [n]: ").strip().lower()
                if export == "y":
                    fmt = input("Format (json / html) [json]: ").strip().lower() or "json"
                    saved = scanner.export_report(res, format=fmt)
                    print(f"Saved audit report to: '{saved}'")
            except Exception as e:
                print(f"Scan failed: {e}")

        elif choice == "2":
            res = scanner.scan_headers_dict(SECURE_HARDENED_SITE, "Offline Profile: Secure Hardened Site")
            display_report(res)

        elif choice == "3":
            res = scanner.scan_headers_dict(VULNERABLE_LEGACY_SITE, "Offline Profile: Vulnerable Legacy Site")
            display_report(res)

        elif choice == "4":
            res = scanner.scan_headers_dict(MISCONFIGURED_SITE, "Offline Profile: Misconfigured Site")
            display_report(res)

        elif choice == "0":
            print("Exiting Header Scanner. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
