# Project 66: Cloud Storage Security Configuration Auditor

A defensive cloud posture assessment and configuration auditing engine designed to analyze AWS S3 bucket definitions (in JSON or YAML), detect critical public access exposures, evaluate server-side encryption and access logging controls, verify versioning and TLS transport enforcement, and output remediation guidance aligned with CIS AWS Benchmarks and NIST guidelines.

## Evaluated Security Baselines (CIS AWS S3 Benchmark Aligned)

- **S3.1 Public Access Block**: Verifies that all 4 settings (`BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`, `RestrictPublicBuckets`) are strictly enabled to prevent accidental exposure.
- **S3.2 Overly Permissive Policies**: Flags wildcard `Principal: "*"` with `Effect: "Allow"` lacking restrictive Condition statements.
- **S3.3 Server-Side Encryption (SSE)**: Verifies that default encryption is active (`aws:kms` or `AES256`) to protect data at rest.
- **S3.4 Access Logging**: Confirms that S3 server access logging is active and streaming audit trails to a dedicated logging bucket.
- **S3.5 Versioning**: Enforces S3 Versioning to defend against catastrophic deletion, tampering, and ransomware overwrites.
- **S3.6 Secure Transport (HTTPS)**: Validates that bucket policies explicitly deny non-SSL traffic (`aws:SecureTransport: "false"`).

## Features

- **Multi-Format Ingestion**: Ingests bucket configuration exports from both JSON and YAML templates (AWS CloudFormation, Terraform state exports, AWS CLI output).
- **Automated Risk Scoring & Severity**: Quantifies compliance percentage and assigns posture ratings (`Strong`, `Moderate`, `Substandard`, `Poor`).
- **Actionable Remediation Guidance**: Generates exact AWS CLI commands to remediate each identified configuration flaw.
- **Non-Destructive & Offline**: Operates via static configuration inspection without performing live mutations or accessing cloud accounts.

## Dependencies

- Python 3.10+
- `PyYAML`

```bash
pip install pyyaml
```

## Running the Application

Launch the interactive CLI:

```bash
cd 66-cloud-storage-security-auditor
python3 main.py
```

Use options `2`, `3`, or `4` to test against pre-packaged offline AWS S3 configuration benchmarks.

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_auditor.py -v
```
