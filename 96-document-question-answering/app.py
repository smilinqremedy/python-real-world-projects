"""
Streamlit Web Interface for Intelligent Document Question-Answering System (RAG).
Supports multi-document uploads (PDF & TXT), semantic vector search,
grounded citations, and anti-hallucination guardrails.
"""
import os
import tempfile
import streamlit as st

from rag_engine import RAGEngine, ANTI_HALLUCINATION_FALLBACK
from document_loader import DocumentExtractionError

st.set_page_config(
    page_title="Document Question-Answering",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Intelligent Document Question-Answering System")
st.markdown("Retrieval-Augmented Generation (RAG) with semantic embeddings, vector search, and anti-hallucination guardrails.")

# Initialize RAGEngine in session state
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine()

engine = st.session_state.rag_engine

# Sidebar Configuration
st.sidebar.header("RAG Retrieval Settings")
top_k = st.sidebar.slider("Top-K Retrieved Chunks", min_value=1, max_value=6, value=3)
min_sim = st.sidebar.slider("Min Relevance Threshold (Anti-Hallucination)", min_value=0.05, max_value=0.50, value=0.15, step=0.05)

st.sidebar.markdown("---")
st.sidebar.write("### Ingested Documents:")
if engine.ingested_documents:
    for doc in engine.ingested_documents:
        st.sidebar.write(f"- 📄 `{doc}`")
    st.sidebar.caption(f"Total Chunks in Vector Store: **{len(engine.vector_store.chunks)}**")
else:
    st.sidebar.info("No documents uploaded yet.")

tabs = st.tabs(["💬 Ask Questions", "📂 Document Ingestion", "🧠 RAG Architecture & Ethics"])

with tabs[0]:
    st.subheader("Query Ingested Knowledge Base")
    if not engine.ingested_documents:
        st.info("Please upload one or more documents in the 'Document Ingestion' tab first.")
    else:
        question = st.text_input("Enter your question regarding the uploaded documents:", placeholder="e.g. What are the key findings or requirements?")

        if st.button("🔍 Get Grounded Answer"):
            if not question:
                st.error("Please enter a question.")
            else:
                res = engine.answer_question(question, top_k=top_k, min_similarity=min_sim)

                if res["is_grounded"]:
                    st.success(f"### Answer (Relevance Confidence: {res['relevance_score'] * 100:.1f}%)")
                    st.write(res["answer"])

                    st.write("#### 📑 Verified Source References:")
                    for idx, src in enumerate(res["sources"], start=1):
                        with st.expander(f"Reference #{idx}: {src['document']} (Page {src['page']}) — Match Score: {src['similarity']:.2f}"):
                            st.write(f"**Chunk ID:** `{src['chunk_id']}`")
                            st.write(f"**Source Excerpt:** *\"{src['excerpt']}\"*")
                else:
                    st.warning("⚠️ **Anti-Hallucination Warning:**")
                    st.write(res["answer"])

with tabs[1]:
    st.subheader("Upload PDF or TXT Documents")
    uploaded_files = st.file_uploader(
        "Upload one or more reference files:",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

    if st.button("📥 Process & Index Documents"):
        if not uploaded_files:
            st.error("Please select at least one PDF or TXT file.")
        else:
            for up_file in uploaded_files:
                ext = os.path.splitext(up_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(up_file.getvalue())
                    tmp_path = tmp.name

                try:
                    stats = engine.ingest_document(tmp_path)
                    st.success(f"Indexed **{up_file.name}**: {stats['pages_count']} pages, {stats['chunks_count']} chunks.")
                except DocumentExtractionError as dee:
                    st.error(f"Extraction error for {up_file.name}: {dee}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

with tabs[2]:
    st.subheader("Retrieval-Augmented Generation (RAG) Architecture")
    st.markdown("""
    ### How RAG Works
    1. **Document Ingestion:** Raw PDFs and text documents are parsed into individual pages and paragraphs.
    2. **Chunking Strategy:** Sliding window chunker segments text into 400-character segments with 80-character overlap to preserve semantic continuity across boundaries.
    3. **Vector Embeddings:** Each chunk is converted into a 128-dimensional mathematical vector representing its semantic meaning.
    4. **Vector Database & Similarity Search:** Chunks are stored with their embeddings. Queries are embedded and compared using **Cosine Similarity**.
    5. **Anti-Hallucination Guardrails:** If the highest chunk similarity is below the relevance threshold, the system explicitly refuses to answer rather than fabricating false information.
    """)
