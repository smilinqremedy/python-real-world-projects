# Project 74: Email Spam Classification System

A Machine Learning and Natural Language Processing (NLP) application that identifies unsolicited spam, phishing scams, and fraudulent emails using TF-IDF feature extraction and probabilistic classification.

## Real-World Problem
Email boxes receive thousands of messages daily, many of which contain malware links, financial fraud schemes, or time-wasting advertisements. Automated spam classifiers protect user privacy, increase productivity, and prevent cyber attacks.

## Key Features
- **Text Preprocessing & Normalization**: Cleans punctuation, strips numerals, replaces URLs and currency values with semantic tokens (`urltoken`, `moneytoken`).
- **TF-IDF Vectorization**: Extracts unigrams and bigrams (`max_features=3000`).
- **Classifier Benchmark**:
  - Multinomial Naive Bayes
  - Logistic Regression
  - Random Forest Classifier
- **Metrics Evaluated**: Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
- **Trigger Word Highlighting**: Scans and flags high-risk phishing/spam keywords.
- **Persistent Scan History**: SQLite database stores all scanned emails and classification scores.
- **Dual Interfaces**: Interactive CLI (`main.py`) and Streamlit web dashboard (`app.py`).

## File Structure
- `database.py`: SQLite persistence and statistics.
- `dataset.py`: Synthetic email corpus generator with labeled spam and ham messages.
- `preprocessor.py`: Text cleaning, normalization, and spam trigger word extraction.
- `model_trainer.py`: Scikit-learn TF-IDF pipeline and model evaluation.
- `classifier.py`: Classification service, keyword aggregation, and database integration.
- `main.py`: Interactive CLI interface.
- `app.py`: Streamlit web dashboard.
- `test_spam_classifier.py`: Automated unit tests.

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
python3 -m unittest test_spam_classifier.py -v
```
