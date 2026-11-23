"""
Streamlit Web Application for Employee Resignation Prediction.
Run with: streamlit run app.py
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import streamlit as st
import pandas as pd
from model_trainer import EmployeeAttritionTrainer
from predictor import AttritionPredictorService
import database


st.set_page_config(page_title="Employee Attrition Prediction Dashboard", layout="wide")


@st.cache_resource
def get_service():
    trainer = EmployeeAttritionTrainer()
    results = trainer.train_and_compare()
    service = AttritionPredictorService(trainer=trainer)
    return service, results


def main():
    st.title("👥 Employee Resignation & Attrition Prediction System")
    st.markdown("People analytics dashboard for forecasting turnover risk, identifying critical burnout indicators, and formulating retention interventions.")

    service, results = get_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Employee Workforce Profile")
        emp_id = st.text_input("Employee ID", value="EMP-1093")
        dept = st.selectbox("Department", ["Engineering", "Sales", "Support", "Marketing", "R&D", "Finance", "HR"], index=0)
        sat = st.slider("Job Satisfaction Survey Score (0.0 to 1.0)", min_value=0.1, max_value=1.0, value=0.38, step=0.01)
        evaluation = st.slider("Last Performance Evaluation Score (0.0 to 1.0)", min_value=0.3, max_value=1.0, value=0.85, step=0.01)
        monthly_hours = st.slider("Average Monthly Hours", min_value=120, max_value=320, value=255, step=5)
        tenure = st.slider("Tenure at Company (Years)", min_value=1, max_value=10, value=4)
        projects = st.slider("Number of Assigned Projects", min_value=2, max_value=7, value=5)
        salary = st.selectbox("Salary Level", ["Low", "Medium", "High"], index=0)
        overtime = st.selectbox("Frequent Overtime", ["Yes", "No"], index=0)
        promotion = st.checkbox("Promoted in the Last 5 Years", value=False)

        if st.button("Evaluate Resignation Risk", type="primary"):
            emp_data = {
                "employee_id": emp_id,
                "department": dept,
                "salary_level": salary,
                "overtime": overtime,
                "satisfaction_score": sat,
                "last_evaluation": evaluation,
                "number_of_projects": projects,
                "monthly_hours": monthly_hours,
                "tenure_years": tenure,
                "promotion_last_5years": 1 if promotion else 0
            }

            res = service.evaluate_employee(emp_data, persist=True)
            risk_badge = {"High Risk": "🔴", "Medium Risk": "🟡", "Low Risk": "🟢"}
            st.markdown(f"### Attrition Risk: {risk_badge.get(res['risk_level'], '')} **{res['risk_level']}** ({res['attrition_percentage']})")
            st.info(f"**Actionable Retention Recommendation:**\n\n{res['hr_recommendations']}")

    with col_right:
        st.subheader("Workforce Classifier Benchmarks")
        metrics_df = pd.DataFrame(results["model_metrics"]).T[["accuracy", "precision", "recall", "f1_score", "roc_auc"]]
        st.dataframe(metrics_df.style.format("{:.4f}"))

        st.subheader("Key Attrition Drivers (Random Forest)")
        feat_df = pd.DataFrame(
            list(results["feature_importances"].items()),
            columns=["Feature", "Importance"]
        ).sort_values("Importance", ascending=True).tail(8)
        st.bar_chart(feat_df.set_index("Feature"))

        st.subheader("Recent Assessments in SQLite")
        recent = database.get_all_assessments(limit=10)
        if recent:
            st.dataframe(pd.DataFrame(recent)[["employee_id", "department", "monthly_hours", "risk_level", "attrition_probability"]])


if __name__ == "__main__":
    main()
