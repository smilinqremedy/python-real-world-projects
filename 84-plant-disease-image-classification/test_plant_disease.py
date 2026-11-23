"""
Unit Tests for Plant Disease Image Classification System.
"""
import unittest
import os
import numpy as np
import torch
from dataset import synthesize_leaf_image, apply_augmentation, create_plant_dataloaders, DISEASE_CLASSES
from model import PlantDiseaseCNN
from trainer import PlantDiseaseTrainer
from classifier import PlantDiseaseClassifier


class TestPlantDiseaseClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.weights_path = "test_plant_model.pth"
        cls.train_loader, cls.test_loader, _, _ = create_plant_dataloaders(samples_per_class=40, batch_size=16, seed=77)
        cls.trainer = PlantDiseaseTrainer(num_classes=5)
        cls.trainer.train_model(cls.train_loader, epochs=6)
        cls.trainer.save_weights(cls.weights_path)
        cls.classifier = PlantDiseaseClassifier(weights_path=cls.weights_path)

    @classmethod
    def tearDownClass(cls):
        for f in [cls.weights_path, "plant_disease_model.pth", "sample_leaf_test.png"]:
            if os.path.exists(f):
                os.remove(f)

    def test_leaf_synthesis_and_augmentation(self):
        img = synthesize_leaf_image("Early Blight", seed=10)
        self.assertEqual(img.shape, (64, 64, 3))
        aug = apply_augmentation(img)
        self.assertEqual(aug.shape, (64, 64, 3))

    def test_cnn_architecture(self):
        model = PlantDiseaseCNN(num_classes=5)
        dummy_tensor = torch.randn(2, 3, 64, 64)
        out = model(dummy_tensor)
        self.assertEqual(out.shape, (2, 5))

    def test_model_evaluation(self):
        metrics = self.trainer.evaluate_model(self.test_loader)
        self.assertIn("accuracy", metrics)
        self.assertIn("f1_score", metrics)
        self.assertGreater(metrics["accuracy"], 0.70)
        self.assertGreater(metrics["f1_score"], 0.70)

    def test_classifier_inference_and_agronomic_guide(self):
        test_img = synthesize_leaf_image("Powdery Mildew", seed=44)
        res = self.classifier.predict(test_img)
        self.assertIn(res["predicted_disease"], DISEASE_CLASSES)
        self.assertIn("treatment_recommendation", res)
        self.assertIn("symptoms", res)
        self.assertIn("agricultural extension", res["specialist_disclaimer"].lower())


if __name__ == "__main__":
    unittest.main()
