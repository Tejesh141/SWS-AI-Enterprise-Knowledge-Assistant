"""
scripts/ingest_documents.py
────────────────────────────
Entry point for the Document Ingestion Pipeline.

Pipeline stages (left to right):
  PDF files
    → DocumentLoader   (extract raw text per page)
    → TextChunker      (split pages into overlapping chunks with chunk_index)
    → EmbeddingService (encode chunks as dense 384-dim vectors)
    → ChromaService    (persist vectors + full metadata to sws_ai_knowledge_base)

Design principles:
- Orchestration only — no business logic lives here
- All config from .env via Settings (Open/Closed Principle)
- Each service is independently testable and replaceable

Run from /backend:
    python scripts/ingest_documents.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

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

    Metrics logged at completion:
        - Documents (PDFs) processed
        - Pages extracted
        - Chunks created
        - Embeddings stored in ChromaDB
        - Duplicates skipped (documents already in collection)
    """
    logger.info("═" * 60)
    logger.info("SWS-AI Enterprise Knowledge Assistant — Ingestion Pipeline")
    logger.info("Collection: %s", settings.chroma_collection_name)
    logger.info("═" * 60)

    base_dir   = Path(__file__).resolve().parents[1]
    pdf_dir    = base_dir / settings.pdf_dir
    chroma_dir = base_dir / settings.chroma_db_dir

    # ── Initialise services ────────────────────────────────────────────
    loader   = DocumentLoader(pdf_dir=pdf_dir)
    chunker  = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    embedder = EmbeddingService(model_name=settings.embedding_model)

    # ChromaService now receives the embedding_service so search() works
    chroma = ChromaService(
        db_dir=chroma_dir,
        embedding_service=embedder,
        collection_name=settings.chroma_collection_name,
    )

    # ── Pipeline metrics ───────────────────────────────────────────────
    docs_processed    = 0
    pages_extracted   = 0
    chunks_created    = 0
    duplicates_skipped = 0
    seen_files: set[str] = set()
    all_chunks = []

    # ── Main pipeline loop ─────────────────────────────────────────────
    skipped_files: set[str] = set()

    for raw_doc in loader.load():
        pages_extracted += 1

        if raw_doc.file_name in skipped_files:
            continue

        if raw_doc.file_name not in seen_files:
            seen_files.add(raw_doc.file_name)

            if chroma.document_exists(raw_doc.file_name):
                logger.warning(
                    "Duplicate skipped | file='%s' already in collection",
                    raw_doc.file_name,
                )
                duplicates_skipped += 1
                skipped_files.add(raw_doc.file_name)
                continue

            docs_processed += 1

        page_chunks = chunker.chunk(raw_doc)
        chunks_created += len(page_chunks)
        all_chunks.extend(page_chunks)

    if not all_chunks:
        logger.warning("No new chunks to store — pipeline complete.")
        return

    # ── Embed all chunks in one batched call ───────────────────────────
    embedded_chunks = embedder.embed_chunks(all_chunks)

    # ── Persist to ChromaDB ────────────────────────────────────────────
    stored = chroma.insert(embedded_chunks)

    # ── Print collection stats ─────────────────────────────────────────
    stats = chroma.get_stats()

    logger.info("═" * 60)
    logger.info("Ingestion Pipeline Complete")
    logger.info("  Documents processed  : %d", docs_processed)
    logger.info("  Duplicates skipped   : %d", duplicates_skipped)
    logger.info("  Pages extracted      : %d", pages_extracted)
    logger.info("  Chunks created       : %d", chunks_created)
    logger.info("  Embeddings stored    : %d", stored)
    logger.info("  Collection total     : %d vectors", stats.total_vectors)
    logger.info("  Unique documents     : %d", stats.unique_documents)
    logger.info("  Documents in KB      : %s", stats.document_names)
    logger.info("═" * 60)


if __name__ == "__main__":
    run_ingestion_pipeline()
