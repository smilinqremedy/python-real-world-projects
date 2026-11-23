"""
Streamlit Web Dashboard for Customer Churn Prediction & Retention Analytics.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from dataset import generate_churn_dataset, CONTRACT_MAPPING
from model_trainer import ChurnModelTrainer
from predictor import ChurnPredictorService
import database


st.set_page_config(page_title="Customer Churn Prediction & Retention", layout="wide")


@st.cache_resource
def get_service():
    trainer = ChurnModelTrainer()
    results = trainer.train_and_compare()
    service = ChurnPredictorService(trainer=trainer)
    return service, results


def main():
    st.title("📊 Customer Churn Prediction & Retention System")
    st.markdown("Identify high-risk churn customers and formulate targeted retention incentives before subscription lapse.")

    service, results = get_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Customer Profile & Subscription Details")
        cust_id = st.text_input("Customer ID", value="CUST-1042")
        tenure = st.slider("Tenure (Months)", min_value=1, max_value=72, value=8)
        contract = st.selectbox("Contract Type", options=["Month-to-month", "One year", "Two year"], index=0)
        monthly_charges = st.slider("Monthly Charges ($)", min_value=20.0, max_value=120.0, value=85.0, step=1.0)
        support_tickets = st.slider("Customer Support Inquiries", min_value=0, max_value=10, value=3)
        online_security = st.checkbox("Subscribed to Online Security", value=False)
        tech_support = st.checkbox("Subscribed to Tech Support", value=False)
        delay_days = st.slider("Average Payment Delay (Days)", min_value=0, max_value=30, value=7)

        if st.button("Evaluate Churn Risk", type="primary"):
            customer_data = {
                "customer_id": cust_id,
                "tenure_months": tenure,
                "contract_type": contract,
                "contract_type_code": CONTRACT_MAPPING[contract],
                "monthly_charges": monthly_charges,
                "total_charges": tenure * monthly_charges,
                "support_tickets": support_tickets,
                "online_security": 1 if online_security else 0,
                "tech_support": 1 if tech_support else 0,
                "payment_delay_days": delay_days
            }

            res = service.evaluate_customer(customer_data, persist=True)

            tier_colors = {"High": "🔴", "Moderate": "🟡", "Low": "🟢"}
            st.markdown(f"### Churn Probability: **{res['churn_percentage']}** {tier_colors[res['risk_tier']]} ({res['risk_tier']} Risk)")
            st.info(f"**Recommended Retention Action:**\n\n{res['retention_strategy']}")

    with col_right:
        st.subheader("Classification Models Performance")
        metrics_df = pd.DataFrame(results["model_metrics"]).T[["accuracy", "precision", "recall", "f1_score", "roc_auc"]]
        st.dataframe(metrics_df.style.format("{:.4f}"))

        st.subheader("Key Drivers of Customer Churn")
        feat_df = pd.DataFrame(
            list(results["feature_importances"].items()),
            columns=["Feature", "Importance"]
        ).sort_values("Importance", ascending=True)
        st.bar_chart(feat_df.set_index("Feature"))

        st.subheader("Recent Predictions in SQLite")
        recent = database.get_all_predictions()
        if recent:
            st.dataframe(pd.DataFrame(recent)[["customer_id", "tenure_months", "monthly_charges", "churn_probability", "risk_tier"]].head(10))


if __name__ == "__main__":
    main()
