# Project 81: Road Accident Severity Prediction System

A transportation analytics and machine learning application that predicts traffic crash severity levels (Slight, Serious, Fatal) to support road safety policy, traffic management, and infrastructure engineering.

## Real-World Problem
Road transport agencies and emergency services must understand the causal factors influencing crash severity to prioritize infrastructure interventions, adjust speed limits, and deploy preventative enforcement.

## Key Features
- **Exploratory Traffic Feature Engineering**: Considers weather conditions, road surface quality, street lighting, posted speed limits, vehicle types, time of day, driver age demographics, and vehicle collision counts.
- **Multi-Class Classification Benchmark**:
  - Multinomial Logistic Regression
  - Random Forest Classifier (balanced class weights)
  - Gradient Boosting Classifier
- **Comprehensive Evaluation**: Precision, Recall, Weighted F1-Score, One-vs-Rest ROC-AUC, and 3x3 Confusion Matrix.
- **Safety Engineering Countermeasures**: Automatically recommends traffic safety interventions (speed radars, surface anti-skid resurfacing, lighting upgrades, segregation lanes).
- **Persistent Audit Logging**: SQLite database maintains all historical scenario evaluations.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `database.py`: SQLite schema and data persistence.
- `dataset.py`: Multi-class synthetic accident dataset generator.
- `model_trainer.py`: Multi-class training pipeline, column transformer, and benchmarking.
- `predictor.py`: Accident severity evaluation and safety intervention engine.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_accident_severity.py`: Automated unit tests.

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
python3 -m unittest test_accident_severity.py -v
```
