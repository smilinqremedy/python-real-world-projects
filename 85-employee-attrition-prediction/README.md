# Project 85: Employee Resignation Prediction System

A People Analytics machine learning application that forecasts employee attrition and voluntary turnover risk using workforce engagement, working hours, compensation, and career mobility data.

## Real-World Problem
Unplanned employee turnover causes immense operational friction, loss of institutional knowledge, and high recruitment costs. Identifying early warning signals of disengagement and burnout empowers HR leadership to enact proactive retention strategies.

## Key Features
- **Comprehensive Workforce Modeling**: Captures job satisfaction surveys, performance evaluation scores, monthly working hours, overtime frequency, tenure, compensation levels, and promotion history.
- **Classification Modeling Pipeline**:
  - Balanced Logistic Regression
  - Random Forest Classifier
  - Gradient Boosting Classifier
- **Model Evaluation**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix.
- **Root-Cause Retention Recommendations**: Automatically detects whether turnover risk stems from burnout, compensation inequity, or stagnation, recommending customized HR interventions.
- **Persistent Audit Logging**: SQLite database records all risk assessments.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `database.py`: SQLite schema and data storage methods.
- `dataset.py`: Synthetic workforce records generator.
- `model_trainer.py`: Classification pipeline with ColumnTransformer and model selection.
- `predictor.py`: Attrition risk classification and HR recommendation engine.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_attrition.py`: Automated unit tests.

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
python3 -m unittest test_attrition.py -v
```
