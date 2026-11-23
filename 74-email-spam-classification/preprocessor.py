"""
Text Preprocessor and Keyword Extractor for Email Spam Classification.
"""
import re
import string
from typing import List, Set


SPAM_TRIGGER_WORDS: Set[str] = {
    "urgent", "winner", "prize", "lottery", "guaranteed", "bitcoin", "crypto",
    "wire", "transfer", "inheritance", "viagra", "cialis", "prescription",
    "suspended", "free", "claim", "instant", "cash", "credit", "invest",
    "unauthorized", "unpaid", "act now", "100%", "double your", "earn money"
}


def clean_text(text: str) -> str:
    """
    Cleans raw email text:
    - Lowercase
    - Replace URLs with 'urltoken'
    - Replace currency / amounts with 'moneytoken'
    - Remove punctuation and numbers
    - Normalize whitespace
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()
    # Replace URLs
    text = re.sub(r"https?://\S+|www\.\S+", "urltoken", text)
    # Replace monetary amounts
    text = re.sub(r"\$\d+(?:,\d+)*(?:\.\d+)?", "moneytoken", text)
    # Remove punctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # Remove remaining numbers
    text = re.sub(r"\d+", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_spam_keywords(text: str) -> List[str]:
    """
    Scans raw text for high-risk spam indicators.
    """
    lower = text.lower()
    detected = []
    for kw in sorted(SPAM_TRIGGER_WORDS):
        if re.search(r"\b" + re.escape(kw) + r"\b", lower):
            detected.append(kw)
    return detected
