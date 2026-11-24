"""
Streamlit Web Interface for AI Financial Fraud Detection System.
Transaction risk scoring dashboard, human analyst review queue, and PR-AUC metrics.
"""
import streamlit as st
import pandas as pd
import numpy as np

from dataset import generate_synthetic_transactions, robust_scale, FEATURE_NAMES
from models import SupervisedFraudClassifier, IsolationForestAnomalyDetector, calculate_risk_score
from evaluator import evaluate_fraud_model
import database

st.set_page_config(
    page_title="Financial Fraud Detection",
    page_icon="💳",
    layout="wide"
)

st.title("💳 AI-Based Financial Fraud Detection System")
st.markdown("Multi-tiered risk scoring combining weighted supervised classifiers and unsupervised anomaly trees.")

# Ethical Policy Banner
st.warning(
    "⚠️ **OPERATIONAL FRAUD POLICY:** In compliance with consumer protection standards, "
    "transactions flagged as HIGH RISK must be reviewed by a human fraud analyst or challenged via step-up "
    "MFA verification. High risk transactions are NEVER automatically declined without recourse."
)

# Train cached model on startup
@st.cache_resource
def load_trained_models():
    X, y, _ = generate_synthetic_transactions(n_samples=1000, fraud_ratio=0.03, seed=42)
    X_scaled, medians, iqrs = robust_scale(X)
    clf = SupervisedFraudClassifier(fraud_weight=20.0)
    clf.train(X_scaled, y, epochs=15)
    iso = IsolationForestAnomalyDetector(n_trees=15)
    iso.fit(X_scaled)
    return clf, iso, medians, iqrs

classifier, anomaly_model, medians, iqrs = load_trained_models()

tabs = st.tabs([
    "🔍 Real-Time Risk Scorer",
    "🛡️ Fraud Analyst Review Queue",
    "📊 PR-AUC & Imbalance Evaluation",
    "🏛️ Financial Policy & Ethics"
])

with tabs[0]:
    st.subheader("Live Transaction Risk Evaluation")
    col1, col2 = st.columns([1, 1])

    with col1:
        txn_id = st.text_input("Transaction Reference ID:", value="TXN-90214")
        txn_amt = st.number_input("Transaction Amount ($):", min_value=0.50, max_value=50000.0, value=35.0, step=5.0)
        txn_time = st.slider("Time of Day (Hour: 0 to 24):", min_value=0, max_value=24, value=14)

        # Custom latent PCA sliders
        v1 = st.slider("PCA Vector V1 (Spending Deviation):", -5.0, 5.0, 0.2, 0.1)
        v2 = st.slider("PCA Vector V2 (Location Anomaly):", -5.0, 5.0, -0.1, 0.1)
        v3 = st.slider("PCA Vector V3 (Device Velocity):", -5.0, 5.0, 0.0, 0.1)

        raw_vec = np.array([txn_amt, txn_time * 3600, v1, v2, v3, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        scaled_vec = (raw_vec - medians) / iqrs

        if st.button("⚡ Score Transaction Risk"):
            prob = float(classifier.forward(np.expand_dims(scaled_vec, axis=0))[0])
            anom = float(anomaly_model.score_anomalies(np.expand_dims(scaled_vec, axis=0))[0])
            score, tier, action = calculate_risk_score(prob, anom)

            database.log_transaction_risk(txn_id, txn_amt, prob, anom, score, tier)

            with col2:
                st.subheader("Risk Assessment Outcome")
                if tier == "LOW":
                    st.success(f"### Tier: **{tier} RISK** (Score: {score}/100)")
                elif tier == "MODERATE":
                    st.warning(f"### Tier: **{tier} RISK** (Score: {score}/100)")
                else:
                    st.error(f"### Tier: **{tier} RISK** (Score: {score}/100)")

                st.write(f"**Recommended Action:** `{action}`")
                st.write(f"- Supervised Fraud Posterior: `{prob * 100:.1f}%`")
                st.write(f"- Unsupervised Anomaly Metric: `{anom * 100:.1f}%`")
                st.progress(score / 100.0)

with tabs[1]:
    st.subheader("Human-in-the-Loop Analyst Queue")
    flagged = database.get_transactions_by_status("flagged", limit=20)
    if flagged:
        st.dataframe(flagged)
        st.write("#### Action Disposition on Flagged Transaction:")
        with st.form("disposition_form"):
            target_tx = st.selectbox("Select Transaction ID:", [r["transaction_id"] for r in flagged])
            decision = st.selectbox("Analyst Decision:", ["cleared", "confirmed_fraud"])
            notes = st.text_input("Investigation Notes & Verification Details:")
            submitted = st.form_submit_button("Record Final Disposition")

            if submitted:
                database.update_analyst_disposition(target_tx, decision, notes)
                st.success(f"Transaction {target_tx} updated to: {decision.upper()}")
                st.experimental_rerun()
    else:
        st.info("No pending high-risk transactions requiring analyst review.")

with tabs[2]:
    st.subheader("Class Imbalance Evaluation: Why Accuracy Is Misleading")
    st.markdown("""
    When only 1-3% of transactions are fraudulent, a naive baseline that predicts **all transactions are legitimate**
    achieves **97-99% accuracy**, while catching **0% of fraudulent theft**.
    Therefore, fraud teams optimize for **PR-AUC (Precision-Recall AUC)** and **Recall**.
    """)

    if st.button("Compute Benchmark PR-AUC vs ROC-AUC"):
        X_test, y_test, _ = generate_synthetic_transactions(n_samples=500, fraud_ratio=0.03, seed=999)
        X_t_scaled, _, _ = robust_scale(X_test, medians, iqrs)
        probs = classifier.forward(X_t_scaled)
        metrics = evaluate_fraud_model(y_test, probs)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PR-AUC (Primary Metric)", f"{metrics['pr_auc'] * 100:.1f}%")
        c2.metric("ROC-AUC", f"{metrics['roc_auc'] * 100:.1f}%")
        c3.metric("Fraud Recall", f"{metrics['recall'] * 100:.1f}%")
        c4.metric("Precision", f"{metrics['precision'] * 100:.1f}%")

        st.write("#### Tradeoff Confusion Matrix:")
        cm = metrics["confusion_matrix"]
        st.write(f"- **True Positives (Caught Fraud):** {cm[1][1]}")
        st.write(f"- **False Positives (Customer Friction):** {cm[0][1]}")
        st.write(f"- **False Negatives (Missed Fraud):** {cm[1][0]}")
        st.write(f"- **True Negatives (Legitimate Cleared):** {cm[0][0]}")

with tabs[3]:
    st.subheader("Financial Consumer Protection Standards")
    st.markdown("""
    - **False Positive Friction:** Erroneously declining a genuine customer's card damages brand loyalty and causes lost revenue. The system implements a three-tier posture (Approve, Step-Up MFA, Analyst Review).
    - **False Negative Risk:** Failing to flag fraudulent transactions causes chargeback penalties and financial losses.
    """)
