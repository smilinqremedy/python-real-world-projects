# Project 96: Intelligent Document Question-Answering System (RAG)

## Overview & Technical Foundations

### Retrieval-Augmented Generation (RAG)
**Retrieval-Augmented Generation (RAG)** is an AI architectural pattern that grounds query responses in external, verified document collections rather than relying on parametric language model memory alone:
1. **Document Ingestion:** Ingests PDF and TXT documents, extracting text page-by-page.
2. **Text Chunking:** Chunks text with sliding window overlap (e.g. 400 chars with 80-char overlap) to retain contextual continuity across sentence boundaries.
3. **Vector Embeddings:** Transforms text chunks into 128-dimensional dense mathematical vector embeddings capturing semantic relationships.
4. **Vector Store & Semantic Search:** Embeddings are indexed using **Cosine Similarity**, enabling sub-millisecond retrieval of the most relevant source passages.
5. **Anti-Hallucination Guardrails:** If the retrieved similarity score falls below the confidence threshold, the system explicitly acknowledges that the document does not contain the answer, strictly preventing fabricated facts.
6. **Source Citations:** Every generated response is accompanied by exact document names, page numbers, and chunk references.

---

## Architecture

```text
96-document-question-answering/
├── app.py                 # Streamlit web interface with multi-document upload
├── chunker.py             # Sliding-window document chunking module
├── document_loader.py     # PDF & TXT text extraction and validation
├── embeddings.py          # Semantic embedding generation engine
├── main.py                # Command-line interface
├── rag_engine.py          # RAG pipeline & anti-hallucination guardrails
├── requirements.txt       # Dependencies
├── test_document_qa.py    # Automated test suite
├── vector_store.py        # Vector similarity indexing and persistence
└── README.md              # Documentation
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 96-document-question-answering
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Ingest Documents via CLI
```bash
python3 main.py --ingest sample.txt policy.pdf --index-path rag_index.npz
```

### 2. Query Ingested Documents
```bash
python3 main.py --ask "What are the data privacy standards?" --index-path rag_index.npz
```

### 3. Launch Streamlit Web UI
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_document_qa.py -v
```
