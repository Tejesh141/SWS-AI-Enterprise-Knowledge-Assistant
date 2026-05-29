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


class RetrievalResult(BaseModel):
    """
    A single ranked result returned by the RetrievalService.
    This is the public-facing contract consumed by the API layer (Phase 2)
    and any downstream LLM prompt-builder.

    Fields map directly to the four required outputs:
        chunk_text       → the verbatim text passage to inject into the LLM prompt
        similarity_score → cosine similarity in [0, 1]; higher = more relevant
        source_document  → original PDF filename for citation / provenance
        page_number      → exact page for human verification
    """
    chunk_text: str
    similarity_score: float   # Normalised cosine similarity: 1.0 = identical
    source_document: str      # e.g. "annual_report_2024.pdf"
    page_number: int


# ── Chat API schemas ───────────────────────────────────────────────────────────
# These are the request/response contracts for POST /api/chat.
# Keeping them in document.py centralises all domain models in one place.

class ChatRequest(BaseModel):
    """
    Incoming payload for POST /api/chat.
    Validated automatically by FastAPI before the handler is called.
    """
    question: str


class SourceReference(BaseModel):
    """
    A single citation entry in the chat response.

    `document` strips the .pdf extension for a cleaner UI display:
        "Leave_Policy.pdf"  →  "Leave Policy"
    """
    document: str   # Human-readable document name (no extension, underscores → spaces)
    page: int


class ChatResponse(BaseModel):
    """
    Response payload for POST /api/chat.

    answer  → Gemini-generated answer grounded strictly in retrieved context.
    sources → Deduplicated list of source citations for the answer.
    """
    answer: str
    sources: list[SourceReference]
