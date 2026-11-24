"""
Retrieval-Augmented Generation (RAG) Engine.
Coordinates ingestion, chunking, embedding, semantic search, and grounded answer synthesis.
Enforces strict anti-hallucination guardrails and source citation tracking.
"""
import os
import re
from typing import List, Dict, Any, Optional
import numpy as np

from document_loader import DocumentLoader, DocumentExtractionError
from chunker import TextChunker, DocumentChunk
from embeddings import EmbeddingEngine
from vector_store import VectorStore

ANTI_HALLUCINATION_FALLBACK = (
    "I cannot find sufficient evidence in the uploaded documents to answer this question. "
    "To prevent hallucination, an answer is only generated when verified by retrieved document excerpts."
)


class RAGEngine:
    def __init__(
        self,
        chunk_size: int = 400,
        chunk_overlap: int = 80,
        vector_store: Optional[VectorStore] = None,
        embedding_engine: Optional[EmbeddingEngine] = None
    ):
        self.loader = DocumentLoader()
        self.chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore()
        self.ingested_documents: List[str] = []

    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """
        Loads document, extracts text pages, creates chunks, computes embeddings,
        and indexes chunks in the vector store.
        """
        pages = self.loader.load_document(file_path)
        chunks = self.chunker.chunk_pages(pages)

        if not chunks:
            raise DocumentExtractionError(f"No valid text chunks could be created from '{file_path}'.")

        texts = [c.text for c in chunks]
        embeddings = self.embedding_engine.embed_batch(texts)
        self.vector_store.add_chunks(chunks, embeddings)

        doc_name = os.path.basename(file_path)
        if doc_name not in self.ingested_documents:
            self.ingested_documents.append(doc_name)

        return {
            "document": doc_name,
            "pages_count": len(pages),
            "chunks_count": len(chunks),
            "total_indexed_chunks": len(self.vector_store.chunks)
        }

    def answer_question(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.20
    ) -> Dict[str, Any]:
        """
        Retrieves relevant document sections, validates relevance against threshold
        to prevent hallucinations, and synthesizes a grounded answer with page citations.
        """
        clean_query = query.strip()
        if not clean_query:
            return {
                "answer": "Please enter a valid question.",
                "is_grounded": False,
                "relevance_score": 0.0,
                "sources": []
            }

        query_vec = self.embedding_engine.embed_text(clean_query)
        retrieved = self.vector_store.similarity_search(query_vec, top_k=top_k, min_similarity=min_similarity)

        # Anti-Hallucination Guardrail Check 1: Similarity threshold
        if not retrieved:
            return {
                "answer": ANTI_HALLUCINATION_FALLBACK,
                "is_grounded": False,
                "relevance_score": 0.0,
                "sources": []
            }

        top_chunk, top_score = retrieved[0]

        # Anti-Hallucination Guardrail Check 2: Content Keyword verification
        # Extract meaningful content terms (len >= 4) from query
        query_terms = set(re.findall(r"\b[a-z]{4,}\b", clean_query.lower()))
        retrieved_text = " ".join(c.text.lower() for c, _ in retrieved)
        term_matches = [t for t in query_terms if t in retrieved_text]

        if query_terms and len(term_matches) == 0:
            return {
                "answer": ANTI_HALLUCINATION_FALLBACK,
                "is_grounded": False,
                "relevance_score": 0.0,
                "sources": []
            }

        # Extract most informative grounded sentences matching question keywords
        keywords = set(re.findall(r"\b\w{4,}\b", clean_query.lower()))
        supporting_sentences = []

        for chunk, score in retrieved:
            sentences = re.split(r"(?<=[.!?])\s+", chunk.text)
            for s in sentences:
                s_words = set(re.findall(r"\b\w{4,}\b", s.lower()))
                overlap = len(keywords.intersection(s_words))
                if overlap > 0:
                    supporting_sentences.append(s.strip())

        # Synthesize answer
        if supporting_sentences:
            grounded_answer = " ".join(dict.fromkeys(supporting_sentences[:3]))
        else:
            grounded_answer = top_chunk.text

        # Format source citations
        citations = []
        for chunk, score in retrieved:
            citations.append({
                "document": chunk.doc_name,
                "page": chunk.page_number,
                "chunk_id": chunk.chunk_id,
                "similarity": score,
                "excerpt": chunk.text[:180] + ("..." if len(chunk.text) > 180 else "")
            })

        return {
            "answer": grounded_answer,
            "is_grounded": True,
            "relevance_score": top_score,
            "sources": citations
        }
