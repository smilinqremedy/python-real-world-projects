# Project 98: AI-Powered News Article Summarization System

## Overview

The **AI-Powered News Article Summarization System** condenses lengthy journalistic articles into concise executive summaries while extracting critical semantic metadata, prominent keywords, and recognized named entities.

Key capabilities include:
1. **Article Cleaning & Preprocessing:** Removes advertising boilerplate, HTML markup, and tracking hyperlinks.
2. **Dual Summarization Modes:**
   - **Short Mode:** 1-2 sentence executive snapshot focusing on primary lead propositions.
   - **Detailed Mode:** Comprehensive multi-sentence executive briefing preserving key arguments.
3. **Graph-Based TextRank Engine:** PageRank sentence centrality graph scoring based on pairwise token similarity.
4. **Keyword Extraction (TF-IDF):** Surfaces high-relevance domain topics.
5. **Named Entity Recognition (NER):** Extracts `Persons`, `Organizations`, `Locations`, and `Dates`.
6. **Automated Quality Evaluation (ROUGE):** Calculates ROUGE-1, ROUGE-2, and ROUGE-L metrics against gold standard reference summaries.

---

## Technical Foundations

### Extractive vs. Abstractive Summarization
- **Extractive Summarization:** Identifies and ranks the most representative sentences directly from the source text (e.g., using **TextRank**). Guarantees that extracted facts belong to the source without synthetic confabulation.
- **Abstractive Summarization:** Synthesizes new sentences and paraphrases like a human editor using sequence-to-sequence encoder-decoder Transformers (e.g. BART, T5). Requires strict guardrails against hallucinating unstated facts.

### ROUGE Metrics & Limitations
- **ROUGE-1 / ROUGE-2:** Evaluates unigram and bigram overlap between candidate and reference texts.
- **ROUGE-L:** Computes the Longest Common Subsequence (LCS) to reward sentence-level word-order preservation.
- **Limitation:** ROUGE evaluates statistical lexical overlap rather than factual truth or grammatical elegance. Valid paraphrases using synonymous vocabulary may receive lower ROUGE scores despite being semantically accurate.

---

## Architecture

```text
98-news-article-summarization/
├── app.py                   # Streamlit side-by-side comparison web interface
├── main.py                  # CLI command runner
├── metrics.py               # ROUGE-1, ROUGE-2, and ROUGE-L metric suite
├── nlp_extractor.py         # Keyword extraction & Named Entity Recognition (NER)
├── requirements.txt         # Dependencies
├── summarizer.py            # TextRank graph centrality & abstractive synthesis
├── test_summarization.py    # Automated unit test suite
├── text_preprocessor.py     # HTML removal, sentence splitter, long-text chunking
└── README.md                # Documentation & evaluation notes
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 98-news-article-summarization
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Summarize via CLI
```bash
python3 main.py --text "Paste full article text..." --mode short --format txt --output summary.txt
```

### 2. Detailed Summary with ROUGE Evaluation
```bash
python3 main.py --input article.txt --mode detailed --eval-ref "Reference gold summary text..."
```

### 3. Launch the Streamlit Web UI
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_summarization.py -v
```
