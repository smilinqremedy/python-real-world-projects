"""
High-Level Medical Image Classifier Service.
Enforces clinical safety disclaimers, input validation, and history logging.
"""
import os
from typing import Dict, Any, Optional
import numpy as np
from dataset import preprocess_image, validate_image_file, CLASSES
from model import MedicalCNN
import database

# Mandatory Clinical Safety Warning
CLINICAL_SAFETY_DISCLAIMER = (
    "NOTICE: This AI-based medical image screening tool is experimental and intended "
    "solely for educational and research assistance. It is NOT a certified medical diagnostic "
    "device and does NOT replace the clinical judgment, diagnosis, or treatment plan of a "
    "licensed healthcare physician or radiologist."
)


class MedicalClassifierService:
    def __init__(self, weights_path: Optional[str] = None, db_path: str = database.DEFAULT_DB_PATH):
        self.db_path = db_path
        self.model = MedicalCNN(in_channels=1, num_classes=2)
        if weights_path and os.path.exists(weights_path):
            self.model.load_weights(weights_path)
        self.weights_path = weights_path

    def classify_image(self, image_path: str, user_notes: str = "") -> Dict[str, Any]:
        """
        Classifies an input medical image (e.g. chest X-ray),
        returns predicted classification, probabilities, confidence,
        audit log ID, and the required clinical safety disclaimer.
        """
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"Image file not found: {image_path}",
                "disclaimer": CLINICAL_SAFETY_DISCLAIMER
            }

        if not validate_image_file(image_path):
            return {
                "success": False,
                "error": "File is corrupted, empty, or not a recognized valid image format.",
                "disclaimer": CLINICAL_SAFETY_DISCLAIMER
            }

        try:
            tensor = preprocess_image(image_path)
            # Add batch dimension: (1, 1, H, W)
            if tensor.ndim == 3:
                tensor = np.expand_dims(tensor, axis=0)
            preds, probs = self.model.predict(tensor)

            pred_idx = int(preds[0])
            pred_class = CLASSES[pred_idx]
            normal_prob = float(probs[0, 0])
            pneumonia_prob = float(probs[0, 1])
            confidence = float(np.max(probs[0]))

            # Log prediction to database
            image_name = os.path.basename(image_path)
            log_id = database.log_prediction(
                image_name=image_name,
                file_path=image_path,
                predicted_class=pred_class,
                confidence_score=round(confidence, 4),
                normal_prob=round(normal_prob, 4),
                pneumonia_prob=round(pneumonia_prob, 4),
                db_path=self.db_path,
                user_notes=user_notes
            )

            return {
                "success": True,
                "predicted_class": pred_class,
                "confidence_score": round(confidence, 4),
                "probabilities": {
                    "Normal": round(normal_prob, 4),
                    "Pneumonia": round(pneumonia_prob, 4)
                },
                "log_id": log_id,
                "image_name": image_name,
                "is_experimental": True,
                "disclaimer": CLINICAL_SAFETY_DISCLAIMER
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Classification error: {str(e)}",
                "disclaimer": CLINICAL_SAFETY_DISCLAIMER
            }
