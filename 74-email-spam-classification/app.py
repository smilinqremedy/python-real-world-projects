"""
Streamlit Web Application for Email Spam Classification.
Run with: streamlit run app.py
"""
import streamlit as st
import pandas as pd
from model_trainer import SpamModelTrainer
from classifier import SpamClassifierService
import database


st.set_page_config(page_title="Email Spam Classification Dashboard", layout="wide")


@st.cache_resource
def get_service():
    trainer = SpamModelTrainer()
    results = trainer.train_and_compare()
    service = SpamClassifierService(trainer=trainer)
    return service, results


def main():
    st.title("🛡️ Email Spam Classification System")
    st.markdown("Natural Language Processing & Machine Learning for detecting spam, phishing, and scam messages.")

    service, results = get_service()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Message Scanner")
        subject = st.text_input("Subject Line", value="Urgent: Your account is suspended!")
        body = st.text_area(
            "Email Body",
            value="Dear customer, your bank account access has been suspended due to suspicious activity. Click here to verify credentials and claim your $5,000 cash reward.",
            height=160
        )

        if st.button("Scan Message", type="primary"):
            res = service.classify_email(text=body, subject=subject, persist=True)
            if res["is_spam"]:
                st.error(f"### ⚠️ Classified as SPAM ({res['spam_probability']*100:.1f}%)")
            else:
                st.success(f"### ✅ Classified as HAM / Legitimate (Confidence: {res['confidence_percent']}%)")

            if res["flagged_keywords"]:
                st.warning(f"**Detected Trigger Keywords:** {', '.join(res['flagged_keywords'])}")

    with col_right:
        st.subheader("Model Benchmarks")
        metrics_df = pd.DataFrame(results["model_metrics"]).T[["accuracy", "precision", "recall", "f1_score"]]
        st.dataframe(metrics_df.style.format("{:.4f}"))

        st.subheader("Recent Scans History (SQLite)")
        history = database.get_scan_history(limit=10)
        if history:
            hist_df = pd.DataFrame(history)[["id", "subject", "is_spam", "spam_probability", "flagged_keywords"]]
            st.dataframe(hist_df)


if __name__ == "__main__":
    main()
