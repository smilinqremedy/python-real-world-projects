"""
Customer Churn Risk Evaluator and Retention Strategy Engine.
Classifies customers into Risk Tiers and generates actionable retention recommendations.
"""
from typing import Dict, Any
from model_trainer import ChurnModelTrainer
from dataset import CONTRACT_MAPPING
import database


class ChurnPredictorService:
    def __init__(self, trainer: ChurnModelTrainer = None, db_path: str = database.DEFAULT_DB_PATH):
        self.trainer = trainer or ChurnModelTrainer()
        if self.trainer.best_model is None:
            self.trainer.train_and_compare()
        self.db_path = db_path

    def assess_risk_tier(self, probability: float) -> str:
        if probability >= 0.65:
            return "High"
        elif probability >= 0.35:
            return "Moderate"
        else:
            return "Low"

    def formulate_retention_strategy(self, customer_data: Dict[str, Any], risk_tier: str, probability: float) -> str:
        contract = customer_data.get("contract_type", "Month-to-month")
        tickets = customer_data.get("support_tickets", 0)
        delay = customer_data.get("payment_delay_days", 0)
        charges = customer_data.get("monthly_charges", 50.0)

        if risk_tier == "High":
            reasons = []
            if contract == "Month-to-month":
                reasons.append("Offer 25% discount on an annual commitment plan")
            if tickets >= 3:
                reasons.append("Escalate open support tickets to Senior Customer Success Manager")
            if delay > 5:
                reasons.append("Provide flexible billing cycle adjustment")
            if charges > 80:
                reasons.append("Review bundle optimization to lower perceived billing burden")
            if not reasons:
                reasons.append("Direct outreach by account retention executive with loyalty perk")
            return "; ".join(reasons)

        elif risk_tier == "Moderate":
            actions = ["Enroll in quarterly loyalty reward points"]
            if contract == "Month-to-month":
                actions.append("Present mid-term upgrade incentive")
            if customer_data.get("tech_support", 0) == 0:
                actions.append("Offer 3-month complimentary premium technical support")
            return "; ".join(actions)

        else:
            return "Maintain standard relationship check-ins; send satisfaction survey."

    def evaluate_customer(self, customer_data: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        # Map contract string if present
        features = dict(customer_data)
        if "contract_type" in features and "contract_type_code" not in features:
            features["contract_type_code"] = CONTRACT_MAPPING.get(features["contract_type"], 0)

        # Ensure total_charges
        if "total_charges" not in features:
            features["total_charges"] = features.get("tenure_months", 1) * features.get("monthly_charges", 50.0)

        prob = self.trainer.predict_churn_probability(features)
        tier = self.assess_risk_tier(prob)
        strategy = self.formulate_retention_strategy(customer_data, tier, prob)

        record_id = None
        if persist:
            record_id = database.save_prediction(
                customer_id=customer_data.get("customer_id", "UNKNOWN"),
                tenure_months=int(customer_data.get("tenure_months", 1)),
                contract_type=customer_data.get("contract_type", "Month-to-month"),
                monthly_charges=float(customer_data.get("monthly_charges", 50.0)),
                support_tickets=int(customer_data.get("support_tickets", 0)),
                payment_delay_days=int(customer_data.get("payment_delay_days", 0)),
                churn_probability=prob,
                risk_tier=tier,
                retention_strategy=strategy,
                db_path=self.db_path
            )

        return {
            "record_id": record_id,
            "customer_id": customer_data.get("customer_id", "UNKNOWN"),
            "churn_probability": prob,
            "churn_percentage": f"{prob * 100:.1f}%",
            "risk_tier": tier,
            "retention_strategy": strategy
        }
