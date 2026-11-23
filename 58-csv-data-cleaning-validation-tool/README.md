# Project 58: CSV Data Cleaning & Validation Tool

A comprehensive Python and pandas data cleaning engine designed to ingest raw, untidy tabular CSV records, diagnose anomalies, deduplicate rows, normalize text casing and whitespace, validate email syntaxes, standardize messy phone numbers to international format (E.164), generate detailed data audit reports, and export clean datasets without mutating the source files.

## Features

- **File Ingestion & Inspection**: Inspect row counts, column inventories, schema data types, null counts, and exact duplicate rows.
- **Deduplication Engine**: Identifies duplicate rows across all or specified columns and prunes redundant records.
- **Missing Value Strategies**:
  - Imputes default placeholder values across missing dimensions.
  - Drops rows where key critical identification fields are absent.
- **Text Normalization**: Strips accidental leading/trailing whitespace, corrects irregular capitalization (Title Case for names, lowercase for emails).
- **Email Validation**: Validates email syntaxes against RFC-compliant pattern rules and lowercases emails; flags invalid email rows in quality audit.
- **Phone Standardization**:
  - Automatically parses messy phone representations (e.g. `08031234567`, `2348031234567`, `+234 803 123 4567`, `(0803) 123-4567`).
  - Standardizes them into uniform E.164 international formats (`+2348031234567`).
- **Data Quality & Audit Reporting**: Produces metrics detailing initial vs. final row counts, duplicates purged, fields imputed, and flagged records.
- **Non-Destructive Export**: Guarantees source file immutability by defaulting to `cleaned_<filename>.csv`.

## Dependencies

- Python 3.10+
- `pandas`

```bash
pip install pandas
```

## Running the Application

Launch the interactive CLI:

```bash
cd 58-csv-data-cleaning-validation-tool
python3 main.py
```

You can choose option `2` to automatically generate a sample dirty contact dataset and run the automated pipeline on it.

## Running Automated Tests

Run the unit test suite:

```bash
python3 -m unittest test_cleaner.py -v
```
