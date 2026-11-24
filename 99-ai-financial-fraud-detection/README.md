# Project 99: AI-Based Financial Fraud Detection System

## Operational Fraud Policy & Consumer Protections

> [!WARNING]
> **FALSE POSITIVES & HUMAN-IN-THE-LOOP SAFEGUARDS:**
> 1. **Extreme Class Imbalance:** Fraud represents an extreme minority of financial traffic (typically 0.1% to 3%). In this regime, **Accuracy is a misleading metric**: a model predicting 100% legitimate achieves 97-99% accuracy while letting all fraud pass undetected. Fraud systems must be optimized for **PR-AUC (Precision-Recall AUC)** and **Recall**.
> 2. **Never Automatically Block Without Recourse:** Erroneously declining genuine cardholders causes severe consumer friction and lost revenue.
> 3. **Actionable Risk Tiers:**
>    - **LOW RISK (0 - 30):** Frictionless approval.
>    - **MODERATE RISK (31 - 70):** Dynamic step-up authentication (e.g. 3D-Secure / SMS OTP).
>    - **HIGH RISK (71 - 100):** Flagged for human fraud analyst investigation with documented disposition audit trails.

---

## Overview

The **AI-Based Financial Fraud Detection System** integrates supervised machine learning with unsupervised anomaly detection to identify suspicious transactions in real time:
- **Supervised Classifier:** Cost-weighted neural classifier weighting positive fraud instances 25x to counteract class imbalance.
- **Unsupervised Anomaly Detector:** Isolation Forest estimating tree path isolation depth for zero-day transaction attack vectors.
- **Robust Outlier Scaling:** Median and Interquartile Range (IQR) normalization robust to high-value transactions.
- **Comprehensive Evaluation:** PR-AUC, ROC-AUC, Precision, Recall, and Confusion Matrices.
- **Analyst Queue & SQLite Audit Trail:** Secure review workflow recording analyst investigations and dispositions.

---

## Architecture

```text
99-ai-financial-fraud-detection/
├── app.py                   # Streamlit live dashboard & analyst review queue
├── database.py              # SQLite audit trail & analyst disposition logs
├── dataset.py               # Ingestion, synthetic transaction generator & RobustScaler
├── evaluator.py             # PR-AUC, ROC-AUC, Precision, Recall & Cost Matrix
├── main.py                  # CLI command runner
├── models.py                # Supervised weighted classifier, Isolation Forest & Risk Engine
├── requirements.txt         # Dependencies
├── test_fraud_detection.py  # Automated unit test suite
└── README.md                # Documentation & fraud policy specifications
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 99-ai-financial-fraud-detection
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Generate Synthetic Transaction Dataset
```bash
python3 main.py --generate-data transactions.csv --n-samples 1500 --fraud-ratio 0.03
```

### 2. Train Models and Evaluate PR-AUC Benchmark
```bash
python3 main.py --train-eval
```

### 3. Score Transactions from a CSV File
```bash
python3 main.py --score-csv transactions.csv --output-report fraud_risk_report.csv
```

### 4. Launch the Streamlit Fraud Dashboard
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_fraud_detection.py -v
```
