"""
models/document.py
──────────────────
Pydantic domain models that act as typed contracts between pipeline stages.

Pipeline data flow:
  PDF file → RawDocument → [chunker] → DocumentChunk → [embedder] → EmbeddedChunk

Using Pydantic ensures:
- Automatic validation at each stage boundary
- Clear, self-documenting data contracts (important for team codebases)
- Easy serialisation for logging / debugging
"""

from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    """
    Represents a single page extracted from a PDF.
    Produced by DocumentLoader, consumed by TextChunker.
    """
    file_name: str          # Original PDF filename, e.g. "policy_v2.pdf"
    page_number: int        # 1-based page index
    text: str               # Raw extracted text for this page
    total_pages: int        # Total pages in the source PDF (useful for metadata)


class DocumentChunk(BaseModel):
    """
    A text chunk produced by splitting a RawDocument page.
    Produced by TextChunker, consumed by EmbeddingService.
    """
    chunk_id: str           # Globally unique ID: "{file_name}_p{page}_c{idx}"
    file_name: str
    page_number: int
    text: str               # The actual chunk text sent to the embedding model


class EmbeddedChunk(BaseModel):
    """
    A DocumentChunk enriched with its vector embedding.
    Produced by EmbeddingService, consumed by ChromaService.
    """
    chunk_id: str
    file_name: str
    page_number: int
    text: str
    embedding: list[float] = Field(default_factory=list)
