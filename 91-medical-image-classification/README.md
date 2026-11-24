# Project 91: AI-Based Medical Image Classification System

## Clinical Safety Advisory & Regulatory Notice

> [!WARNING]
> **EXPERIMENTAL CLINICAL SCREENING AID ONLY — NOT A DIAGNOSTIC DEVICE:**
> This software system is developed exclusively for academic, research, and technical evaluation purposes. The predictions and probability scores produced by the underlying convolutional neural network do NOT constitute a medical diagnosis, clinical opinion, or therapeutic prescription. This tool must not be used as a standalone diagnostic device or to substitute the certified clinical examination of a licensed healthcare physician or radiologist.

---

## Overview

The **AI-Based Medical Image Classification System** is an end-to-end deep learning solution for automated screening of chest radiography images (detecting patterns consistent with Normal pulmonary fields versus Pneumonic consolidations). The solution provides:

1. **Modular Deep Learning Architecture:** Convolutional Neural Network (CNN) featuring convolutional filtering, spatial pooling, zero-mean normalization, and fully connected classification heads.
2. **Clinical Safety & Auditability:** Every classification automatically logs an audit trail (timestamp, image SHA-256 hash, predicted class, probability scores, user notes) to a secure SQLite database.
3. **Web Interface (Streamlit):** Upload radiographic imagery, visualize probability distributions across classes, and inspect historical screening logs.
4. **Command-Line Interface (CLI):** Full capabilities to train, evaluate, generate synthetic benchmark datasets, and classify individual images.

---

## Architecture

```text
91-medical-image-classification/
├── app.py                         # Streamlit web interface
├── classifier.py                  # Service layer with safety checks & logging
├── database.py                    # SQLite audit trail & prediction history
├── dataset.py                     # Ingestion, validation, preprocessing, synthetic data generator
├── evaluator.py                   # Accuracy, Precision, Recall, Specificity, F1, Confusion Matrix
├── main.py                        # CLI entrypoint
├── model.py                       # Convolutional Neural Network (CNN) architecture
├── requirements.txt               # Dependencies
├── test_medical_classification.py # Automated test suite
├── trainer.py                     # Training loop, validation checkpoints, and weights saving
└── README.md                      # Documentation
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 91-medical-image-classification
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Generate Synthetic Benchmark Dataset
Create synthetic radiographic images with realistic anatomical contours and opacity patterns:
```bash
python3 main.py --generate-samples ./sample_dataset --samples-count 20
```

### 2. Train the CNN Model
Train on the generated dataset and save model weights:
```bash
python3 main.py --train ./sample_dataset --epochs 5 --weights-out medical_cnn_weights.npz
```

### 3. Screen a Medical Image via CLI
Run classification on an image:
```bash
python3 main.py --predict ./sample_dataset/Normal/normal_001.png --weights medical_cnn_weights.npz
```

### 4. Review Audit History
```bash
python3 main.py --history
```

### 5. Launch the Streamlit Web UI
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite using `unittest`:
```bash
python3 -m unittest test_medical_classification.py -v
```
