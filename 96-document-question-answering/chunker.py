"""
Document Chunking Module.
Splits document pages into meaningful overlapping text chunks preserving metadata.
"""
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from document_loader import DocumentPage


@dataclass
class DocumentChunk:
    chunk_id: str
    doc_name: str
    page_number: int
    text: str
    char_start: int
    char_end: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TextChunker:
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 80):
        if chunk_size <= chunk_overlap:
            raise ValueError("chunk_size must be strictly greater than chunk_overlap.")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: List[DocumentPage]) -> List[DocumentChunk]:
        """
        Splits a list of DocumentPages into overlapping chunks.
        """
        chunks: List[DocumentChunk] = []
        chunk_counter = 1

        for page in pages:
            text = page.text.strip()
            if not text:
                continue

            start = 0
            text_len = len(text)

            while start < text_len:
                end = min(start + self.chunk_size, text_len)

                # Try to adjust boundary to the nearest space or punctuation
                if end < text_len:
                    last_break = max(text.rfind(" ", start, end), text.rfind("\n", start, end))
                    if last_break > start + (self.chunk_size // 2):
                        end = last_break + 1

                chunk_text = text[start:end].strip()
                if chunk_text:
                    cid = f"{page.doc_name}_p{page.page_number}_c{chunk_counter}"
                    chunks.append(DocumentChunk(
                        chunk_id=cid,
                        doc_name=page.doc_name,
                        page_number=page.page_number,
                        text=chunk_text,
                        char_start=start,
                        char_end=end
                    ))
                    chunk_counter += 1

                if end >= text_len:
                    break
                start = end - self.chunk_overlap

        return chunks
