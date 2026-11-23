"""
Employee Attrition Risk Assessment and HR Strategy Engine.
Classifies attrition probabilities into risk tiers and suggests retention interventions.
"""
from typing import Dict, Any, Optional
from model_trainer import EmployeeAttritionTrainer
import database


class AttritionPredictorService:
    def __init__(self, trainer: Optional[EmployeeAttritionTrainer] = None, db_path: str = database.DEFAULT_DB_PATH):
        self.trainer = trainer or EmployeeAttritionTrainer()
        if self.trainer.best_pipeline is None:
            self.trainer.train_and_compare()
        self.db_path = db_path

    def assess_risk_level(self, probability: float) -> str:
        if probability >= 0.65:
            return "High Risk"
        elif probability >= 0.35:
            return "Medium Risk"
        else:
            return "Low Risk"

    def formulate_retention_recommendations(self, emp: Dict[str, Any], risk_level: str, probability: float) -> str:
        actions = []
        sat = float(emp.get("satisfaction_score", 0.7))
        hours = int(emp.get("monthly_hours", 180))
        ot = emp.get("overtime", "No")
        salary = emp.get("salary_level", "Medium")
        tenure = int(emp.get("tenure_years", 2))
        promo = int(emp.get("promotion_last_5years", 0))

        if risk_level == "High Risk":
            if sat < 0.45:
                actions.append("Initiate immediate 1-on-1 engagement interview with People Operations")
            if hours > 240 or ot == "Yes":
                actions.append("Implement mandatory workload cap and reassign pending deliverables to reduce burnout")
            if salary == "Low":
                actions.append("Conduct off-cycle market compensation equity review")
            if tenure >= 3 and promo == 0:
                actions.append("Review career advancement pathway and potential promotion milestone")
            if not actions:
                actions.append("Assign executive mentor and arrange retention dialogue")
            return "; ".join(actions)

        elif risk_level == "Medium Risk":
            if ot == "Yes":
                actions.append("Monitor overtime hours and offer compensatory time-off")
            if sat < 0.60:
                actions.append("Schedule quarterly career satisfaction check-in")
            actions.append("Enroll in leadership development and skill enhancement tracks")
            return "; ".join(actions)

        else:
            return "Maintain standard performance recognition and annual development review."

    def evaluate_employee(self, emp: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        pred_class, prob = self.trainer.predict_employee(emp)
        risk_level = self.assess_risk_level(prob)
        recs = self.formulate_retention_recommendations(emp, risk_level, prob)

        record_id = None
        if persist:
            record_id = database.save_assessment(
                employee_id=emp.get("employee_id", "EMP-UNKNOWN"),
                department=emp.get("department", "Engineering"),
                tenure_years=int(emp.get("tenure_years", 2)),
                monthly_hours=int(emp.get("monthly_hours", 180)),
                satisfaction_score=float(emp.get("satisfaction_score", 0.7)),
                last_evaluation=float(emp.get("last_evaluation", 0.7)),
                promotion=int(emp.get("promotion_last_5years", 0)),
                salary_level=emp.get("salary_level", "Medium"),
                overtime=emp.get("overtime", "No"),
                probability=prob,
                risk_level=risk_level,
                recommendations=recs,
                db_path=self.db_path
            )

        return {
            "record_id": record_id,
            "employee_id": emp.get("employee_id", "EMP-UNKNOWN"),
            "predicted_attrition": bool(pred_class),
            "attrition_probability": prob,
            "attrition_percentage": f"{prob * 100:.1f}%",
            "risk_level": risk_level,
            "hr_recommendations": recs
        }
