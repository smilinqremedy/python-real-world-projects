"""
Natural Language Processing (NLP) Feature Extractor:
Keywords (TF-IDF) and Named Entity Recognition (NER: Person, Org, Location, Date).
"""
import re
from collections import Counter
from typing import List, Dict, Any, Set

STOP_WORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "how", "what", "which", "who", "whom",
    "this", "that", "these", "those", "it", "its", "as", "if", "after", "before",
    "into", "over", "under", "about", "above", "also", "said", "says", "inc", "co"
}

KNOWN_LOCATIONS = {
    "washington", "london", "paris", "tokyo", "beijing", "berlin", "geneva", "brussels",
    "new york", "san francisco", "california", "europe", "asia", "america", "africa"
}

KNOWN_ORGS = {
    "google", "microsoft", "apple", "amazon", "openai", "meta", "tesla", "spacex",
    "united nations", "european union", "who", "federal reserve", "imf", "world bank"
}


def extract_keywords(text: str, top_n: int = 8) -> List[Dict[str, Any]]:
    """
    Extracts prominent keywords based on Term Frequency (TF) with stopword exclusion.
    """
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    counts = Counter(filtered)

    total_words = len(filtered)
    if total_words == 0:
        return []

    return [
        {"keyword": k, "frequency": count, "relevance_score": round(count / total_words, 4)}
        for k, count in counts.most_common(top_n)
    ]


def extract_named_entities(text: str) -> Dict[str, List[str]]:
    """
    Identifies Named Entities: Person, Organization, Location, and Date.
    Uses contextual regex and linguistic pattern recognition.
    """
    persons = set()
    orgs = set()
    locations = set()
    dates = set()

    # 1. Dates: e.g. "January 15, 2026", "2026", "October 24"
    date_patterns = [
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s+\d{4})?\b",
        r"\b\d{4}\b",
        r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b"
    ]
    for pat in date_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            dates.add(m.group(0))

    # 2. Persons: Honorifics + Capitalized Names or Title-cased Full Names
    person_pattern = r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.|President|CEO|Minister)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    for m in re.finditer(person_pattern, text):
        persons.add(m.group(1))

    # Two-word proper nouns: e.g. "Satya Nadella", "Sam Altman"
    capital_pairs = re.findall(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b", text)
    for pair in capital_pairs:
        pair_lower = pair.lower()
        if pair_lower in KNOWN_LOCATIONS:
            locations.add(pair)
        elif pair_lower in KNOWN_ORGS:
            orgs.add(pair)
        elif not any(w in STOP_WORDS for w in pair_lower.split()):
            # Candidate person
            persons.add(pair)

    # 3. Known Orgs and Locations lookup
    text_lower = text.lower()
    for loc in KNOWN_LOCATIONS:
        if loc in text_lower:
            locations.add(loc.title())

    for org in KNOWN_ORGS:
        if org in text_lower:
            orgs.add(org.title())

    # Corporate suffix entities: e.g. "Corp", "Inc", "Technologies"
    corp_matches = re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?\s+(?:Inc|Corp|Ltd|GmbH|Group|Foundation))\b", text)
    for c in corp_matches:
        orgs.add(c)

    return {
        "persons": sorted(list(persons))[:6],
        "organizations": sorted(list(orgs))[:6],
        "locations": sorted(list(locations))[:6],
        "dates": sorted(list(dates))[:6]
    }
