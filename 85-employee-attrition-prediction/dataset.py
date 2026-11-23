"""
Workforce Dataset Generator for Employee Attrition & Resignation Prediction.
Generates realistic organizational turnover datasets.
"""
import numpy as np
import pandas as pd


CATEGORICAL_COLUMNS = [
    "department",
    "salary_level",
    "overtime"
]

NUMERICAL_COLUMNS = [
    "satisfaction_score",
    "last_evaluation",
    "number_of_projects",
    "monthly_hours",
    "tenure_years",
    "promotion_last_5years"
]


def generate_employee_dataset(n_samples: int = 1500, seed: int = 42, output_csv: str = "employee_attrition.csv") -> pd.DataFrame:
    np.random.seed(seed)

    emp_ids = [f"EMP-{10000 + i}" for i in range(n_samples)]
    departments = np.random.choice(
        ["Engineering", "Sales", "Support", "Marketing", "R&D", "Finance", "HR"],
        p=[0.30, 0.25, 0.15, 0.10, 0.08, 0.07, 0.05],
        size=n_samples
    )
    salary_level = np.random.choice(["Low", "Medium", "High"], p=[0.45, 0.40, 0.15], size=n_samples)
    overtime = np.random.choice(["Yes", "No"], p=[0.32, 0.68], size=n_samples)

    tenure_years = np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 10], p=[0.15, 0.20, 0.25, 0.15, 0.10, 0.06, 0.04, 0.03, 0.02], size=n_samples)
    monthly_hours = np.random.randint(130, 310, size=n_samples)
    number_of_projects = np.random.choice([2, 3, 4, 5, 6, 7], p=[0.15, 0.30, 0.30, 0.15, 0.07, 0.03], size=n_samples)
    promotion_last_5years = np.random.choice([0, 1], p=[0.94, 0.06], size=n_samples)

    # Correlated satisfaction score
    base_satisfaction = np.random.uniform(0.3, 0.95, size=n_samples)
    base_satisfaction -= np.where(overtime == "Yes", 0.12, 0.0)
    base_satisfaction -= np.where(salary_level == "Low", 0.10, 0.0)
    base_satisfaction += np.where(promotion_last_5years == 1, 0.15, 0.0)
    satisfaction_score = np.round(np.clip(base_satisfaction, 0.09, 1.0), 2)

    last_evaluation = np.round(np.random.uniform(0.36, 1.0, size=n_samples), 2)

    # Logit calculation for Attrition
    # Drivers: low satisfaction, extreme hours (>250 or <150), no promotion, high tenure without promotion, overtime, low salary
    salary_risk = np.where(salary_level == "Low", 0.6, np.where(salary_level == "Medium", 0.1, -0.6))
    overtime_risk = np.where(overtime == "Yes", 0.8, 0.0)
    hours_risk = np.where(monthly_hours > 250, 0.9, np.where(monthly_hours < 150, 0.4, 0.0))
    tenure_risk = np.where(tenure_years >= 3, 0.35, 0.0)

    logit = (
        0.2
        - 3.2 * satisfaction_score
        + 0.8 * last_evaluation
        + salary_risk
        + overtime_risk
        + hours_risk
        + tenure_risk
        - 1.0 * promotion_last_5years
    )
    prob = 1.0 / (1.0 + np.exp(-logit))
    attrition = (np.random.rand(n_samples) < prob).astype(int)

    df = pd.DataFrame({
        "employee_id": emp_ids,
        "department": departments,
        "salary_level": salary_level,
        "overtime": overtime,
        "satisfaction_score": satisfaction_score,
        "last_evaluation": last_evaluation,
        "number_of_projects": number_of_projects,
        "monthly_hours": monthly_hours,
        "tenure_years": tenure_years,
        "promotion_last_5years": promotion_last_5years,
        "attrition": attrition
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
