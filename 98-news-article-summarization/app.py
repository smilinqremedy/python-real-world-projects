"""
Streamlit Web Interface for AI News Article Summarization System.
Supports side-by-side comparison, short vs detailed modes, entity badges, and ROUGE evaluation.
"""
import streamlit as st
import json

from summarizer import ArticleSummarizer
from metrics import compute_rouge

st.set_page_config(
    page_title="News Article Summarization",
    page_icon="📰",
    layout="wide"
)

st.title("📰 AI-Powered News Article Summarization System")
st.markdown("Natural Language Processing pipeline for extractive TextRank, abstractive synthesis, and Named Entity Recognition.")

# Sidebar Settings
st.sidebar.header("Summarization Controls")
summary_mode = st.sidebar.radio("Summary Depth:", ["short", "detailed"], index=0, help="Short (1-2 sentences) or Detailed (multi-sentence executive)")
summary_method = st.sidebar.selectbox("Model Method:", ["extractive", "abstractive"], index=0)

summarizer = ArticleSummarizer()

tabs = st.tabs(["📑 Article Summarizer", "📊 ROUGE Evaluation", "📘 NLP Architecture & Guide"])

with tabs[0]:
    st.subheader("Input News Article")
    source_choice = st.radio("Choose Input Source:", ["Paste Text", "Upload TXT File"], horizontal=True)

    article_text = ""
    if source_choice == "Paste Text":
        article_text = st.text_area(
            "Paste Article Content Here:",
            height=200,
            value=(
                "SAN FRANCISCO — Artificial intelligence research laboratory OpenAI and cloud computing giant "
                "Microsoft announced a major expansion of their collaborative technical partnership on Tuesday. "
                "Under the new framework, the organizations will deploy specialized high-performance computing clusters "
                "in Washington and California to accelerate foundation model training. Dr. Elena Rostova, principal "
                "researcher at the AI Governance Institute in Geneva, commended the initiative for its explicit focus on "
                "computational efficiency and safety verification. The joint deployment is scheduled to commence "
                "operations by October 2026."
            )
        )
    else:
        uploaded_txt = st.file_uploader("Select TXT file:", type=["txt"])
        if uploaded_txt:
            article_text = uploaded_txt.getvalue().decode("utf-8", errors="replace")

    if st.button("✨ Generate AI Summary"):
        if not article_text.strip():
            st.error("Please provide article text.")
        else:
            res = summarizer.summarize_article(article_text, mode=summary_mode, method=summary_method)
            if res["success"]:
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.write("### Original Article")
                    st.caption(f"Word Count: {res['original_word_count']} words")
                    st.info(article_text)

                with col2:
                    st.write(f"### Generated Summary ({res['mode'].capitalize()} - {res['method'].capitalize()})")
                    st.caption(f"Word Count: {res['summary_word_count']} words (Compressed to {res['compression_ratio_pct']}%)")
                    st.success(res["summary"])

                    # Download Buttons
                    st.write("#### Download Summary:")
                    c_d1, c_d2 = st.columns(2)
                    c_d1.download_button("📄 Plain Text (.txt)", data=res["summary"], file_name="article_summary.txt", mime="text/plain")
                    c_d2.download_button("📊 JSON Metadata (.json)", data=json.dumps(res, indent=2), file_name="summary_metadata.json", mime="application/json")

                st.markdown("---")
                st.subheader("Key Entities & Prominent Topics")

                col_k, col_e = st.columns([1, 1])
                with col_k:
                    st.write("#### Prominent Keywords:")
                    for kw in res["keywords"]:
                        st.write(f"- **{kw['keyword']}** (Freq: {kw['frequency']})")

                with col_e:
                    st.write("#### Named Entities Recognized (NER):")
                    entities = res["named_entities"]
                    if entities.get("persons"):
                        st.write(f"👤 **Persons:** {', '.join(entities['persons'])}")
                    if entities.get("organizations"):
                        st.write(f"🏢 **Organizations:** {', '.join(entities['organizations'])}")
                    if entities.get("locations"):
                        st.write(f"📍 **Locations:** {', '.join(entities['locations'])}")
                    if entities.get("dates"):
                        st.write(f"📅 **Dates:** {', '.join(entities['dates'])}")
            else:
                st.error(res["error"])

with tabs[1]:
    st.subheader("Automated Summary Quality Evaluation (ROUGE)")
    st.markdown("Evaluate candidate summaries against a reference ground truth using ROUGE-1, ROUGE-2, and ROUGE-L.")

    ref_input = st.text_area("Reference Gold Summary:", "OpenAI and Microsoft expand partnership for computing clusters in California and Washington.")
    cand_input = st.text_area("Candidate Generated Summary:", "OpenAI and Microsoft announced an expansion of their technical partnership for computing clusters.")

    if st.button("Compute ROUGE Scores"):
        rouge_scores = compute_rouge(ref_input, cand_input)
        c1, c2, c3 = st.columns(3)
        c1.metric("ROUGE-1 F1 (Unigram)", f"{rouge_scores['rouge_1']['f1'] * 100:.1f}%")
        c2.metric("ROUGE-2 F1 (Bigram)", f"{rouge_scores['rouge_2']['f1'] * 100:.1f}%")
        c3.metric("ROUGE-L F1 (LCS)", f"{rouge_scores['rouge_l']['f1'] * 100:.1f}%")

        st.caption(f"ℹ️ **Evaluation Note:** {rouge_scores['metric_limitations_note']}")

with tabs[2]:
    st.subheader("NLP Foundations: Extractive vs. Abstractive Summarization")
    st.markdown("""
    ### Key Concepts
    - **Extractive Summarization:** Selects and extracts the most statistically representative sentences directly from the source text (e.g., using **TextRank** graph centrality). Guarantees that extracted facts belong to the source.
    - **Abstractive Summarization:** Paraphrases and synthesizes new sentences like a human writer using sequence-to-sequence encoder-decoder Transformers (e.g. BART, T5). Requires strict guardrails against hallucinating unstated facts.
    - **TextRank Algorithm:** Formulates sentences as nodes in a fully connected weighted graph where edges represent pairwise lexical and semantic overlap. The PageRank algorithm converges on the most central sentences.
    """)
