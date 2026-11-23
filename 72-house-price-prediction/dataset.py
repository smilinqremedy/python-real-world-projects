"""
Dataset Generator & Feature Schema for House Price Prediction System.
"""
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "square_feet",
    "bedrooms",
    "bathrooms",
    "location_score",
    "year_built",
    "condition_rating",
    "garage_spaces"
]


def generate_housing_dataset(n_samples: int = 1000, seed: int = 42, output_csv: str = "housing_records.csv") -> pd.DataFrame:
    np.random.seed(seed)

    square_feet = np.random.normal(loc=2200, scale=650, size=n_samples).astype(int)
    square_feet = np.clip(square_feet, 800, 5500)

    bedrooms = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.05, 0.20, 0.45, 0.20, 0.08, 0.02], size=n_samples)
    bathrooms = np.round(np.clip(bedrooms * 0.7 + np.random.normal(0, 0.4, size=n_samples), 1.0, 5.0), 1)

    location_score = np.random.randint(1, 11, size=n_samples)  # 1 to 10
    year_built = np.random.randint(1965, 2025, size=n_samples)
    condition_rating = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.50, 0.20, 0.10], size=n_samples)
    garage_spaces = np.random.choice([0, 1, 2, 3], p=[0.15, 0.35, 0.40, 0.10], size=n_samples)

    # Valuation Formula with noise
    base_price = 80000.0
    price = (
        base_price
        + (square_feet * 165.0)
        + (bedrooms * 12000.0)
        + (bathrooms * 18000.0)
        + (location_score * 25000.0)
        + ((year_built - 1965) * 850.0)
        + (condition_rating * 15000.0)
        + (garage_spaces * 14000.0)
        + np.random.normal(0, 22000.0, size=n_samples)
    )
    price = np.round(np.clip(price, 95000, 1500000), 2)

    df = pd.DataFrame({
        "square_feet": square_feet,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "location_score": location_score,
        "year_built": year_built,
        "condition_rating": condition_rating,
        "garage_spaces": garage_spaces,
        "price": price
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
