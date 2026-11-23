"""
Plant Disease Inference Service with Agronomic Educational Information.
"""
from typing import Dict, Any, Union, Optional
import os
import cv2
import numpy as np
import torch
from model import PlantDiseaseCNN
from dataset import DISEASE_CLASSES, IDX_TO_CLASS


AGRONOMIC_GUIDE: Dict[str, Dict[str, str]] = {
    "Healthy Leaf": {
        "symptoms": "Vibrant uniform green pigmentation with clear, intact venation and no chlorosis or necrosis.",
        "treatment": "No treatment required. Maintain balanced nitrogen-potassium soil fertilization and drip irrigation.",
        "prevention": "Ensure adequate plant spacing for airflow and practice routine crop scouting."
    },
    "Bacterial Blight": {
        "symptoms": "Water-soaked lesions that rapidly darken to brown/black, frequently bordered by a chlorotic yellow halo.",
        "treatment": "Apply copper-based bactericides (e.g., copper hydroxide or copper sulfate). Remove and destroy severely infected foliage.",
        "prevention": "Avoid overhead sprinkler irrigation; disinfect pruning tools between plants; use certified pathogen-free seeds."
    },
    "Early Blight": {
        "symptoms": "Dark brown to black necrotic spots with characteristic concentric rings creating a 'target board' pattern.",
        "treatment": "Apply registered protective bio-fungicides (Bacillus subtilis) or broad-spectrum fungicides (Chlorothalonil/Mancozeb).",
        "prevention": "Practice 3-year crop rotation with non-solanaceous crops; mulch soil around stems to prevent rain splashback."
    },
    "Powdery Mildew": {
        "symptoms": "Superficial white talcum-like powdery fungal spots expanding over leaf surfaces, leading to curling and senescence.",
        "treatment": "Spray horticultural potassium bicarbonate, sulfur sprays, or neem oil solution upon first symptom detection.",
        "prevention": "Prune dense canopies to maximize sunlight penetration and reduce microclimate humidity."
    },
    "Leaf Rust": {
        "symptoms": "Small, raised reddish-orange or cinnamon-brown pustules on the lower leaf surface, releasing powdery spores.",
        "treatment": "Apply triazole or strobilurin-class fungicides at early onset. Isolate affected plot sections.",
        "prevention": "Plant resistant cultivars; eliminate alternative weed hosts around field margins."
    }
}


class PlantDiseaseClassifier:
    def __init__(self, weights_path: Optional[str] = "plant_disease_model.pth"):
        self.device = torch.device("cpu")
        self.model = PlantDiseaseCNN(num_classes=5).to(self.device)
        if weights_path and os.path.exists(weights_path):
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
        self.model.eval()

    def preprocess_image(self, img_input: Union[str, np.ndarray]) -> torch.Tensor:
        """
        Loads and resizes image to 64x64 RGB, normalizes to [0, 1].
        """
        if isinstance(img_input, str):
            if not os.path.exists(img_input):
                raise FileNotFoundError(f"Image not found: {img_input}")
            img = cv2.imread(img_input, cv2.IMREAD_COLOR)
        elif isinstance(img_input, np.ndarray):
            img = img_input
        else:
            raise ValueError("Input must be a valid file path or NumPy array.")

        resized = cv2.resize(img, (64, 64), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB) if len(img.shape) == 3 and img.shape[2] == 3 else resized
        norm = rgb.astype(np.float32) / 255.0
        tensor = torch.tensor(norm, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0)
        return tensor

    def predict(self, img_input: Union[str, np.ndarray]) -> Dict[str, Any]:
        tensor = self.preprocess_image(img_input).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

        pred_idx = int(np.argmax(probs))
        pred_disease = IDX_TO_CLASS[pred_idx]
        confidence = round(float(probs[pred_idx]) * 100, 2)

        distribution = {
            cls_name: round(float(probs[i]) * 100, 2)
            for i, cls_name in enumerate(DISEASE_CLASSES)
        }

        guide = AGRONOMIC_GUIDE.get(pred_disease, {})

        return {
            "predicted_disease": pred_disease,
            "confidence_percentage": confidence,
            "probability_distribution": distribution,
            "symptoms": guide.get("symptoms", "N/A"),
            "treatment_recommendation": guide.get("treatment", "N/A"),
            "preventative_measures": guide.get("prevention", "N/A"),
            "specialist_disclaimer": (
                "Agronomic Advisory: Computer vision predictions are automated diagnostic aids based on visual surface cues. "
                "Always confirm diagnosis with local agricultural extension specialists before applying chemical treatments."
            )
        }
