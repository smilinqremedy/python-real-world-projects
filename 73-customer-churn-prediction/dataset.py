"""
Dataset Generator for Customer Churn Prediction.
Generates realistic telecom/subscription customer behavioral records.
"""
import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "tenure_months",
    "contract_type_code",
    "monthly_charges",
    "total_charges",
    "support_tickets",
    "online_security",
    "tech_support",
    "payment_delay_days"
]

CONTRACT_MAPPING = {
    "Month-to-month": 0,
    "One year": 1,
    "Two year": 2
}


def generate_churn_dataset(n_samples: int = 1200, seed: int = 42, output_csv: str = "customer_churn.csv") -> pd.DataFrame:
    np.random.seed(seed)

    customer_ids = [f"CUST-{1000 + i}" for i in range(n_samples)]
    tenure_months = np.random.randint(1, 73, size=n_samples)
    contract_types = np.random.choice(["Month-to-month", "One year", "Two year"], p=[0.55, 0.25, 0.20], size=n_samples)
    contract_code = np.array([CONTRACT_MAPPING[c] for c in contract_types])

    monthly_charges = np.round(np.random.uniform(20.0, 115.0, size=n_samples), 2)
    total_charges = np.round(tenure_months * monthly_charges + np.random.normal(0, 15.0, size=n_samples), 2)
    total_charges = np.clip(total_charges, 20.0, None)

    support_tickets = np.random.poisson(lam=1.8, size=n_samples)
    online_security = np.random.choice([0, 1], p=[0.6, 0.4], size=n_samples)
    tech_support = np.random.choice([0, 1], p=[0.65, 0.35], size=n_samples)
    payment_delay_days = np.random.choice([0, 2, 5, 10, 20], p=[0.5, 0.2, 0.15, 0.1, 0.05], size=n_samples)

    # Churn probability logit formulation
    # Factors increasing churn: high charges, low tenure, month-to-month, many tickets, payment delay
    # Factors decreasing churn: long tenure, multi-year contract, tech support, online security
    logit = (
        -0.5
        - 0.04 * tenure_months
        - 0.8 * contract_code
        + 0.025 * (monthly_charges - 60)
        + 0.4 * support_tickets
        - 0.4 * online_security
        - 0.4 * tech_support
        + 0.08 * payment_delay_days
    )
    prob = 1.0 / (1.0 + np.exp(-logit))
    churn = (np.random.rand(n_samples) < prob).astype(int)

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "tenure_months": tenure_months,
        "contract_type": contract_types,
        "contract_type_code": contract_code,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "support_tickets": support_tickets,
        "online_security": online_security,
        "tech_support": tech_support,
        "payment_delay_days": payment_delay_days,
        "churn": churn
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
