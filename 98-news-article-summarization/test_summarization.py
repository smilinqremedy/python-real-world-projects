"""
Automated unit tests for AI News Article Summarization System.
"""
import unittest
import os
import shutil
import tempfile
import json

from text_preprocessor import clean_article_text, split_into_sentences, chunk_long_article
from nlp_extractor import extract_keywords, extract_named_entities
from summarizer import ArticleSummarizer
from metrics import compute_rouge, longest_common_subsequence


class TestArticleSummarization(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_article = (
            "SAN FRANCISCO — Artificial intelligence research laboratory OpenAI and cloud computing giant "
            "Microsoft announced a major expansion of their collaborative technical partnership on Tuesday. "
            "Under the new framework, the organizations will deploy specialized high-performance computing clusters "
            "in Washington and California to accelerate foundation model training. Dr. Elena Rostova, principal "
            "researcher at the AI Governance Institute in Geneva, commended the initiative for its explicit focus on "
            "computational efficiency and safety verification. The joint deployment is scheduled to commence "
            "operations by October 2026."
        )
        self.summarizer = ArticleSummarizer()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_text_cleaning_and_sentence_splitting(self):
        dirty_html = "<html><body><h1>News</h1><p>Visit https://example.com for more info. Advertisement</p>Hello world.</body></html>"
        cleaned = clean_article_text(dirty_html)
        self.assertNotIn("<html>", cleaned)
        self.assertNotIn("https://", cleaned)
        self.assertNotIn("Advertisement", cleaned)
        self.assertIn("Hello world.", cleaned)

        sents = split_into_sentences("Dr. Smith visited London. The conference began promptly at 9 AM.")
        self.assertEqual(len(sents), 2)
        self.assertIn("Dr. Smith visited London.", sents[0])

    def test_chunking_long_article(self):
        sentences = [f"Sentence number {i} provides detailed background information regarding policy." for i in range(30)]
        chunks = chunk_long_article(sentences, max_words=60, overlap_words=15)
        self.assertGreater(len(chunks), 1)

    def test_keyword_and_named_entity_extraction(self):
        keywords = extract_keywords(self.sample_article, top_n=5)
        self.assertTrue(len(keywords) > 0)
        kw_names = [k["keyword"] for k in keywords]
        self.assertTrue(any(w in ["intelligence", "computing", "partnership", "openai", "microsoft"] for w in kw_names))

        entities = extract_named_entities(self.sample_article)
        self.assertIn("organizations", entities)
        self.assertIn("locations", entities)
        self.assertIn("dates", entities)

    def test_summarization_modes(self):
        # Short mode (1-2 sentences)
        res_short = self.summarizer.summarize_article(self.sample_article, mode="short", method="extractive")
        self.assertTrue(res_short["success"])
        self.assertLess(res_short["summary_word_count"], res_short["original_word_count"])
        short_sents = split_into_sentences(res_short["summary"])
        self.assertLessEqual(len(short_sents), 2)

        # Detailed mode
        res_detailed = self.summarizer.summarize_article(self.sample_article, mode="detailed", method="extractive")
        self.assertTrue(res_detailed["success"])
        self.assertGreaterEqual(res_detailed["summary_word_count"], res_short["summary_word_count"])

    def test_rouge_evaluation_metrics(self):
        ref = "OpenAI and Microsoft expand computing partnership in Washington."
        cand = "OpenAI and Microsoft expand computing partnership in California."

        rouge = compute_rouge(ref, cand)
        self.assertIn("rouge_1", rouge)
        self.assertIn("rouge_2", rouge)
        self.assertIn("rouge_l", rouge)

        self.assertGreater(rouge["rouge_1"]["f1"], 0.70)
        self.assertGreater(rouge["rouge_2"]["f1"], 0.50)
        self.assertGreater(rouge["rouge_l"]["f1"], 0.70)

        # Identical text must score 1.0
        exact_rouge = compute_rouge(ref, ref)
        self.assertAlmostEqual(exact_rouge["rouge_1"]["f1"], 1.0, places=4)
        self.assertAlmostEqual(exact_rouge["rouge_l"]["f1"], 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
