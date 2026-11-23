"""
Machine Learning Training Pipeline for Bank Loan Default Prediction.
Trains and evaluates Logistic Regression, Decision Tree, and Random Forest classifiers.
Computes Precision, Recall, F1-Score, Confusion Matrix, and ROC-AUC.
"""
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from database import get_connection, init_db
from dataset import FEATURE_COLUMNS, generate_loan_dataset


class LoanModelTrainer:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        init_db(self.db_path)
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}

    def _get_connection(self):
        return get_connection(self.db_path)

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple:
        X = df[FEATURE_COLUMNS]
        y = df["default"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_loan_dataset(n_samples=1200)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_models = {
            "Logistic Regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
            "Decision Tree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=42)
        }

        conn = self._get_connection()
        best_auc = -1.0

        for name, clf in candidate_models.items():
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            y_proba = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else y_pred

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            roc_auc = float(roc_auc_score(y_test, y_proba))
            cm = confusion_matrix(y_test, y_pred).tolist()

            metrics = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
                "confusion_matrix": cm,
            }
            self.model_metrics[name] = metrics

            # Record in SQLite
            try:
                with conn:
                    conn.execute(
                        """
                        INSERT INTO model_metrics (model_name, accuracy, precision_val, recall_val, f1_val, roc_auc)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (name, acc, prec, rec, f1, roc_auc)
                    )
            except Exception:
                pass

            if roc_auc > best_auc:
                best_auc = roc_auc
                self.best_model = clf
                self.best_model_name = name

        conn.close()

        return {
            "best_model_name": self.best_model_name,
            "best_roc_auc": round(best_auc, 4),
            "all_model_metrics": self.model_metrics
        }
