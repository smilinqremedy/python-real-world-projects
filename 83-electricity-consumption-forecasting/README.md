# Project 83: Electricity Consumption Forecasting System

A Time-Series Predictive Analytics and Machine Learning application that forecasts grid electricity demand using historical consumption patterns, seasonal trends, and meteorological factors.

## Real-World Problem
Electric utilities, grid operators, and facilities managers must accurately forecast power consumption to balance supply, prevent grid outages, schedule maintenance windows, and optimize energy procurement contracts.

## Key Features
- **Time-Series Decomposition**: Identifies weekly seasonality (weekday vs. weekend), annual temperature cooling/heating cycles, and underlying load growth trends.
- **Chronological Data Integrity**: Enforces strict chronological train-test splitting to eliminate future data leakage.
- **Autoregressive Feature Engineering**: Generates lag features ($t-1, t-2, t-7, t-14, t-30$) and rolling window statistics ($7$-day rolling mean and standard deviation).
- **Multi-Model Benchmark**:
  - Baseline Persistence model
  - Classical ARIMA $(2, 1, 1)$
  - Random Forest Time-Series Regressor
- **Comprehensive Error Metrics**: Evaluates Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE), and $R^2$.
- **Forward Horizon Projections**: Projects multi-day out-of-sample demand and flags peak grid strain alerts.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `dataset.py`: Multi-year synthetic electricity consumption dataset generator.
- `model_trainer.py`: Time-series feature engineering, chronological splits, and model benchmarking.
- `forecaster.py`: Autoregressive multi-step projection service and grid advisories.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_forecasting.py`: Automated unit tests.

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
python3 -m unittest test_forecasting.py -v
```
