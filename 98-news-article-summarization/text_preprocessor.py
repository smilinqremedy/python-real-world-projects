"""
Text Preprocessing, Boilerplate Cleaning, Sentence Segmentation, and Chunking Module.
"""
import re
from typing import List

# Common abbreviations to prevent false sentence breaks
ABBREVIATIONS = {
    "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.", "inc.", "corp.", "co.", "ltd.", "u.s.", "u.k."
}


def clean_article_text(raw_text: str) -> str:
    """
    Cleans raw news text:
    - Removes HTML tags and scripts
    - Removes URLs and hyperlinks
    - Strips social sharing artifacts and advertisement headers
    - Normalizes excessive whitespace and line breaks
    """
    if not raw_text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", raw_text)

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", text)

    # Remove typical advertisement and clickbait boilerplate
    boilerplate_patterns = [
        r"(?i)advertisement\b",
        r"(?i)sponsored\s+content\b",
        r"(?i)sign\s+up\s+for\s+our\s+newsletter\b",
        r"(?i)all\s+rights\s+reserved\b",
        r"(?i)follow\s+us\s+on\s+twitter\b",
        r"(?i)read\s+more:.*"
    ]
    for pattern in boilerplate_patterns:
        text = re.sub(pattern, " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into coherent sentences while preserving abbreviations and quotes.
    """
    if not text:
        return []

    # Tokenize potential sentences
    raw_splits = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    buffer = ""

    for s in raw_splits:
        candidate = (buffer + " " + s).strip() if buffer else s.strip()
        last_word = candidate.split()[-1].lower() if candidate.split() else ""

        if last_word in ABBREVIATIONS and not candidate.endswith(("!", "?")):
            buffer = candidate
        else:
            if candidate and len(candidate) > 5:
                sentences.append(candidate)
            buffer = ""

    if buffer and len(buffer) > 5:
        sentences.append(buffer)

    return sentences


def chunk_long_article(sentences: List[str], max_words: int = 250, overlap_words: int = 40) -> List[List[str]]:
    """
    Splits a long sequence of sentences into overlapping chunks to respect context token limits.
    """
    if not sentences:
        return []

    chunks = []
    current_chunk = []
    current_word_count = 0

    for sent in sentences:
        words = sent.split()
        if current_word_count + len(words) > max_words and current_chunk:
            chunks.append(current_chunk)
            # Maintain overlap
            overlap_chunk = []
            overlap_count = 0
            for s in reversed(current_chunk):
                s_words = len(s.split())
                if overlap_count + s_words <= overlap_words:
                    overlap_chunk.insert(0, s)
                    overlap_count += s_words
                else:
                    break
            current_chunk = overlap_chunk + [sent]
            current_word_count = sum(len(s.split()) for s in current_chunk)
        else:
            current_chunk.append(sent)
            current_word_count += len(words)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
