"""
PyTorch Training and Evaluation Pipeline for Facial Expression CNN.
Computes Accuracy, Precision, Recall, F1, and Confusion Matrix.
"""
from typing import Dict, Any, Tuple
import os
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from model import FacialExpressionCNN
from dataset import create_expression_dataloaders, EXPRESSION_CLASSES


class FERModelTrainer:
    def __init__(self, num_classes: int = 5, lr: float = 0.003):
        self.device = torch.device("cpu")
        self.model = FacialExpressionCNN(num_classes=num_classes).to(self.device)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.metrics: Dict[str, Any] = {}

    def train_model(self, train_loader, epochs: int = 10) -> list:
        self.model.train()
        loss_history = []
        for epoch in range(epochs):
            running_loss = 0.0
            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                self.optimizer.zero_grad()
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
                running_loss += loss.item() * images.size(0)
            epoch_loss = running_loss / len(train_loader.dataset)
            loss_history.append(round(epoch_loss, 4))
        return loss_history

    def evaluate_model(self, test_loader) -> Dict[str, Any]:
        self.model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for images, labels in test_loader:
                images = images.to(self.device)
                outputs = self.model(images)
                _, preds = torch.max(outputs, 1)
                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels.numpy().tolist())

        acc = float(accuracy_score(all_labels, all_preds))
        prec = float(precision_score(all_labels, all_preds, average="weighted", zero_division=0))
        rec = float(recall_score(all_labels, all_preds, average="weighted", zero_division=0))
        f1 = float(f1_score(all_labels, all_preds, average="weighted", zero_division=0))
        cm = confusion_matrix(all_labels, all_preds).tolist()

        self.metrics = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "classes": EXPRESSION_CLASSES
        }
        return self.metrics

    def save_weights(self, path: str = "facial_expression_model.pth"):
        torch.save(self.model.state_dict(), path)

    def load_weights(self, path: str = "facial_expression_model.pth"):
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.model.eval()
