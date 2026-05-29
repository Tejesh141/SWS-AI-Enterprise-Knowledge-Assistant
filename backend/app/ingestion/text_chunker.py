"""
ingestion/text_chunker.py
──────────────────────────
Responsibility (Single Responsibility Principle):
    Split RawDocument pages into fixed-size, overlapping DocumentChunks.

Why RecursiveCharacterTextSplitter?
- Tries to split on paragraph → sentence → word boundaries in order,
  preserving semantic coherence better than a naive character split.
- chunk_overlap ensures context is not lost at chunk boundaries,
  which is critical for retrieval quality.

This module does NOT load PDFs or create embeddings.
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.models.document import DocumentChunk, RawDocument
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TextChunker:
    """
    Wraps LangChain's RecursiveCharacterTextSplitter and converts
    the output into typed DocumentChunk objects with rich metadata.

    Usage:
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk(raw_doc)
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        """
        Args:
            chunk_size:    Maximum number of characters per chunk.
            chunk_overlap: Number of characters shared between consecutive chunks.
        """
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            # Separator hierarchy: paragraph → newline → space → character
            separators=["\n\n", "\n", " ", ""],
        )

    # ── Public API ─────────────────────────────────────────────────────

    def chunk(self, raw_doc: RawDocument) -> list[DocumentChunk]:
        """
        Split a single RawDocument page into DocumentChunks.

        The chunk_id format is deterministic:
            "{file_name}_p{page_number}_c{chunk_index}"
        This makes deduplication and debugging straightforward.

        Args:
            raw_doc: A single page extracted from a PDF.

        Returns:
            List of DocumentChunk objects (may be empty if text is blank).
        """
        if not raw_doc.text.strip():
            return []

        raw_chunks: list[str] = self._splitter.split_text(raw_doc.text)

        chunks = [
            DocumentChunk(
                # Deterministic ID — safe to use as ChromaDB document ID
                chunk_id=self._build_chunk_id(raw_doc, idx),
                file_name=raw_doc.file_name,
                page_number=raw_doc.page_number,
                text=chunk_text,
            )
            for idx, chunk_text in enumerate(raw_chunks)
        ]

        logger.debug(
            "'%s' page %d → %d chunk(s)",
            raw_doc.file_name,
            raw_doc.page_number,
            len(chunks),
        )
        return chunks

    # ── Private helpers ────────────────────────────────────────────────

    @staticmethod
    def _build_chunk_id(raw_doc: RawDocument, chunk_index: int) -> str:
        """
        Build a globally unique, human-readable chunk identifier.

        Format: "report_q1.pdf_p3_c0"
                 ↑ file      ↑page ↑chunk index
        """
        # Replace spaces in filename to keep IDs filesystem-safe
        safe_name = raw_doc.file_name.replace(" ", "_")
        return f"{safe_name}_p{raw_doc.page_number}_c{chunk_index}"
