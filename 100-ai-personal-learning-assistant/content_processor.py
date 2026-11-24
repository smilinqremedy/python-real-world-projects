"""
Content Ingestion, Topic Summarization, and Grounded Quiz Generation.
Extracts factual statements from uploaded PDF and TXT study materials,
synthesizes topic summaries, and builds verifiable MCQs and Short-Answer questions.
"""
import os
import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class GeneratedQuestion:
    question_text: str
    question_type: str  # 'mcq' or 'short_answer'
    options: List[str]  # Empty for short_answer
    correct_answer: str
    explanation: str
    source_excerpt: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContentProcessor:
    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """Extracts plain text from TXT or PDF documents."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")

        _, ext = os.path.splitext(file_path.lower())
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                pages = [p.extract_text() or "" for p in reader.pages]
                return "\n".join(pages).strip()
            except Exception:
                # Native fallback PDF string parser
                with open(file_path, "rb") as f:
                    raw = f.read()
                matches = re.findall(rb"\((.*?)\)\s*Tj", raw)
                clean_strings = [m.decode("latin1", errors="ignore").strip() for m in matches if len(m) > 1]
                return " ".join(clean_strings).strip()
        else:
            raise ValueError(f"Unsupported document format: {ext}")

    @staticmethod
    def generate_topic_summary(content: str, max_sentences: int = 3) -> str:
        """Generates a concise conceptual summary from the most informative sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Heuristic ranking: sentences with definitional markers ('is', 'are', 'enables', 'consists')
        scored = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) < 15:
                continue
            score = 0
            if any(term in s_clean.lower() for term in [" is ", " are ", " enables ", " defined as ", " consists of "]):
                score += 3
            if any(term in s_clean.lower() for term in [" essential ", " key ", " primary ", " fundamental "]):
                score += 2
            scored.append((score, s_clean))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [s for _, s in scored[:max_sentences]]
        return " ".join(top)

    @staticmethod
    def generate_grounded_questions(content: str, num_questions: int = 4) -> List[GeneratedQuestion]:
        """
        Synthesizes factual MCQs and Short-Answer questions strictly grounded in the text.
        Every question is tied directly to a source sentence excerpt to prevent hallucination.
        """
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content.strip()) if len(s.strip()) > 25]
        if not sentences:
            return []

        # Find key candidate terms from the text to form question answers and distractors
        all_words = re.findall(r"\b[A-Z][a-z]{3,}\b", content) + re.findall(r"\b[a-z]{5,}\b", content.lower())
        stopwords = {"which", "their", "there", "about", "these", "those", "after", "before", "because", "between"}
        pool_terms = list(dict.fromkeys([w for w in all_words if w.lower() not in stopwords]))

        questions: List[GeneratedQuestion] = []

        for idx, sent in enumerate(sentences):
            if len(questions) >= num_questions:
                break

            # Check for definitional structure: "X is ..." or "X refers to ..."
            match = re.match(r"^([A-Z][a-zA-Z\s]{2,25})\s+(?:is|are|refers to|consists of|enables)\s+(.*)$", sent)
            if match:
                subject = match.group(1).strip()
                predicate = match.group(2).strip()

                # Generate MCQ
                q_text = f"Which concept or entity {match.group(0).split()[1]} {predicate[:80]}...?"
                correct = subject

                # Pick 3 plausible distractors from pool
                distractors = [t for t in pool_terms if t.lower() != correct.lower()][:3]
                while len(distractors) < 3:
                    distractors.append(f"Alternative Concept {len(distractors) + 1}")

                options = distractors + [correct]
                import random
                random.seed(idx + 42)
                random.shuffle(options)

                questions.append(GeneratedQuestion(
                    question_text=q_text,
                    question_type="mcq",
                    options=options,
                    correct_answer=correct,
                    explanation=f"According to the study material: '{sent}'",
                    source_excerpt=sent
                ))
            else:
                # Generate Short-Answer Question
                words = sent.split()
                if len(words) >= 6:
                    key_term = words[-1].strip(".,!?:")
                    q_text = f"Complete the statement from the study text: '{' '.join(words[:-1])} ______?'"
                    questions.append(GeneratedQuestion(
                        question_text=q_text,
                        question_type="short_answer",
                        options=[],
                        correct_answer=key_term,
                        explanation=f"Source statement: '{sent}'",
                        source_excerpt=sent
                    ))

        return questions
