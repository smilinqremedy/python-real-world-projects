# Project 72: House Price Prediction System

A predictive analytics machine learning application that forecasts property valuation using physical features, location quality, and property condition.

## Real-World Problem
Real estate buyers, sellers, and appraisers need reliable estimates of property values based on historical comparable sales. Accurate regression models help reduce subjective pricing bias and assess fair market values.

## Key Features
- **Data Generation & Ingestion**: Generates and parses real estate datasets with features including square footage, bedrooms, bathrooms, location scores, year built, condition rating, and garage capacity.
- **Multiple Regression Models**: Trains and compares:
  - Linear Regression (Baseline)
  - Decision Tree Regressor
  - Random Forest Regressor
- **Comprehensive Evaluation**: Measures Mean Absolute Error (MAE), Mean Squared Error (MSE), Root Mean Squared Error (RMSE), and Coefficient of Determination ($R^2$).
- **Feature Importance Analysis**: Identifies dominant drivers of valuation.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `dataset.py`: Synthetic real estate dataset generator and schema definitions.
- `model_trainer.py`: Regression training pipeline, model selection, and metric calculations.
- `main.py`: Interactive command-line interface.
- `app.py`: Streamlit web application.
- `test_house_price.py`: Automated unit tests.

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
python3 -m unittest test_house_price.py -v
```
