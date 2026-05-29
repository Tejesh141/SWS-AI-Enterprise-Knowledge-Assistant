"""
scripts/ingest_documents.py
────────────────────────────
Entry point for the Document Ingestion Pipeline (Phase 1).

Pipeline stages (left to right):
  PDF files
    → DocumentLoader   (extract raw text per page)
    → TextChunker      (split pages into overlapping chunks)
    → EmbeddingService (encode chunks as dense vectors)
    → ChromaService    (persist vectors + metadata to disk)

Design principles applied:
- Orchestration only — this script wires services together but contains
  no business logic itself (Dependency Inversion Principle)
- All configuration comes from .env via Settings (Open/Closed Principle)
- Each service is independently testable and replaceable

Run from /backend:
    python scripts/ingest_documents.py
"""

import sys
from pathlib import Path

# ── Ensure /backend is on sys.path when running as a script ───────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

# Load .env before importing settings (settings reads env vars at import time)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.config.settings import settings
from app.ingestion.document_loader import DocumentLoader
from app.ingestion.text_chunker import TextChunker
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


def run_ingestion_pipeline() -> None:
    """
    Orchestrate the full document ingestion pipeline.

    Metrics logged at the end:
    - Total documents (PDFs) processed
    - Total pages extracted
    - Total chunks created
    - Total embeddings stored in ChromaDB
    """
    logger.info("═" * 60)
    logger.info("SWS-AI Enterprise Knowledge Assistant — Ingestion Pipeline")
    logger.info("═" * 60)

    # ── Resolve paths relative to /backend ────────────────────────────
    base_dir   = Path(__file__).resolve().parents[1]
    pdf_dir    = base_dir / settings.pdf_dir
    chroma_dir = base_dir / settings.chroma_db_dir

    # ── Initialise services ────────────────────────────────────────────
    loader    = DocumentLoader(pdf_dir=pdf_dir)
    chunker   = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    embedder  = EmbeddingService(model_name=settings.embedding_model)
    chroma    = ChromaService(
        db_dir=chroma_dir,
        collection_name=settings.chroma_collection_name,
    )

    # ── Pipeline metrics ───────────────────────────────────────────────
    docs_processed  = 0
    pages_extracted = 0
    chunks_created  = 0
    embeddings_stored = 0

    # Track which files we've seen to count unique documents
    seen_files: set[str] = set()

    # ── Main pipeline loop ─────────────────────────────────────────────
    # DocumentLoader yields RawDocument objects lazily (generator),
    # so memory usage stays constant regardless of corpus size.
    all_chunks = []

    for raw_doc in loader.load():
        pages_extracted += 1

        # Count unique PDFs processed
        if raw_doc.file_name not in seen_files:
            seen_files.add(raw_doc.file_name)
            docs_processed += 1

            # Inform operator if this document was previously ingested
            if chroma.document_exists(raw_doc.file_name):
                logger.warning(
                    "Duplicate detected: '%s' already exists in the knowledge base "
                    "— chunks will be overwritten (upsert)",
                    raw_doc.file_name,
                )

        # Chunk the page text
        page_chunks = chunker.chunk(raw_doc)
        chunks_created += len(page_chunks)
        all_chunks.extend(page_chunks)

    if not all_chunks:
        logger.warning("No chunks produced — pipeline complete with nothing to store.")
        return

    # ── Embed all chunks in one batched call ───────────────────────────
    # Batching is more efficient than embedding page-by-page because the
    # model can parallelise across the full batch.
    embedded_chunks = embedder.embed_chunks(all_chunks)

    # ── Persist to ChromaDB ────────────────────────────────────────────
    chroma.upsert(embedded_chunks)
    embeddings_stored = len(embedded_chunks)

    # ── Final summary ──────────────────────────────────────────────────
    logger.info("═" * 60)
    logger.info("Ingestion Pipeline Complete")
    logger.info("  Documents processed : %d", docs_processed)
    logger.info("  Pages extracted     : %d", pages_extracted)
    logger.info("  Chunks created      : %d", chunks_created)
    logger.info("  Embeddings stored   : %d", embeddings_stored)
    logger.info("  ChromaDB total docs : %d", chroma.count())
    logger.info("═" * 60)


if __name__ == "__main__":
    run_ingestion_pipeline()
