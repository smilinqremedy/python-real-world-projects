"""
Command-Line Interface for Document Question-Answering System (RAG).
"""
import argparse
import sys
import os
from rag_engine import RAGEngine
from document_loader import DocumentExtractionError


def main():
    parser = argparse.ArgumentParser(description="Intelligent Document Question-Answering System (RAG)")
    parser.add_argument("--ingest", nargs="+", help="File paths to PDF or TXT documents to ingest")
    parser.add_argument("--ask", type=str, help="Question to ask about ingested documents")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks")
    parser.add_argument("--min-sim", type=float, default=0.15, help="Minimum relevance threshold")
    parser.add_argument("--index-path", type=str, default="rag_index.npz", help="Vector store save/load path")

    args = parser.parse_args()
    engine = RAGEngine()

    # Load existing vector index if present
    if os.path.exists(args.index_path):
        engine.vector_store.load(args.index_path)

    if args.ingest:
        for path in args.ingest:
            if not os.path.exists(path):
                print(f"File not found: {path}", file=sys.stderr)
                continue
            try:
                res = engine.ingest_document(path)
                print(f"Ingested '{res['document']}': {res['pages_count']} pages, {res['chunks_count']} chunks.")
            except DocumentExtractionError as e:
                print(f"Error ingesting {path}: {e}", file=sys.stderr)

        engine.vector_store.save(args.index_path)
        print(f"Vector store saved to: {args.index_path}")
        if not args.ask:
            return

    if args.ask:
        if len(engine.vector_store.chunks) == 0:
            print("Error: Vector store is empty. Ingest documents first using --ingest <files>.", file=sys.stderr)
            sys.exit(1)

        result = engine.answer_question(args.ask, top_k=args.top_k, min_similarity=args.min_sim)
        print("\n" + "=" * 60)
        print(f"QUESTION: {args.ask}")
        print("=" * 60)
        print(f"GROUNDED ANSWER (Score: {result['relevance_score']:.2f}):\n")
        print(result["answer"])

        if result["sources"]:
            print("\n" + "-" * 60)
            print("VERIFIED SOURCES & CITATIONS:")
            for s in result["sources"]:
                print(f"- [{s['document']} (Page {s['page']})] Similarity: {s['similarity']:.2f}")
                print(f"  Excerpt: {s['excerpt']}\n")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
