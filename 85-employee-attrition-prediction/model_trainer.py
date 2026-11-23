"""
Model Training Pipeline for Employee Attrition Prediction.
Trains and benchmarks Logistic Regression, Random Forest, and Gradient Boosting.
Computes Accuracy, Precision, Recall, F1, ROC-AUC, and feature importance.
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
    generate_employee_dataset
)


class EmployeeAttritionTrainer:
    def __init__(self):
        self.preprocessor: Optional[ColumnTransformer] = None
        self.best_pipeline: Optional[Pipeline] = None
        self.best_model_name: str = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self.feature_importances: Dict[str, float] = {}

    def build_preprocessor(self) -> ColumnTransformer:
        return ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), NUMERICAL_COLUMNS),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_COLUMNS)
            ]
        )

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.25, random_state: int = 42) -> Tuple:
        features = NUMERICAL_COLUMNS + CATEGORICAL_COLUMNS
        X = df[features]
        y = df["attrition"]

        return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_employee_dataset(n_samples=1500)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=7, class_weight="balanced", random_state=42),
            "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
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
            y_prob = pipeline.predict_proba(X_test)[:, 1]

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            roc_auc = float(roc_auc_score(y_test, y_prob))
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

        # Extract top feature importances from Random Forest
        rf_pipeline = Pipeline([
            ("preprocessor", self.build_preprocessor()),
            ("clf", candidate_models["Random Forest"])
        ])
        rf_pipeline.fit(X_train, y_train)
        encoded_cat_names = rf_pipeline.named_steps["preprocessor"].transformers_[1][1].get_feature_names_out(CATEGORICAL_COLUMNS).tolist()
        all_feature_names = NUMERICAL_COLUMNS + encoded_cat_names
        importances = rf_pipeline.named_steps["clf"].feature_importances_
        self.feature_importances = {
            feat: round(float(imp), 4)
            for feat, imp in zip(all_feature_names, importances)
        }

        return {
            "best_model_name": self.best_model_name,
            "best_f1_score": round(best_f1, 4),
            "model_metrics": self.model_metrics,
            "feature_importances": self.feature_importances
        }

    def predict_employee(self, emp_dict: Dict[str, Any]) -> Tuple[int, float]:
        if self.best_pipeline is None:
            self.train_and_compare()

        df_single = pd.DataFrame([emp_dict])
        pred_class = int(self.best_pipeline.predict(df_single)[0])
        prob = float(self.best_pipeline.predict_proba(df_single)[0][1])
        return pred_class, round(prob, 4)
