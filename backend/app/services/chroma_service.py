"""
services/chroma_service.py
───────────────────────────
Responsibility (Single Responsibility Principle):
    Persist EmbeddedChunks into ChromaDB and handle deduplication.

Why ChromaDB?
- Embedded vector database — no separate server process needed
- Persists to disk automatically (PersistentClient)
- Native support for metadata filtering (file_name, page_number)
- Production-ready for single-node deployments

Deduplication strategy:
- ChromaDB uses `chunk_id` as the document ID
- Calling `upsert` instead of `add` means re-ingesting the same PDF
  will overwrite existing chunks rather than creating duplicates.
  This is the correct behaviour for a document update workflow.
"""

from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models.document import EmbeddedChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaService:
    """
    Manages a persistent ChromaDB collection for the knowledge base.

    Usage:
        service = ChromaService(db_dir=Path("data/chroma_db"), collection_name="kb")
        service.upsert(embedded_chunks)
        count = service.count()
    """

    def __init__(self, db_dir: Path, collection_name: str) -> None:
        """
        Initialise the ChromaDB persistent client and get/create the collection.

        Args:
            db_dir:          Directory where ChromaDB stores its SQLite + vector files.
            collection_name: Logical name for the collection (like a table name).
        """
        db_dir.mkdir(parents=True, exist_ok=True)

        # PersistentClient writes to disk automatically — no manual `.persist()` needed
        self._client = chromadb.PersistentClient(
            path=str(db_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # get_or_create_collection is idempotent — safe to call on every startup
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            # cosine distance is standard for sentence-transformer embeddings
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            "ChromaDB ready | collection='%s' | existing docs=%d",
            collection_name,
            self._collection.count(),
        )

    # ── Public API ─────────────────────────────────────────────────────

    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """
        Insert or update a batch of EmbeddedChunks in the collection.

        Using `upsert` (not `add`) provides automatic deduplication:
        - New chunk_id  → inserted
        - Existing chunk_id → updated (handles re-ingestion of updated PDFs)

        Args:
            chunks: List of EmbeddedChunk objects to persist.
        """
        if not chunks:
            logger.warning("upsert called with empty chunk list — nothing to store")
            return

        # ChromaDB expects parallel lists, not a list of dicts
        ids        = [c.chunk_id    for c in chunks]
        embeddings = [c.embedding   for c in chunks]
        documents  = [c.text        for c in chunks]
        metadatas  = [
            {
                "file_name":   c.file_name,
                "page_number": c.page_number,
                "chunk_id":    c.chunk_id,
            }
            for c in chunks
        ]

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            "Upserted %d chunk(s) → collection total: %d",
            len(chunks),
            self._collection.count(),
        )

    def count(self) -> int:
        """Return the total number of vectors stored in the collection."""
        return self._collection.count()

    def document_exists(self, file_name: str) -> bool:
        """
        Check whether any chunks from a given file already exist.

        Used by the ingestion pipeline to detect and log duplicate documents
        before upserting (so the operator knows a re-ingestion is happening).

        Args:
            file_name: The PDF filename to check.

        Returns:
            True if at least one chunk from this file is already stored.
        """
        results = self._collection.get(
            where={"file_name": file_name},
            limit=1,
            include=[],  # We only need to know if any result exists
        )
        return len(results["ids"]) > 0
