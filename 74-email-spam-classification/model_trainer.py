"""
Model Training Pipeline with TF-IDF Vectorization.
Trains and compares Multinomial Naive Bayes, Logistic Regression, and Random Forest.
"""
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from preprocessor import clean_text
from dataset import generate_spam_dataset


class SpamModelTrainer:
    def __init__(self):
        self.best_pipeline: Optional[Pipeline] = None
        self.best_model_name: str = ""
        self.model_metrics: Dict[str, Dict[str, Any]] = {}

    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.25, random_state: int = 42) -> Tuple:
        cleaned_messages = [clean_text(msg) for msg in df["message"]]
        y = df["is_spam"]

        return train_test_split(cleaned_messages, y, test_size=test_size, random_state=random_state, stratify=y)

    def train_and_compare(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if df is None:
            df = generate_spam_dataset(n_samples=1000)

        X_train, X_test, y_train, y_test = self.prepare_data(df)

        candidate_classifiers = {
            "Multinomial Naive Bayes": MultinomialNB(alpha=0.5),
            "Logistic Regression": LogisticRegression(random_state=42),
            "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        }

        best_f1 = -1.0

        for name, clf in candidate_classifiers.items():
            pipe = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=3000)),
                ("clf", clf)
            ])
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, zero_division=0))
            rec = float(recall_score(y_test, y_pred, zero_division=0))
            f1 = float(f1_score(y_test, y_pred, zero_division=0))
            cm = confusion_matrix(y_test, y_pred).tolist()

            metrics = {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "confusion_matrix": cm
            }
            self.model_metrics[name] = metrics

            if f1 > best_f1:
                best_f1 = f1
                self.best_pipeline = pipe
                self.best_model_name = name

        return {
            "best_model_name": self.best_model_name,
            "best_f1_score": round(best_f1, 4),
            "model_metrics": self.model_metrics
        }

    def predict_message(self, text: str) -> Tuple[bool, float]:
        if self.best_pipeline is None:
            self.train_and_compare()

        cleaned = clean_text(text)
        prob = float(self.best_pipeline.predict_proba([cleaned])[0][1])
        is_spam = prob >= 0.50
        return is_spam, round(prob, 4)
