"""
Road Accident Severity Predictor and Safety Recommendation Engine.
Analyzes road safety risk factors, limitations, and countermeasures.
"""
from typing import Dict, Any, Optional
from model_trainer import AccidentModelTrainer
import database


class AccidentSeverityPredictorService:
    def __init__(self, trainer: Optional[AccidentModelTrainer] = None, db_path: str = database.DEFAULT_DB_PATH):
        self.trainer = trainer or AccidentModelTrainer()
        if self.trainer.best_pipeline is None:
            self.trainer.train_and_compare()
        self.db_path = db_path

    def formulate_recommendations(self, incident: Dict[str, Any], severity: str, probs: Dict[str, float]) -> str:
        recs = []
        speed = incident.get("speed_limit", 30)
        light = incident.get("light_condition", "")
        surface = incident.get("road_surface", "")
        vtype = incident.get("vehicle_type", "")

        if speed >= 60:
            recs.append("Implement automated speed enforcement / radar speed display cameras")
        if "no lights" in light.lower():
            recs.append("Install street illumination or high-visibility reflective road cat-eyes")
        if surface in ["Icy", "Wet", "Flooded"]:
            recs.append("Apply anti-skid friction resurfacing and install active electronic slippery-surface warnings")
        if vtype in ["Motorcycle", "Bicycle"]:
            recs.append("Evaluate dedicated cycle/motorcycle segregation corridors and mandatory helmet enforcement")
        if severity == "Fatal" or probs.get("Fatal", 0) > 0.25:
            recs.append("Conduct comprehensive road safety audit and reduce corridor posted speed limit by 10 mph")

        if not recs:
            recs.append("Maintain routine road maintenance and standard traffic surveillance.")
        return "; ".join(recs)

    def evaluate_incident(self, incident: Dict[str, Any], incident_ref: str = "ACC-SIMULATED", persist: bool = True) -> Dict[str, Any]:
        pred = self.trainer.predict_scenario(incident)
        severity = pred["predicted_severity"]
        probs = pred["probabilities"]
        recommendations = self.formulate_recommendations(incident, severity, probs)

        record_id = None
        if persist:
            record_id = database.save_prediction(
                incident_ref=incident_ref,
                weather=incident.get("weather_condition", "Clear"),
                road_surface=incident.get("road_surface", "Dry"),
                light=incident.get("light_condition", "Daylight"),
                speed_limit=int(incident.get("speed_limit", 30)),
                vehicle_type=incident.get("vehicle_type", "Car"),
                predicted_severity=severity,
                fatal_prob=probs.get("Fatal", 0.0),
                serious_prob=probs.get("Serious", 0.0),
                slight_prob=probs.get("Slight", 0.0),
                safety_recommendations=recommendations,
                db_path=self.db_path
            )

        return {
            "record_id": record_id,
            "incident_ref": incident_ref,
            "predicted_severity": severity,
            "probabilities": probs,
            "safety_recommendations": recommendations,
            "limitations_notice": (
                "Notice: Model estimates are probabilistic risk indications derived from historical patterns. "
                "They do not constitute deterministic accident certainty and cannot replace forensic crash reconstruction."
            )
        }
