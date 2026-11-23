# Project 84: Plant Disease Image Classification System

A Computer Vision and Agricultural Machine Learning application that detects plant leaf diseases from images using Convolutional Neural Networks (CNN) in PyTorch.

## Real-World Problem
Crop diseases cause severe agricultural yield losses and threaten food security worldwide. Early and automated visual leaf pathology detection helps farmers apply timely remedies, prevent broad epidemic spread, and optimize fungicide use.

## Key Features
- **Pathology Signatures & Augmentation**: Captures healthy leaves, bacterial blight (water-soaked necrotic lesions), early blight (concentric target board rings), powdery mildew (fungal spores), and leaf rust (cinnamon pustules). Applies random geometric and photometric augmentations.
- **Deep Convolutional Architecture**: 3-stage Conv2D feature extractor with Batch Normalization, ReLU activations, Max-Pooling, Adaptive Average Pooling, and Dropout regularization.
- **Model Evaluation**: Accuracy, Precision, Recall, Weighted F1-Score, and 5-class Confusion Matrix.
- **Agronomic Actionable Intelligence**: Provides tailored treatment protocols (organic and chemical fungicides) and preventative cultural practices for every detected condition.
- **Specialist Advisory Notice**: Clarifies diagnostic scope and emphasizes confirmation with local agricultural extension officers.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `dataset.py`: Synthetic plant leaf dataset generator and PyTorch DataLoader pipeline with augmentation.
- `model.py`: PyTorch `PlantDiseaseCNN` architecture.
- `trainer.py`: PyTorch training loop and validation evaluation.
- `classifier.py`: OpenCV preprocessing, disease classification, and agronomic guidance.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_plant_disease.py`: Automated unit tests.

## Running the Application
### Interactive CLI
```bash
python3 main.py
```

### Streamlit Web Dashboard
```bash
streamlit run app.py
```

### Running Unit Tests
```bash
python3 -m unittest test_plant_disease.py -v
```
