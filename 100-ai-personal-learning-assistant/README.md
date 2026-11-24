# Project 100: AI-Powered Personal Learning Assistant

## Overview

The **AI-Powered Personal Learning Assistant** provides an adaptive learning management and spaced-repetition platform designed to ingest educational study materials, extract core concepts, synthesize grounded quiz questions, and diagnose knowledge gaps.

Key capabilities include:
1. **Curriculum Hierarchy:** Organizes study materials by Subjects and Topics.
2. **Multi-Format Content Ingestion:** Ingests TXT and PDF lecture notes and study guides.
3. **Conceptual Summarization:** Generates concise topic summaries highlighting core assertions.
4. **Grounded Question Generation:** Synthesizes Multiple Choice Questions (MCQs) and Short-Answer questions directly anchored to source statements (strictly preventing fabricated information).
5. **Automated Quiz Arena:** Real-time grading with question-level feedback, explanations, and score tracking.
6. **Weak Topic Diagnosis:** Flags topics with average scores below the 70% threshold.
7. **Personalized Revision Recommendations:** Prioritizes targeted review schedules for underperforming areas.
8. **Progress Reporting:** One-click downloadable CSV performance logs.

---

## Technical Foundations

### Grounded Question Generation
To avoid hallucinating inaccurate educational content:
- The question generation engine parses definitional and relational clauses from the uploaded text.
- For MCQs, the focal concept serves as the correct key, while plausible distractors are extracted exclusively from other terms appearing within the same study material.
- Every question stores an immutable `source_excerpt` snippet enabling students to verify the answer directly against the source text.

### Performance Analytics & Weak Topic Threshold
- Student quiz submissions record percentage score, total questions, and completion timestamps in SQLite.
- A rolling average score is computed per topic. Topics with an average score $< 70.0\%$ are automatically categorized as **Needs Revision** and scheduled for spaced repetition.

---

## Architecture

```text
100-ai-personal-learning-assistant/
├── app.py                      # Streamlit interactive learning portal
├── auth.py                     # PBKDF2-HMAC-SHA256 password hashing & auth
├── content_processor.py        # PDF/TXT extraction, summarization & question synthesis
├── database.py                 # SQLite schema (users, subjects, topics, questions, attempts)
├── learning_engine.py          # Core business logic, quiz grading & weak topic tracking
├── main.py                     # CLI command runner
├── requirements.txt            # Dependencies
├── test_learning_assistant.py  # Automated unit test suite
└── README.md                   # Documentation & educational framework
```

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd 100-ai-personal-learning-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Register a Learner Account
```bash
python3 main.py --register-user alex SecurePass@2026
```

### 2. Create a Learning Subject
```bash
python3 main.py --add-subject alex "Computer Science" "Algorithms and Data Structures"
```

### 3. Upload Study Material & Generate Quiz
```bash
python3 main.py --upload-material alex "Computer Science" "Binary Trees" study_notes.txt
```

### 4. Review Weak Topics
```bash
python3 main.py --weak-topics alex
```

### 5. Export Progress Report to CSV
```bash
python3 main.py --export-report alex learning_report.csv
```

### 6. Launch the Streamlit Portal
```bash
streamlit run app.py
```

---

## Running Automated Tests

Run the test suite with `unittest`:
```bash
python3 -m unittest test_learning_assistant.py -v
```
