"""
Automated unit tests for Intelligent Document Question-Answering System (RAG).
"""
import unittest
import os
import shutil
import tempfile
import numpy as np

from document_loader import DocumentLoader, DocumentPage, DocumentExtractionError
from chunker import TextChunker, DocumentChunk
from embeddings import EmbeddingEngine
from vector_store import VectorStore
from rag_engine import RAGEngine, ANTI_HALLUCINATION_FALLBACK


class TestDocumentQuestionAnswering(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_txt = os.path.join(self.test_dir, "sample_ai_policy.txt")
        self.index_file = os.path.join(self.test_dir, "test_index.npz")

        with open(self.sample_txt, "w", encoding="utf-8") as f:
            f.write(
                "Artificial Intelligence Governance Policy 2026.\n\n"
                "Section 1: Data Privacy and Security.\n"
                "All deep learning models must ensure that training datasets are anonymized and free of private credentials.\n"
                "Personal identifiable information must be encrypted using AES-256 standards.\n\n"
                "Section 2: Ethical Biometrics and Consent.\n"
                "Biometric facial recognition requires informed consent from participants prior to system registration.\n"
                "Manual alternatives must be provided for individuals who opt out of biometric verification.\n"
            )

        self.engine = RAGEngine()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_document_loader_txt_and_validation(self):
        pages = DocumentLoader.load_document(self.sample_txt)
        self.assertEqual(len(pages), 1)
        self.assertIn("Artificial Intelligence Governance", pages[0].text)

        # Missing file error
        with self.assertRaises(DocumentExtractionError):
            DocumentLoader.load_document("non_existent.txt")

        # Empty file error
        empty_file = os.path.join(self.test_dir, "empty.txt")
        with open(empty_file, "w") as f:
            pass
        with self.assertRaises(DocumentExtractionError):
            DocumentLoader.load_document(empty_file)

    def test_text_chunking(self):
        chunker = TextChunker(chunk_size=150, chunk_overlap=30)
        pages = [DocumentPage(doc_name="test.txt", page_number=1, text="Hello world! " * 20)]
        chunks = chunker.chunk_pages(pages)

        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertIsInstance(c, DocumentChunk)
            self.assertLessEqual(len(c.text), 180)
            self.assertEqual(c.doc_name, "test.txt")
            self.assertEqual(c.page_number, 1)

    def test_embeddings_and_vector_store(self):
        ee = EmbeddingEngine(embedding_dim=128)
        vec1 = ee.embed_text("Data privacy and biometric encryption standards.")
        vec2 = ee.embed_text("Data privacy and encryption security.")
        vec3 = ee.embed_text("Baking recipes for chocolate cake and strawberry cookies.")

        self.assertEqual(len(vec1), 128)
        # Cosine similarity between related topics should exceed unrelated topics
        sim_related = float(np.dot(vec1, vec2))
        sim_unrelated = float(np.dot(vec1, vec3))
        self.assertGreater(sim_related, sim_unrelated)

        # Vector store indexing and search
        vs = VectorStore(embedding_dim=128)
        chunk1 = DocumentChunk(chunk_id="c1", doc_name="doc1", page_number=1, text="Biometric consent policy.", char_start=0, char_end=25)
        vs.add_chunks([chunk1], np.array([vec1]))

        results = vs.similarity_search(vec2, top_k=1, min_similarity=0.1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].chunk_id, "c1")

        # Persistence
        vs.save(self.index_file)
        self.assertTrue(os.path.exists(self.index_file))

        vs2 = VectorStore(embedding_dim=128)
        vs2.load(self.index_file)
        self.assertEqual(len(vs2.chunks), 1)

    def test_rag_end_to_end_answering_and_grounding(self):
        self.engine.ingest_document(self.sample_txt)
        self.assertIn("sample_ai_policy.txt", self.engine.ingested_documents)

        # Relevant question
        res = self.engine.answer_question("What is the policy on biometric informed consent and manual alternatives?")
        self.assertTrue(res["is_grounded"])
        self.assertGreater(res["relevance_score"], 0.15)
        self.assertGreater(len(res["sources"]), 0)
        self.assertEqual(res["sources"][0]["document"], "sample_ai_policy.txt")
        self.assertEqual(res["sources"][0]["page"], 1)

    def test_anti_hallucination_guardrail(self):
        self.engine.ingest_document(self.sample_txt)

        # Completely unrelated question not present anywhere in policy document
        res = self.engine.answer_question("How do penguins survive Antarctic winters in subzero temperatures?", min_similarity=0.25)
        self.assertFalse(res["is_grounded"])
        self.assertEqual(res["answer"], ANTI_HALLUCINATION_FALLBACK)
        self.assertEqual(len(res["sources"]), 0)


if __name__ == "__main__":
    unittest.main()
