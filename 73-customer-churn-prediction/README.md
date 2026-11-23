# Project 73: Customer Churn Prediction System

An end-to-end customer retention and churn intelligence system that predicts subscription cancellation risks and suggests targeted retention incentives.

## Real-World Problem
Subscription, SaaS, and telecom companies lose significant recurring revenue when customers cancel their subscriptions. Detecting churn early allows customer success and marketing teams to intervene with discounts, onboarding support, or contract upgrades.

## Key Features
- **Behavioral Feature Engineering**: Analyzes tenure, contract type, monthly charges, customer support tickets, online security adoption, tech support, and billing payment delays.
- **Classification Modeling**:
  - Logistic Regression (with balanced class weights)
  - Decision Tree Classifier
  - Random Forest Classifier
- **Model Evaluation**: Computes Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.
- **Risk Tiering & Retention Rules**: Categorizes customers into Low, Moderate, or High Risk, providing automated actionable retention strategies.
- **Persistent Audit Logging**: SQLite database records all churn assessments.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `database.py`: SQLite schema and data access methods.
- `dataset.py`: Synthetic customer dataset generator and contract mappings.
- `model_trainer.py`: Classification model pipeline, metric calculations, and feature importance extraction.
- `predictor.py`: Risk classification and retention strategy engine.
- `main.py`: Interactive command-line interface.
- `app.py`: Streamlit web application.
- `test_churn.py`: Automated unit tests.

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
python3 -m unittest test_churn.py -v
```
