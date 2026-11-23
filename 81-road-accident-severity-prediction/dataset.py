"""
Road Accident Dataset Generator and Preprocessing Schema.
Generates multi-class historical road traffic accident records.
"""
import numpy as np
import pandas as pd


SEVERITY_CLASSES = ["Slight", "Serious", "Fatal"]
SEVERITY_MAPPING = {0: "Slight", 1: "Serious", 2: "Fatal"}

CATEGORICAL_COLUMNS = [
    "weather_condition",
    "road_surface",
    "road_type",
    "light_condition",
    "time_of_day",
    "vehicle_type",
    "driver_age_group"
]

NUMERICAL_COLUMNS = [
    "speed_limit",
    "vehicles_involved",
    "casualties"
]


def generate_accident_dataset(n_samples: int = 1500, seed: int = 42, output_csv: str = "accident_data.csv") -> pd.DataFrame:
    np.random.seed(seed)

    incident_refs = [f"ACC-{2024000 + i}" for i in range(n_samples)]
    weather = np.random.choice(["Clear", "Rainy", "Foggy", "Snowing"], p=[0.60, 0.25, 0.08, 0.07], size=n_samples)
    road_surface = np.random.choice(["Dry", "Wet", "Icy", "Flooded"], p=[0.62, 0.26, 0.09, 0.03], size=n_samples)
    road_type = np.random.choice(["Single carriageway", "Dual carriageway", "Roundabout", "Highway"], p=[0.45, 0.25, 0.15, 0.15], size=n_samples)
    light = np.random.choice(["Daylight", "Darkness - lights lit", "Darkness - no lights"], p=[0.60, 0.25, 0.15], size=n_samples)
    speed_limit = np.random.choice([30, 40, 50, 60, 70], p=[0.35, 0.20, 0.15, 0.15, 0.15], size=n_samples)
    time_of_day = np.random.choice(["Morning Rush", "Midday", "Evening Rush", "Night"], p=[0.25, 0.30, 0.30, 0.15], size=n_samples)
    vehicle_type = np.random.choice(["Car", "Motorcycle", "Truck", "Bus", "Bicycle"], p=[0.60, 0.15, 0.12, 0.08, 0.05], size=n_samples)
    driver_age_group = np.random.choice(["Young (17-24)", "Adult (25-54)", "Senior (55+)"], p=[0.25, 0.55, 0.20], size=n_samples)
    vehicles_involved = np.random.choice([1, 2, 3, 4], p=[0.45, 0.40, 0.10, 0.05], size=n_samples)
    casualties = np.random.choice([1, 2, 3], p=[0.75, 0.20, 0.05], size=n_samples)

    # Risk score calculation for severity assignment
    risk = np.zeros(n_samples)
    # Speed risk
    risk += (speed_limit - 30) * 0.035
    # Light condition risk
    risk += np.where(light == "Darkness - no lights", 0.7, np.where(light == "Darkness - lights lit", 0.25, 0.0))
    # Road surface risk
    risk += np.where(road_surface == "Icy", 0.6, np.where(road_surface == "Wet", 0.25, 0.0))
    # Weather risk
    risk += np.where(weather == "Foggy", 0.5, np.where(weather == "Snowing", 0.4, 0.0))
    # Vulnerable / heavy vehicle risk
    risk += np.where(vehicle_type == "Motorcycle", 0.8, np.where(vehicle_type == "Truck", 0.5, 0.0))
    # Casualties / vehicles
    risk += (casualties - 1) * 0.4 + (vehicles_involved - 1) * 0.2
    # Add random disturbance
    risk += np.random.normal(0, 0.35, size=n_samples)

    # Multi-class thresholds
    # Slight (approx 65%), Serious (approx 25%), Fatal (approx 10%)
    severity = np.where(risk > 1.6, 2, np.where(risk > 0.8, 1, 0))

    df = pd.DataFrame({
        "incident_ref": incident_refs,
        "weather_condition": weather,
        "road_surface": road_surface,
        "road_type": road_type,
        "light_condition": light,
        "speed_limit": speed_limit,
        "time_of_day": time_of_day,
        "vehicle_type": vehicle_type,
        "driver_age_group": driver_age_group,
        "vehicles_involved": vehicles_involved,
        "casualties": casualties,
        "severity": severity
    })

    if output_csv:
        df.to_csv(output_csv, index=False)
    return df
