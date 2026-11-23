"""
Machine Learning Model Training Pipeline for Customer Churn Prediction.
Compares Logistic Regression, Decision Tree, and Random Forest.
Computes Accuracy, Precision, Recall, F1, and ROC-AUC.
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from dataset import FEATURE_COLUMNS, generate_churn_dataset


class ChurnModelTrainer:
    def __init__(self):
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}
        self.feature_importances: Dict[str, float] = {}

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.25, random_state: int = 42) -> Tuple:
        X = df[FEATURE_COLUMNS]
        y = df["churn"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_churn_dataset(n_samples=1200)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_models = {
            "Logistic Regression": LogisticRegression(class_weight="balanced", random_state=42),
            "Decision Tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=42)
        }

        best_f1 = -1.0

        for name, clf in candidate_models.items():
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred

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
                self.best_model = clf
                self.best_model_name = name

        rf = candidate_models["Random Forest"]
        importances = rf.feature_importances_
        self.feature_importances = {
            col: round(float(imp), 4) for col, imp in zip(FEATURE_COLUMNS, importances)
        }

        return {
            "best_model_name": self.best_model_name,
            "best_f1_score": round(best_f1, 4),
            "model_metrics": self.model_metrics,
            "feature_importances": self.feature_importances
        }

    def predict_churn_probability(self, customer_features: Dict[str, Any]) -> float:
        if self.best_model is None:
            self.train_and_compare()

        df_single = pd.DataFrame([customer_features])[FEATURE_COLUMNS]
        scaled = self.scaler.transform(df_single)
        prob = float(self.best_model.predict_proba(scaled)[0][1])
        return round(prob, 4)
