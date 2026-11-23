"""
CSV Data Cleaning & Validation Engine.
Provides modular data cleaning, standardization, and quality reporting for tabular CSV datasets.
"""
import os
import re
from typing import Dict, List, Optional, Any
import pandas as pd


class CSVCleaner:
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    def __init__(self, filepath: Optional[str] = None, df: Optional[pd.DataFrame] = None):
        self.original_filepath = filepath
        self.df = None
        self.initial_rows = 0
        self.initial_columns = 0
        self.report: Dict[str, Any] = {
            "initial_rows": 0,
            "initial_columns": 0,
            "duplicate_rows_removed": 0,
            "missing_values_detected": {},
            "missing_values_handled": {},
            "invalid_emails_count": 0,
            "invalid_emails_indices": [],
            "phones_standardized_count": 0,
            "invalid_phones_count": 0,
            "normalized_columns": [],
            "final_rows": 0,
            "final_columns": 0,
        }

        if df is not None:
            self.df = df.copy()
            self.initial_rows = len(self.df)
            self.initial_columns = len(self.df.columns)
            self.report["initial_rows"] = self.initial_rows
            self.report["initial_columns"] = self.initial_columns
        elif filepath:
            self.load_csv(filepath)

    def load_csv(self, filepath: str) -> pd.DataFrame:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: '{filepath}'")
        self.original_filepath = filepath
        self.df = pd.read_csv(filepath)
        self.initial_rows = len(self.df)
        self.initial_columns = len(self.df.columns)
        self.report["initial_rows"] = self.initial_rows
        self.report["initial_columns"] = self.initial_columns
        return self.df

    def inspect(self) -> Dict[str, Any]:
        """Return dataset structure and overview."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        return {
            "rows": len(self.df),
            "columns": list(self.df.columns),
            "dtypes": {col: str(dtype) for col, dtype in self.df.dtypes.items()},
            "missing_per_col": self.df.isnull().sum().to_dict(),
            "duplicate_count": int(self.df.duplicated().sum()),
        }

    def remove_duplicates(self, subset: Optional[List[str]] = None, keep: str = "first") -> int:
        """Identify and eliminate duplicate rows."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)
        removed = before - len(self.df)
        self.report["duplicate_rows_removed"] += removed
        return removed

    def detect_missing(self) -> Dict[str, int]:
        """Detect count of null/NaN values per column."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        missing = self.df.isnull().sum().to_dict()
        self.report["missing_values_detected"] = missing
        return missing

    def handle_missing(self, drop_columns: Optional[List[str]] = None,
                       fill_defaults: Optional[Dict[str, Any]] = None,
                       drop_threshold_rows: bool = False) -> Dict[str, Any]:
        """
        Handle missing values by filling default values or dropping records.
        """
        if self.df is None:
            raise ValueError("No dataset loaded.")

        self.detect_missing()

        # Fill defaults
        if fill_defaults:
            for col, val in fill_defaults.items():
                if col in self.df.columns:
                    missing_count = int(self.df[col].isnull().sum())
                    self.df[col] = self.df[col].fillna(val)
                    self.report["missing_values_handled"][col] = f"Filled {missing_count} missing with '{val}'"

        # Drop rows where critical columns are null
        if drop_columns:
            for col in drop_columns:
                if col in self.df.columns:
                    missing_count = int(self.df[col].isnull().sum())
                    self.df = self.df.dropna(subset=[col]).reset_index(drop=True)
                    self.report["missing_values_handled"][col] = f"Dropped {missing_count} rows where '{col}' was null"

        # Optionally drop rows where all columns are empty
        if drop_threshold_rows:
            before = len(self.df)
            self.df = self.df.dropna(how="all").reset_index(drop=True)
            self.report["missing_values_handled"]["all_empty_rows"] = f"Dropped {before - len(self.df)} empty rows"

        return self.report["missing_values_handled"]

    def normalize_text(self, column: str, casing: str = "title", strip: bool = True):
        """
        Normalize text content: strip whitespace and apply casing ('title', 'lower', 'upper').
        """
        if self.df is None or column not in self.df.columns:
            return

        def _clean_str(val):
            if pd.isna(val):
                return val
            s = str(val)
            if strip:
                s = s.strip()
            if casing == "title":
                return s.title()
            elif casing == "lower":
                return s.lower()
            elif casing == "upper":
                return s.upper()
            return s

        self.df[column] = self.df[column].apply(_clean_str)
        if column not in self.report["normalized_columns"]:
            self.report["normalized_columns"].append(f"{column} ({casing})")

    def validate_and_normalize_emails(self, email_col: str, drop_invalid: bool = False) -> Dict[str, Any]:
        """
        Lowercases email strings and checks against standard email regex format.
        Flags or removes invalid emails.
        """
        if self.df is None or email_col not in self.df.columns:
            return {}

        self.normalize_text(email_col, casing="lower", strip=True)

        invalid_indices = []
        for idx, val in self.df[email_col].items():
            if pd.isna(val) or not self.EMAIL_REGEX.match(str(val)):
                invalid_indices.append(idx)

        self.report["invalid_emails_count"] = len(invalid_indices)
        self.report["invalid_emails_indices"] = invalid_indices

        if drop_invalid and invalid_indices:
            self.df = self.df.drop(index=invalid_indices).reset_index(drop=True)

        return {
            "invalid_count": len(invalid_indices),
            "invalid_indices": invalid_indices,
        }

    @staticmethod
    def format_phone_number(phone_str: Any, default_country_code: str = "+234") -> Optional[str]:
        """
        Standardize phone numbers to international E.164-style standard.
        e.g.,
          08031234567 -> +2348031234567
          2348031234567 -> +2348031234567
          +234 803 123 4567 -> +2348031234567
          (0803) 123-4567 -> +2348031234567
        """
        if pd.isna(phone_str):
            return None

        # Strip all non-digit characters except leading '+'
        raw = str(phone_str).strip()
        digits = re.sub(r"[^\d]", "", raw)

        if not digits or len(digits) < 7:
            return None

        # Clean cc
        cc_digits = re.sub(r"[^\d]", "", default_country_code)

        # Case 1: Starts with country code without plus (e.g. 234803...)
        if digits.startswith(cc_digits) and len(digits) >= 10:
            return f"+{digits}"

        # Case 2: Starts with local zero (e.g. 0803..., 070...)
        if digits.startswith("0") and len(digits) == 11:
            return f"+{cc_digits}{digits[1:]}"

        # Case 3: 10 digits without leading 0 (e.g. 8031234567)
        if len(digits) == 10 and not digits.startswith("0"):
            return f"+{cc_digits}{digits}"

        # If already formatted with cc and proper length
        if len(digits) >= 11:
            return f"+{digits}"

        return f"+{cc_digits}{digits}"

    def standardize_phones(self, phone_col: str, default_country_code: str = "+234") -> Dict[str, Any]:
        """
        Standardizes phone numbers in the specified column.
        """
        if self.df is None or phone_col not in self.df.columns:
            return {}

        standardized_count = 0
        invalid_count = 0

        new_phones = []
        for val in self.df[phone_col]:
            formatted = self.format_phone_number(val, default_country_code)
            if formatted:
                new_phones.append(formatted)
                standardized_count += 1
            else:
                new_phones.append(val)
                if not pd.isna(val):
                    invalid_count += 1

        self.df[phone_col] = new_phones
        self.report["phones_standardized_count"] = standardized_count
        self.report["invalid_phones_count"] = invalid_count
        return {
            "standardized_count": standardized_count,
            "invalid_count": invalid_count,
        }

    def run_standard_pipeline(self,
                              name_col: Optional[str] = "name",
                              email_col: Optional[str] = "email",
                              phone_col: Optional[str] = "phone",
                              fill_defaults: Optional[Dict[str, Any]] = None,
                              drop_missing_cols: Optional[List[str]] = None,
                              country_code: str = "+234") -> Dict[str, Any]:
        """Execute complete standardized cleaning pipeline."""
        if self.df is None:
            raise ValueError("No dataset loaded.")

        # 1. Handle Duplicates
        self.remove_duplicates()

        # 2. Handle Missing values
        self.handle_missing(drop_columns=drop_missing_cols, fill_defaults=fill_defaults)

        # 3. Normalize Name columns
        if name_col and name_col in self.df.columns:
            self.normalize_text(name_col, casing="title", strip=True)

        # 4. Normalize & Validate Emails
        if email_col and email_col in self.df.columns:
            self.validate_and_normalize_emails(email_col)

        # 5. Standardize Phone Numbers
        if phone_col and phone_col in self.df.columns:
            self.standardize_phones(phone_col, default_country_code=country_code)

        # Final counts
        self.report["final_rows"] = len(self.df)
        self.report["final_columns"] = len(self.df.columns)
        return self.get_quality_report()

    def get_quality_report(self) -> Dict[str, Any]:
        """Generate full data cleaning & quality audit report."""
        if self.df is not None:
            self.report["final_rows"] = len(self.df)
            self.report["final_columns"] = len(self.df.columns)
        return self.report

    def export_cleaned(self, output_filepath: Optional[str] = None) -> str:
        """
        Export cleaned dataset to CSV. Preserves the original file by default.
        """
        if self.df is None:
            raise ValueError("No dataset to export.")

        if output_filepath is None:
            if self.original_filepath:
                dirname, basename = os.path.split(self.original_filepath)
                output_filepath = os.path.join(dirname, f"cleaned_{basename}")
            else:
                output_filepath = "cleaned_data.csv"

        # Prevent overwriting original file
        if self.original_filepath and os.path.abspath(output_filepath) == os.path.abspath(self.original_filepath):
            dirname, basename = os.path.split(output_filepath)
            output_filepath = os.path.join(dirname, f"cleaned_{basename}")

        self.df.to_csv(output_filepath, index=False)
        return output_filepath
