# Project 71: Bank Loan Default Prediction System

A supervised machine learning classification platform designed for credit risk assessment, estimating the probability that a loan applicant will default on repayments, comparing multiple classification algorithms, addressing class imbalance, and categorizing applications into risk tiers.

## Machine Learning Task & Business Problem

Retail banks and lending institutions face financial loss when borrowers default on loans. The goal is to estimate default probability $P(\text{Default}=1)$ based on borrower financial features:
- `annual_income`: Total yearly earnings
- `loan_amount`: Total principal requested
- `interest_rate`: Fixed or variable borrowing rate
- `employment_years`: Years of steady employment
- `debt_to_income`: Monthly debt obligations divided by monthly gross income (DTI)
- `credit_score`: Credit bureau score (FICO 300–850)
- `previous_defaults`: Count of prior delinquent loan defaults

### Class Imbalance & Model Evaluation

Loan defaults typically represent only 15–20% of historical loan datasets. Evaluating models solely by raw accuracy is misleading (a naive model predicting all loans will repay achieves 85% accuracy but catches 0 defaults).

This system enforces `class_weight="balanced"` and evaluates models using:
- **Precision**: Proportion of predicted defaults that were actual defaults.
- **Recall (Sensitivity)**: Proportion of actual defaults caught by the model (critical for risk mitigation).
- **F1-Score**: Harmonic mean balancing precision and recall.
- **ROC-AUC**: Area under the Receiver Operating Characteristic curve.
- **Confusion Matrix**: Tracking False Positives (denying a safe borrower) and False Negatives (granting a loan to a defaulting borrower).

## Compared Algorithms

1. **Logistic Regression**: Interpretable linear baseline with standard scaling.
2. **Decision Tree Classifier**: Captures non-linear thresholds and feature splits.
3. **Random Forest Classifier**: Ensemble of bagged decision trees maximizing generalization and ROC-AUC.

## Credit Risk Categorization

- **Low Risk** ($P < 0.25$): Prime credit profile; standard approval terms.
- **Medium Risk** ($0.25 \le P \le 0.55$): Moderate risk; manual underwriting review required.
- **High Risk** ($P > 0.55$): Subprime profile; secondary guarantor or secured collateral required.

> [!IMPORTANT]
> **Advisory Disclaimer**: Model predictions are advisory risk metrics and do not constitute an automated legal credit denial or approval decision.

## Database Schema

- `loan_applications`: Unique application reference, borrower financials, credit score, predicted default probability, risk tier, and underwriting recommendation.
- `model_metrics`: Historical audit ledger of algorithm performance metrics.

## Running the Application

Launch the interactive CLI:

```bash
cd 71-bank-loan-default-prediction
python3 main.py
```

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_loan_prediction.py -v
```
