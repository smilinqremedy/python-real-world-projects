"""
Email Spam Classification Service.
Coordinates text cleaning, feature extraction, ML inference, and SQLite auditing.
"""
from typing import Dict, Any, Optional
from model_trainer import SpamModelTrainer
from preprocessor import extract_spam_keywords
import database


class SpamClassifierService:
    def __init__(self, trainer: Optional[SpamModelTrainer] = None, db_path: str = database.DEFAULT_DB_PATH):
        self.trainer = trainer or SpamModelTrainer()
        if self.trainer.best_pipeline is None:
            self.trainer.train_and_compare()
        self.db_path = db_path

    def classify_email(self, text: str, subject: str = "", persist: bool = True) -> Dict[str, Any]:
        full_content = f"{subject} {text}".strip()
        is_spam, probability = self.trainer.predict_message(full_content)
        flagged_keywords = extract_spam_keywords(full_content)

        # Keyword boost: if multiple strong spam words appear, adjust probability floor
        if len(flagged_keywords) >= 2 and probability < 0.5:
            probability = max(probability, 0.55)
            is_spam = True

        record_id = None
        if persist:
            record_id = database.save_scan(
                subject=subject,
                body=text,
                is_spam=is_spam,
                spam_probability=probability,
                flagged_keywords=flagged_keywords,
                db_path=self.db_path
            )

        confidence = round((probability if is_spam else (1.0 - probability)) * 100, 1)

        return {
            "record_id": record_id,
            "subject": subject,
            "is_spam": is_spam,
            "classification": "SPAM" if is_spam else "HAM (Legitimate)",
            "spam_probability": probability,
            "confidence_percent": confidence,
            "flagged_keywords": flagged_keywords
        }
