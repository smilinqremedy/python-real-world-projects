"""
Dataset Generator & Utility for Bank Loan Default Prediction.
Generates balanced realistic historical loan records for model training and benchmarking.
"""
import numpy as np
import pandas as pd
import os

FEATURE_COLUMNS = [
    "annual_income",
    "loan_amount",
    "interest_rate",
    "employment_years",
    "debt_to_income",
    "credit_score",
    "previous_defaults"
]


def generate_loan_dataset(n_samples: int = 1200, seed: int = 42, output_csv: str = "loan_records.csv") -> pd.DataFrame:
    np.random.seed(seed)

    # 1. Generate realistic financial features
    annual_income = np.random.lognormal(mean=10.8, sigma=0.55, size=n_samples)  # ~$30k - $150k
    annual_income = np.clip(annual_income, 20000, 220000)

    loan_amount = np.random.lognormal(mean=9.5, sigma=0.6, size=n_samples)    # ~$5k - $50k
    loan_amount = np.clip(loan_amount, 3000, 80000)

    credit_score = np.random.normal(loc=660, scale=80, size=n_samples).astype(int)
    credit_score = np.clip(credit_score, 350, 850)

    debt_to_income = np.random.beta(a=2.5, b=4.5, size=n_samples) * 0.8
    debt_to_income = np.round(np.clip(debt_to_income, 0.05, 0.75), 3)

    interest_rate = 5.0 + (850 - credit_score) * 0.035 + (debt_to_income * 8.0) + np.random.normal(0, 1.0, size=n_samples)
    interest_rate = np.round(np.clip(interest_rate, 4.5, 32.0), 2)

    employment_years = np.random.exponential(scale=5.0, size=n_samples).astype(int)
    employment_years = np.clip(employment_years, 0, 30)

    prev_defaults_prob = np.clip((700 - credit_score) / 600.0, 0.02, 0.5)
    previous_defaults = np.random.binomial(n=3, p=prev_defaults_prob, size=n_samples)

    # 2. Compute Ground Truth Default Label using Logistic Link
    # Lower score + Higher DTI + Previous defaults = Higher probability of default
    z = (
        - 3.2
        - (credit_score - 650) * 0.012
        + (debt_to_income - 0.35) * 4.5
        + (interest_rate - 12.0) * 0.12
        + previous_defaults * 1.2
        - (annual_income - 60000) / 100000.0
        - employment_years * 0.06
    )
    prob_default = 1.0 / (1.0 + np.exp(-z))
    default = (np.random.rand(n_samples) < prob_default).astype(int)

    df = pd.DataFrame({
        "annual_income": np.round(annual_income, 2),
        "loan_amount": np.round(loan_amount, 2),
        "interest_rate": interest_rate,
        "employment_years": employment_years,
        "debt_to_income": debt_to_income,
        "credit_score": credit_score,
        "previous_defaults": previous_defaults,
        "default": default
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
