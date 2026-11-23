"""
Inference & Risk Categorization Service for Bank Loan Default Prediction.
Evaluates borrower loan applications, categorizes credit risk tiers, and logs underwriting records.
"""
from datetime import datetime
import secrets
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from database import get_connection, init_db
from dataset import FEATURE_COLUMNS
from model_trainer import LoanModelTrainer


class LoanPredictorService:
    DISCLAIMER = (
        "NOTICE: Model predictions provide advisory risk estimation metrics and "
        "must not be used as an automated loan approval or denial decision."
    )

    def __init__(self, trainer: Optional[LoanModelTrainer] = None, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)
        self.trainer = trainer or LoanModelTrainer(self.db_path)
        if self.trainer.best_model is None:
            self.trainer.train_and_compare()

    def _get_connection(self):
        return get_connection(self.db_path)

    @staticmethod
    def classify_risk_tier(prob: float) -> Tuple[str, str]:
        if prob < 0.25:
            return "Low Risk", "Strong credit profile. Eligible for standard credit terms."
        elif prob <= 0.55:
            return "Medium Risk", "Moderate credit risk. Manual underwriting review and income verification recommended."
        else:
            return "High Risk", "Elevated default probability. Additional collateral or secondary guarantor required."

    def predict_application(self, applicant_name: str, annual_income: float,
                            loan_amount: float, interest_rate: float,
                            employment_years: int, debt_to_income: float,
                            credit_score: int, previous_defaults: int = 0) -> Dict[str, Any]:
        """
        Evaluate loan application and persist result in SQLite database.
        """
        input_dict = {
            "annual_income": float(annual_income),
            "loan_amount": float(loan_amount),
            "interest_rate": float(interest_rate),
            "employment_years": int(employment_years),
            "debt_to_income": float(debt_to_income),
            "credit_score": int(credit_score),
            "previous_defaults": int(previous_defaults)
        }

        df_input = pd.DataFrame([input_dict])[FEATURE_COLUMNS]
        scaled_input = self.trainer.scaler.transform(df_input)

        # Predict probability of class 1 (default)
        prob = float(self.trainer.best_model.predict_proba(scaled_input)[0][1])
        prob_rounded = round(prob, 4)

        risk_tier, rec = self.classify_risk_tier(prob_rounded)

        # Generate unique application ref
        today_tag = datetime.now().strftime("%Y%m%d")
        seq = secrets.randbelow(9000) + 1000
        app_ref = f"LOAN-{today_tag}-{seq}"

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO loan_applications (
                        application_ref, applicant_name, annual_income, loan_amount,
                        interest_rate, employment_years, debt_to_income, credit_score,
                        previous_defaults, default_probability, risk_category, underwriting_recommendation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        app_ref, applicant_name.strip(), annual_income, loan_amount,
                        interest_rate, employment_years, debt_to_income, credit_score,
                        previous_defaults, prob_rounded, risk_tier, rec
                    )
                )
                app_id = cursor.lastrowid

            return {
                "application_id": app_id,
                "application_ref": app_ref,
                "applicant_name": applicant_name,
                "default_probability": prob_rounded,
                "default_probability_percentage": f"{prob_rounded * 100:.1f}%",
                "risk_category": risk_tier,
                "model_used": self.trainer.best_model_name,
                "recommendation": rec,
                "disclaimer": self.DISCLAIMER
            }
        finally:
            conn.close()

    def get_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM loan_applications ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
