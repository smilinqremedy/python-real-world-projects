"""
Regression Model Training Pipeline for House Price Prediction.
Trains, evaluates, and compares Linear Regression, Decision Tree, and Random Forest.
Computes MAE, MSE, RMSE, R2, and feature importance rankings.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from dataset import FEATURE_COLUMNS, generate_housing_dataset


class HousePriceModelTrainer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self.feature_importances: Dict[str, float] = {}

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple:
        X = df[FEATURE_COLUMNS]
        y = df["price"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_housing_dataset(n_samples=1000)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_models = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(max_depth=6, random_state=42),
            "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
        }

        best_r2 = -float("inf")

        for name, reg in candidate_models.items():
            reg.fit(X_train, y_train)
            y_pred = reg.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            mse = float(mean_squared_error(y_test, y_pred))
            rmse = float(np.sqrt(mse))
            r2 = float(r2_score(y_test, y_pred))

            metrics = {
                "mae": round(mae, 2),
                "mse": round(mse, 2),
                "rmse": round(rmse, 2),
                "r2_score": round(r2, 4)
            }
            self.model_metrics[name] = metrics

            if r2 > best_r2:
                best_r2 = r2
                self.best_model = reg
                self.best_model_name = name

        # Extract feature importance from Random Forest
        rf = candidate_models["Random Forest"]
        importances = rf.feature_importances_
        self.feature_importances = {
            col: round(float(imp), 4) for col, imp in zip(FEATURE_COLUMNS, importances)
        }

        return {
            "best_model_name": self.best_model_name,
            "best_r2_score": round(best_r2, 4),
            "model_metrics": self.model_metrics,
            "feature_importances": self.feature_importances
        }

    def predict_price(self, property_dict: Dict[str, Any]) -> float:
        if self.best_model is None:
            self.train_and_compare()

        df_single = pd.DataFrame([property_dict])[FEATURE_COLUMNS]
        scaled = self.scaler.transform(df_single)
        pred = float(self.best_model.predict(scaled)[0])
        return round(pred, 2)
