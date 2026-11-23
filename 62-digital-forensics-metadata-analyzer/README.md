# Project 62: Digital Forensics File Metadata Analyzer

A specialized digital forensics tool engineered to collect, analyze, hash, and document digital evidence from target directories while strictly maintaining evidence preservation and immutability.

## Forensics Principles & Chain of Custody

Digital forensic examinations mandate that original evidence files are never modified, executed, or corrupted:
- **Strict Read-Only Operations**: All file system operations open files in read-only binary mode (`"rb"`).
- **Cryptographic Hashing (SHA-256 & MD5)**: Memory-efficient chunked hashing establishes cryptographic fingerprints for every evidence item.
- **Timestamp Caveats**: Filesystem timestamps (`mtime`, `ctime`, `atime`) are documented as indicators of filesystem events rather than definitive, tamper-proof proof of original authoring time.
- **Deceptive Extension Detection**: Identifies evasion attempts such as deceptive double extensions (e.g. `report.pdf.exe`) and unexpected executable script types.
- **Integrity Verification (Anti-Tamper Audit)**: Recalculates hashes against previously locked baselines to identify any evidence tampering, modification, or deletion.

## Features

- **Metadata Extraction**: Gathers file names, relative/absolute paths, extensions, sizes, and filesystem timestamps.
- **Cryptographic Fingerprinting**: Calculates both SHA-256 and MD5 hashes using 64 KB streaming buffers.
- **Exact Duplicate Detection**: Clusters identical files based on SHA-256 hash collisions.
- **Suspicious File Heuristics**:
  - Flags double extensions (`.pdf.exe`, `.docx.vbs`, `.jpg.scr`).
  - Flags executable formats (`.exe`, `.scr`, `.bat`, `.ps1`).
  - Flags hidden executable files and zero-byte anomalies.
- **Cryptographic Verification**: Re-scans previously logged cases to ensure 100% data integrity or immediately alert on evidence tampering.
- **JSON Evidence Manifest Export**: Exports structured case reports suitable for incident documentation.

## Database Schema

- `forensic_cases`: Case number, investigator name, target directory, and creation timestamp.
- `evidence_items`: Relative path, file size, SHA-256, MD5, filesystem timestamps, duplicate status, and suspicious flags.
- `integrity_verifications`: Audit log documenting verification runs, intact counts, modified counts, and missing files.

## Running the Application

Launch the interactive CLI:

```bash
cd 62-digital-forensics-metadata-analyzer
python3 main.py
```

Use Option `2` to generate a demo evidence directory with duplicate and suspicious files for testing.

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_forensics.py -v
```
