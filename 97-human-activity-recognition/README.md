# Project 97: AI-Powered Human Activity Recognition System

## Overview

The **AI-Powered Human Activity Recognition System** classifies physical human movements and postures using tri-axial accelerometer and gyroscope measurements from wearable devices.

Key capabilities include:
1. **6-Axis Sensor Ingestion:** Accelerometer `(acc_x, acc_y, acc_z)` and Gyroscope `(gyro_x, gyro_y, gyro_z)`.
2. **Time-Window Segmentation:** Converts continuous high-frequency time series into overlapping 64-timestep windows.
3. **Subject-Based Partitioning (Zero Data Leakage):** Enforces subject-wise cross-validation to guarantee that adjacent overlapping windows from the same individual do not contaminate test evaluations.
4. **Deep Learning Architecture:** 1D Convolutional Neural Network (1D-CNN) extracting multi-scale temporal motion signatures.
5. **6 Activity Categories:** `Walking`, `Walking Upstairs`, `Walking Downstairs`, `Sitting`, `Standing`, `Laying`.
6. **Visualization & Diagnostic HUD:** Waveform plotting and confusion matrix performance breakdowns.

---

## Technical Foundations

### Sequential Time-Series Windowing
Wearable sensors produce continuous high-frequency streams (e.g. 50 Hz). A fixed sliding window (e.g. 64 timesteps with 50% overlap) captures complete periodic gait cycles:
- **Stationary Postures:** Static gravitational acceleration aligned with vertical axes (Y-axis for standing/sitting, Z-axis for laying).
- **Dynamic Postures:** Periodic sinusoidal harmonic peaks and higher angular velocities around rotational axes.

### Data Leakage Mitigation
Randomly shuffling windows creates massive artificial test score inflation because adjacent overlapping windows from the same recording session share identical sensor artifacts. In this implementation:
- Subject IDs 1-4 are assigned to training.
- Subject ID 5 is assigned to validation.
- Subject ID 6 is reserved exclusively for uncorrupted testing.

---

## Architecture

```text
97-human-activity-recognition/
├── app.py              # Streamlit dashboard & sensor waveform visualizer
├── dataset.py          # Windowing, subject splitting & benchmark data generator
├── evaluator.py        # Multi-class Accuracy, Precision, Recall, F1, Confusion Matrix
├── main.py             # CLI command runner
├── model.py            # 1D Convolutional Neural Network (1D-CNN) architecture
├── requirements.txt    # Dependencies
├── test_har.py         # Automated unit test suite
├── trainer.py          # Training loop with validation tracking and checkpoints
├── visualizer.py       # Multi-channel sensor waveform renderer
└── README.md           # Documentation
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 97-human-activity-recognition
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Generate Synthetic Sensor Benchmark Data
```bash
python3 main.py --generate-data ./har_dataset
```

### 2. Train the 1D-CNN Model
```bash
python3 main.py --train ./har_dataset --epochs 8 --weights-out har_model_weights.npz
```

### 3. Evaluate on an Unseen Subject
```bash
python3 main.py --evaluate ./har_dataset/subject_06 --weights har_model_weights.npz
```

### 4. Predict Activity from a Sensor CSV
```bash
python3 main.py --predict ./har_dataset/subject_06/walking.csv --weights har_model_weights.npz
```

### 5. Launch the Streamlit Interface
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_har.py -v
```
