"""
Machine Learning Training Pipeline for Road Accident Severity Prediction.
Benchmarks Logistic Regression, Random Forest, and Gradient Boosting.
Calculates Precision, Recall, F1, Confusion Matrix, and ROC-AUC.
"""
from typing import Dict, Any, Tuple, Optional
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from dataset import (
    CATEGORICAL_COLUMNS,
    NUMERICAL_COLUMNS,
    SEVERITY_CLASSES,
    SEVERITY_MAPPING,
    generate_accident_dataset
)


class AccidentModelTrainer:
    def __init__(self):
        self.preprocessor: Optional[ColumnTransformer] = None
        self.best_pipeline: Optional[Pipeline] = None
        self.best_model_name: str = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self.feature_names = []

    def build_preprocessor(self) -> ColumnTransformer:
        return ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_COLUMNS),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLUMNS)
            ]
        )

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.25, random_state: int = 42) -> Tuple:
        feature_cols = NUMERICAL_COLUMNS + CATEGORICAL_COLUMNS
        X = df[feature_cols]
        y = df["severity"]

        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_accident_dataset(n_samples=1500)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_models = {
            "Logistic Regression": LogisticRegression(
                max_iter=1000, class_weight="balanced", random_state=42
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=100, max_depth=8, class_weight="balanced", random_state=42
            ),
            "Gradient Boosting": GradientBoostingClassifier(
                n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
            )
        }

        best_f1 = -1.0

        for name, clf in candidate_models.items():
            preprocessor = self.build_preprocessor()
            pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("clf", clf)
            ])

            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            y_prob = pipeline.predict_proba(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
            rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
            try:
                roc_auc = float(roc_auc_score(y_test, y_prob, multi_class="ovr", average="weighted"))
            except Exception:
                roc_auc = 0.0
            cm = confusion_matrix(y_test, y_pred).tolist()

            metrics = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "confusion_matrix": cm
            }
            self.model_metrics[name] = metrics

            if f1 > best_f1:
                best_f1 = f1
                self.best_pipeline = pipeline
                self.best_model_name = name

        return {
            "best_model_name": self.best_model_name,
            "best_f1_score": round(best_f1, 4),
            "model_metrics": self.model_metrics
        }

    def predict_scenario(self, incident_dict: Dict[str, Any]) -> Dict[str, Any]:
        if self.best_pipeline is None:
            self.train_and_compare()

        df_single = pd.DataFrame([incident_dict])
        pred_class_idx = int(self.best_pipeline.predict(df_single)[0])
        probabilities = self.best_pipeline.predict_proba(df_single)[0]

        return {
            "predicted_severity": SEVERITY_MAPPING.get(pred_class_idx, "Unknown"),
            "probabilities": {
                "Slight": round(float(probabilities[0]), 4),
                "Serious": round(float(probabilities[1]), 4),
                "Fatal": round(float(probabilities[2]), 4)
            }
        }
