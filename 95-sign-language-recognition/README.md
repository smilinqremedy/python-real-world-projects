# Project 95: AI-Powered Sign Language Recognition System

## Ethical Scope, Linguistic Complexity & Regional Variations

> [!IMPORTANT]
> **NATURAL SIGN LANGUAGE COMPLEXITY & ETHICAL DISCLAIMER:**
> 1. **Complete Languages vs Isolated Gestures:** Natural sign languages (such as American Sign Language - ASL, British Sign Language - BSL, or French Sign Language - LSF) are complete, independent human languages with complex spatial syntax, simultaneous morphological inflection, and grammatical facial expressions.
> 2. **Engineering Scope:** This project focuses on recognizing a defined dictionary of isolated manual hand postures via 21 3D skeletal landmarks. It is designed as an assistive educational and technical aid, NOT a substitute for professional certified human sign language interpreters.
> 3. **Non-Manual Markers (NMMs):** Real-world signed discourse relies heavily on torso movement, mouthing, eyebrow posture, and head positioning which cannot be captured through hand landmarks alone.
> 4. **Regional Differences:** ASL uses a single-handed fingerspelling alphabet, while BSL and Auslan employ two-handed manual alphabets.

---

## Overview

The **AI-Powered Sign Language Recognition System** applies computer vision landmark extraction to classify hand postures into supported sign categories:
- **Supported Vocabulary (8 Signs):** `Hello`, `Thank You`, `Yes`, `No`, `Please`, `I Love You`, `Good`, `Peace`.
- **Landmark Extraction:** 21 anatomical 3D hand keypoints (Wrist, Thumb, Index, Middle, Ring, Pinky).
- **Scale & Translation Invariance:** All landmark coordinates are translated relative to the wrist and scaled by palm size.
- **Classification Engine:** Multi-Layer Perceptron (MLP) trained on 63-dimensional normalized spatial coordinates.
- **Visual Feedback:** 21-node skeletal graph visualization with connecting bones and HUD confidence display.

---

## Architecture

```text
95-sign-language-recognition/
├── app.py                   # Streamlit interactive application
├── classifier.py            # Neural network classifier (MLP), forward pass & SGD training
├── evaluator.py             # Multi-class Accuracy, Precision, Recall, F1, Confusion Matrix
├── hand_detector.py         # 21-point hand landmark extraction & normalization
├── main.py                  # CLI command runner
├── requirements.txt         # Dependencies
├── sign_dictionary.py       # Linguistic metadata, definitions & regional notes
├── test_sign_language.py    # Automated test suite
├── visualizer.py            # Skeletal joint and bone renderer
└── README.md                # Documentation & linguistic specifications
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 95-sign-language-recognition
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. View Supported Sign Dictionary
```bash
python3 main.py --list-signs
```

### 2. Train the Landmark Classifier
```bash
python3 main.py --train --epochs 15 --weights-out sign_model_weights.npz
```

### 3. Evaluate Model Accuracy on Test Data
```bash
python3 main.py --evaluate --weights sign_model_weights.npz
```

### 4. Predict on a Canonical Sign Posture
```bash
python3 main.py --predict-sign "I Love You"
```

### 5. Launch the Streamlit Web Application
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_sign_language.py -v
```
