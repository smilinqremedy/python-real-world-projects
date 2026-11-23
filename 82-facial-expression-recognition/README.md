# Project 82: Facial Expression Recognition System

A Computer Vision and Deep Learning application that classifies human facial expressions using Convolutional Neural Networks (CNN) in PyTorch.

## Real-World Problem
Computer vision systems in human-computer interaction, accessibility tools, and digital media analyze visible facial features to recognize facial gestures. Responsible AI requires acknowledging that surface expressions cannot definitively verify internal emotional states.

## Key Features
- **Facial Image Preprocessing**: Grayscale conversion, automated face alignment/resizing to standard 48x48 resolution, and float pixel normalization.
- **Deep Convolutional Architecture**: 3-stage Conv2D feature extractor with Batch Normalization, ReLU activations, and Max-Pooling coupled with Adaptive Average Pooling and Dropout regularization.
- **Model Evaluation**: Accuracy, Precision, Recall, Weighted F1-score, and 5-class Confusion Matrix.
- **Multi-Class Output**: Classifies `Angry`, `Happy`, `Neutral`, `Sad`, and `Surprise` with confidence distributions.
- **Ethics & Psychological Advisory**: Clarifies demographic variance and the distinction between visible expression vs. true internal emotions.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `dataset.py`: Synthetic facial expression dataset generator and PyTorch DataLoader pipeline.
- `model.py`: PyTorch `FacialExpressionCNN` architecture.
- `trainer.py`: PyTorch training loop, optimization, and validation evaluation.
- `classifier.py`: OpenCV image loading, inference service, and ethics advisory.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_fer.py`: Automated unit tests.

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
python3 -m unittest test_fer.py -v
```
