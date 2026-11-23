"""
Facial Expression Classifier Inference Service with Bias & Ethics Advisory.
"""
from typing import Dict, Any, Union, Optional
import os
import cv2
import numpy as np
import torch
from model import FacialExpressionCNN
from dataset import EXPRESSION_CLASSES, IDX_TO_CLASS


class FacialExpressionClassifier:
    def __init__(self, weights_path: Optional[str] = "facial_expression_model.pth"):
        self.device = torch.device("cpu")
        self.model = FacialExpressionCNN(num_classes=5).to(self.device)
        if weights_path and os.path.exists(weights_path):
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.eval()

    def preprocess_image(self, img_input: Union[str, np.ndarray]) -> torch.Tensor:
        """
        Accepts filepath or numpy array. Converts to 48x48 grayscale normalized tensor.
        """
        if isinstance(img_input, str):
            if not os.path.exists(img_input):
                raise FileNotFoundError(f"Image file not found: {img_input}")
            img = cv2.imread(img_input, cv2.IMREAD_GRAYSCALE)
        elif isinstance(img_input, np.ndarray):
            if len(img_input.shape) == 3:
                img = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
            else:
                img = img_input
        else:
            raise ValueError("Input must be a valid file path or NumPy array.")

        resized = cv2.resize(img, (48, 48), interpolation=cv2.INTER_AREA)
        norm = resized.astype(np.float32) / 255.0
        tensor = torch.tensor(norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        return tensor

    def predict(self, img_input: Union[str, np.ndarray]) -> Dict[str, Any]:
        tensor = self.preprocess_image(img_input).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx = int(np.argmax(probs))
        pred_label = IDX_TO_CLASS[pred_idx]
        confidence = round(float(probs[pred_idx]) * 100, 2)

        distribution = {
            cls_name: round(float(probs[i]) * 100, 2)
            for i, cls_name in enumerate(EXPRESSION_CLASSES)
        }

        return {
            "predicted_expression": pred_label,
            "confidence_percentage": confidence,
            "probability_distribution": distribution,
            "ethics_notice": (
                "Demographic & Psychological Advisory: Facial expression recognition classifies visible superficial surface "
                "geometry. It CANNOT establish a person's authentic internal psychological or emotional state. Models "
                "may exhibit demographic disparity across age, race, and lighting variations."
            )
        }
