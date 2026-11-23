"""
Command-Line Interface for CSV Data Cleaning & Validation Tool.
"""
import sys
import os
import pandas as pd
from csv_cleaner import CSVCleaner


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def generate_sample_csv(target_path: str = "sample_dirty_contacts.csv") -> str:
    data = [
        {"name": "  fatima aliyu  ", "email": "Fatima.Aliyu@EXAMPLE.COM", "phone": "08031234567", "city": "Kano", "role": "Engineer"},
        {"name": "CHUKWUMA OBI", "email": "chukwuma@obi.ng", "phone": "+234 802 111 2233", "city": "Enugu", "role": "Manager"},
        {"name": "olumide adeyemi", "email": "invalid-email-address", "phone": "2348055556677", "city": "Ibadan", "role": "Analyst"},
        {"name": "  fatima aliyu  ", "email": "Fatima.Aliyu@EXAMPLE.COM", "phone": "08031234567", "city": "Kano", "role": "Engineer"},  # Exact Duplicate
        {"name": "grace bassey", "email": "grace@calabar.org", "phone": "not_a_phone", "city": None, "role": "Designer"},
        {"name": "  tariq bello  ", "email": "tariq@bello.com", "phone": "(0809) 999-8877", "city": "Abuja", "role": None},
    ]
    df = pd.DataFrame(data)
    df.to_csv(target_path, index=False)
    return target_path


def display_report(report: dict):
    print("\n" + "-" * 50)
    print("        DATA QUALITY & AUDIT REPORT        ")
    print("-" * 50)
    print(f"Initial Rows:             {report['initial_rows']}")
    print(f"Initial Columns:          {report['initial_columns']}")
    print(f"Duplicates Removed:       {report['duplicate_rows_removed']}")
    print(f"Final Rows:               {report['final_rows']}")
    print(f"Final Columns:            {report['final_columns']}")
    print(f"Standardized Phones:      {report['phones_standardized_count']}")
    print(f"Invalid Phones Flagged:   {report['invalid_phones_count']}")
    print(f"Invalid Emails Flagged:   {report['invalid_emails_count']}")

    if report["missing_values_detected"]:
        print("\nMissing Values Detected Before Cleaning:")
        for col, count in report["missing_values_detected"].items():
            if count > 0:
                print(f"  - {col}: {count} missing")

    if report["missing_values_handled"]:
        print("\nMissing Values Handled:")
        for col, action in report["missing_values_handled"].items():
            print(f"  - {col}: {action}")

    if report["normalized_columns"]:
        print("\nNormalized Text Columns:")
        for col in report["normalized_columns"]:
            print(f"  - {col}")
    print("-" * 50)


def main():
    cleaner = None

    while True:
        print_banner("CSV Data Cleaning & Validation Tool")
        print("1. Load CSV File")
        print("2. Generate Sample Dirty CSV File")
        print("3. Inspect Loaded Dataset")
        print("4. Run Automated Cleaning Pipeline")
        print("5. View Data Quality Audit Report")
        print("6. Export Cleaned Dataset (Preserves Original)")
        print("0. Exit")

        choice = input("\nSelect an option [0-6]: ").strip()

        if choice == "1":
            path = input("Enter path to CSV file: ").strip()
            if not os.path.exists(path):
                print(f"File not found: '{path}'")
                continue
            try:
                cleaner = CSVCleaner(filepath=path)
                print(f"Loaded successfully: {len(cleaner.df)} rows, {len(cleaner.df.columns)} columns.")
            except Exception as e:
                print(f"Failed to load CSV: {e}")

        elif choice == "2":
            sample_file = generate_sample_csv()
            cleaner = CSVCleaner(filepath=sample_file)
            print(f"Generated and loaded sample file: '{sample_file}' ({len(cleaner.df)} rows)")

        elif choice == "3":
            if not cleaner:
                print("Please load a CSV file first (Option 1 or 2).")
                continue
            info = cleaner.inspect()
            print(f"\nTotal Rows: {info['rows']}")
            print(f"Total Columns: {len(info['columns'])}: {', '.join(info['columns'])}")
            print("\nColumn Data Types:")
            for col, dt in info["dtypes"].items():
                print(f"  - {col}: {dt}")
            print("\nMissing Values per Column:")
            for col, count in info["missing_per_col"].items():
                print(f"  - {col}: {count}")
            print(f"Duplicate Rows Count: {info['duplicate_count']}")

        elif choice == "4":
            if not cleaner:
                print("Please load a CSV file first (Option 1 or 2).")
                continue
            name_col = input("Name column [default: 'name']: ").strip() or "name"
            email_col = input("Email column [default: 'email']: ").strip() or "email"
            phone_col = input("Phone column [default: 'phone']: ").strip() or "phone"

            fill_val = input("Default fill value for missing fields [default: 'Unknown']: ").strip() or "Unknown"
            defaults = {col: fill_val for col in cleaner.df.columns if col not in [name_col, email_col, phone_col]}

            report = cleaner.run_standard_pipeline(
                name_col=name_col if name_col in cleaner.df.columns else None,
                email_col=email_col if email_col in cleaner.df.columns else None,
                phone_col=phone_col if phone_col in cleaner.df.columns else None,
                fill_defaults=defaults,
                country_code="+234"
            )
            print("\nCleaning pipeline completed successfully!")
            display_report(report)

        elif choice == "5":
            if not cleaner:
                print("Please load a CSV file first (Option 1 or 2).")
                continue
            display_report(cleaner.get_quality_report())

        elif choice == "6":
            if not cleaner:
                print("Please load a CSV file first (Option 1 or 2).")
                continue
            out_path = input("Enter output CSV path (or press Enter for auto-named 'cleaned_<filename>.csv'): ").strip() or None
            try:
                saved = cleaner.export_cleaned(out_path)
                print(f"Cleaned CSV successfully saved to: '{saved}'")
            except Exception as e:
                print(f"Failed to export: {e}")

        elif choice == "0":
            print("Exiting CSV Data Cleaning Tool. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose an option from 0 to 6.")


if __name__ == "__main__":
    main()
