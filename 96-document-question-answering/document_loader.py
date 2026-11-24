"""
Document Loading and Text Extraction for PDF and TXT Files.
Includes native PDF stream parsing and graceful error handling for empty or corrupted documents.
"""
import os
import re
from dataclasses import dataclass
from typing import List, Optional


class DocumentExtractionError(Exception):
    """Raised when document extraction fails due to format corruption or empty content."""
    pass


@dataclass
class DocumentPage:
    doc_name: str
    page_number: int
    text: str


class DocumentLoader:
    @staticmethod
    def load_document(file_path: str) -> List[DocumentPage]:
        """
        Loads document from file_path (PDF or TXT) and returns a list of DocumentPage objects.
        """
        if not os.path.exists(file_path):
            raise DocumentExtractionError(f"File not found: {file_path}")

        if os.path.getsize(file_path) == 0:
            raise DocumentExtractionError(f"Document is empty (0 bytes): {file_path}")

        _, ext = os.path.splitext(file_path.lower())
        doc_name = os.path.basename(file_path)

        if ext == ".txt":
            return DocumentLoader._load_txt(file_path, doc_name)
        elif ext == ".pdf":
            return DocumentLoader._load_pdf(file_path, doc_name)
        else:
            raise DocumentExtractionError(f"Unsupported document format '{ext}'. Supported: .pdf, .txt")

    @staticmethod
    def _load_txt(file_path: str, doc_name: str) -> List[DocumentPage]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
        except Exception as e:
            raise DocumentExtractionError(f"Failed to read text file: {e}")

        if not content:
            raise DocumentExtractionError(f"Text document contains no readable text: {doc_name}")

        return [DocumentPage(doc_name=doc_name, page_number=1, text=content)]

    @staticmethod
    def _load_pdf(file_path: str, doc_name: str) -> List[DocumentPage]:
        # Attempt pypdf first if installed
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages = []
            for idx, page in enumerate(reader.pages, start=1):
                t = page.extract_text() or ""
                if t.strip():
                    pages.append(DocumentPage(doc_name=doc_name, page_number=idx, text=t.strip()))
            if pages:
                return pages
        except Exception:
            pass

        # Native fallback PDF text extractor
        try:
            with open(file_path, "rb") as f:
                raw = f.read()

            # Find PDF text objects between BT (Begin Text) and ET (End Text) or Tj/TJ strings
            text_chunks = []
            # Extract parenthesized strings inside PDF streams: \((.*?)\)\s*Tj
            matches = re.findall(rb"\((.*?)\)\s*Tj", raw)
            for m in matches:
                try:
                    decoded = m.decode("latin1", errors="ignore").strip()
                    if decoded and len(decoded) > 1:
                        text_chunks.append(decoded)
                except Exception:
                    continue

            extracted = " ".join(text_chunks)
            if not extracted:
                # Fallback to general printable ASCII string extraction
                clean_ascii = re.findall(rb"[A-Za-z0-9 .,;:!?'\"\-\n]{4,}", raw)
                extracted = " ".join(b.decode("latin1") for b in clean_ascii if b"PDF" not in b)

            if not extracted.strip():
                raise DocumentExtractionError(f"PDF document contains no extractable text streams: {doc_name}")

            return [DocumentPage(doc_name=doc_name, page_number=1, text=extracted.strip())]
        except DocumentExtractionError:
            raise
        except Exception as e:
            raise DocumentExtractionError(f"Failed to extract text from PDF: {e}")
