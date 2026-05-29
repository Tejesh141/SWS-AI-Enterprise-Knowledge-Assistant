"""
services/chroma_service.py
───────────────────────────
Responsibility (Single Responsibility Principle):
    All ChromaDB interactions for the SWS-AI knowledge base live here.
    No other module touches the ChromaDB client directly.

Capabilities provided:
    - initialize_collection  : get-or-create the persistent collection
    - insert                 : store embedded chunks with full metadata
    - search                 : embed a query and return top-k ranked results
    - document_exists        : duplicate-ingestion guard
    - delete_document        : remove all chunks belonging to one PDF
    - get_stats              : collection health / size metrics
    - count                  : total vector count (used by ingestion pipeline)
    - query                  : raw ANN search (used by RetrievalService)

Why ChromaDB?
    See README.md — # Why ChromaDB? section.

Persistence strategy:
    PersistentClient writes every upsert to a local SQLite + HNSW index
    under `data/chroma_db/`. No manual `.persist()` call is needed.
    Data survives application restarts automatically.

Deduplication strategy:
    `upsert` (not `add`) is used for all writes. ChromaDB uses `chunk_id`
    as the primary key, so re-ingesting the same PDF overwrites stale
    vectors rather than creating duplicates. The `document_exists` method
    lets the caller log a warning before the upsert happens.

Collection name: sws_ai_knowledge_base
    Named after the project to avoid collisions if multiple projects
    share the same ChromaDB data directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.models.document import EmbeddedChunk, SearchResult
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Collection name is a module constant so it can be referenced in tests
# without importing settings, keeping test setup minimal.
COLLECTION_NAME = "sws_ai_knowledge_base"


@dataclass
class CollectionStats:
    """
    Snapshot of collection health metrics.

    Returned by get_stats() and used for logging, monitoring dashboards,
    and the /health endpoint in future phases.
    """
    collection_name: str
    total_vectors: int          # Total number of stored chunk embeddings
    unique_documents: int       # Number of distinct source PDFs
    document_names: list[str]   # Sorted list of ingested PDF filenames


class ChromaService:
    """
    Manages the persistent ChromaDB collection for the SWS-AI knowledge base.

    This class is the single gateway to ChromaDB. All other services
    (ingestion pipeline, retrieval service) call methods on this class —
    they never import chromadb directly. This enforces the
    Open/Closed Principle: swapping ChromaDB for another vector store
    only requires changes here, nowhere else.

    Usage:
        svc = ChromaService(
            db_dir=Path("data/chroma_db"),
            embedding_service=EmbeddingService(model_name=...),
        )
        svc.insert(embedded_chunks)
        results = svc.search("What is the leave policy?", k=3)
    """

    def __init__(
        self,
        db_dir: Path,
        embedding_service: EmbeddingService,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        """
        Initialise the ChromaDB persistent client and get/create the collection.

        The embedding_service is injected here (Dependency Inversion Principle)
        so that search() can embed the query using the same model that was used
        during ingestion — a hard requirement for meaningful similarity scores.

        Args:
            db_dir:            Local directory for ChromaDB's SQLite + HNSW files.
            embedding_service: Shared EmbeddingService instance (model loaded once).
            collection_name:   ChromaDB collection identifier.
        """
        db_dir.mkdir(parents=True, exist_ok=True)

        self._embedder = embedding_service

        # PersistentClient: all writes are flushed to disk automatically.
        # anonymized_telemetry=False: no usage data sent to Chroma's servers.
        self._client = chromadb.PersistentClient(
            path=str(db_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self._collection = self._initialize_collection(collection_name)

    # ── Initialisation ─────────────────────────────────────────────────

    def _initialize_collection(
        self, collection_name: str
    ) -> chromadb.Collection:
        """
        Get an existing collection or create it if it doesn't exist.

        `get_or_create_collection` is idempotent — safe to call on every
        application startup without risk of data loss.

        The `hnsw:space` metadata key tells ChromaDB to use cosine distance
        for the HNSW index. This is the correct choice for sentence-transformer
        embeddings, which are L2-normalised by default.

        Args:
            collection_name: Name of the ChromaDB collection.

        Returns:
            The ChromaDB Collection object.
        """
        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        existing = collection.count()
        if existing == 0:
            logger.info(
                "Collection created | name='%s' | status=empty", collection_name
            )
        else:
            logger.info(
                "Collection loaded  | name='%s' | existing_vectors=%d",
                collection_name,
                existing,
            )

        return collection

    # ── Write operations ───────────────────────────────────────────────

    def insert(self, chunks: list[EmbeddedChunk]) -> int:
        """
        Persist a batch of EmbeddedChunks to the collection.

        Stores the following for every chunk (requirement §3):
            id                   → chunk.chunk_id  (globally unique)
            chunk_text           → chunk.text       (stored as ChromaDB document)
            embedding vector     → chunk.embedding  (384-dim float list)
            source_document_name → chunk.file_name  (in metadata)
            page_number          → chunk.page_number (in metadata)
            chunk_index          → chunk.chunk_index (in metadata)

        Uses `upsert` not `add`:
            - Re-ingesting the same PDF overwrites stale vectors (no duplicates)
            - Idempotent: safe to call multiple times with the same data

        Args:
            chunks: List of EmbeddedChunk objects ready for storage.

        Returns:
            Number of chunks actually upserted (0 if input was empty).
        """
        if not chunks:
            logger.warning("insert() called with empty list — nothing stored")
            return 0

        ids        = [c.chunk_id    for c in chunks]
        embeddings = [c.embedding   for c in chunks]
        documents  = [c.text        for c in chunks]
        metadatas  = [
            {
                # All six required fields stored in metadata for filtering + display
                "source_document_name": c.file_name,
                "page_number":          c.page_number,
                "chunk_index":          c.chunk_index,
                "chunk_id":             c.chunk_id,
                # Redundant with `documents` field but useful for metadata-only queries
                "chunk_text_preview":   c.text[:120],
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
            "Embeddings inserted | count=%d | collection_total=%d",
            len(chunks),
            self._collection.count(),
        )
        return len(chunks)

    # Keep `upsert` as an alias so the existing ingestion pipeline
    # (ingest_documents.py) continues to work without modification.
    def upsert(self, chunks: list[EmbeddedChunk]) -> None:
        """Alias for insert() — preserves backward compatibility."""
        self.insert(chunks)

    def delete_document(self, file_name: str) -> int:
        """
        Remove all chunks belonging to a specific source document.

        Use case: a PDF has been updated and needs to be re-ingested cleanly.
        Calling delete_document() first ensures no stale chunks remain from
        the old version, then re-run the ingestion pipeline for the new file.

        Args:
            file_name: The PDF filename whose chunks should be deleted,
                       e.g. "Leave_Policy.pdf".

        Returns:
            Number of chunks deleted (0 if document was not found).
        """
        # First check how many chunks exist for this document
        existing = self._collection.get(
            where={"source_document_name": file_name},
            include=[],  # IDs only — no need to fetch text or embeddings
        )
        chunk_ids = existing["ids"]

        if not chunk_ids:
            logger.warning(
                "delete_document: '%s' not found in collection — nothing deleted",
                file_name,
            )
            return 0

        self._collection.delete(ids=chunk_ids)

        logger.info(
            "Document deleted | file='%s' | chunks_removed=%d | collection_total=%d",
            file_name,
            len(chunk_ids),
            self._collection.count(),
        )
        return len(chunk_ids)

    # ── Read operations ────────────────────────────────────────────────

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        """
        Semantic similarity search — the primary retrieval interface.

        This is the method called by test_retrieval.py and any external
        consumer that wants a clean, typed result without dealing with
        raw ChromaDB response dicts.

        Process (requirement §6):
            1. Validate query is non-empty.
            2. Embed the query using the injected EmbeddingService.
               CRITICAL: must use the same model as ingestion, otherwise
               the query vector lives in a different semantic space and
               similarity scores are meaningless.
            3. Run ANN search in ChromaDB (cosine distance).
            4. Convert distance → similarity score: score = 1 - distance.
            5. Return typed SearchResult objects sorted best-first.

        Args:
            query: Natural-language question or keyword phrase.
            k:     Maximum number of results to return (default 3).

        Returns:
            List of SearchResult objects, sorted by descending similarity.
            Returns empty list if collection is empty.

        Raises:
            ValueError: If query is blank.
        """
        query = query.strip()
        if not query:
            raise ValueError("search() requires a non-empty query string")

        total = self._collection.count()
        if total == 0:
            logger.warning(
                "search() called on empty collection — run ingestion pipeline first"
            )
            return []

        logger.info(
            "Retrieval request | query='%s' | k=%d | collection_size=%d",
            query, k, total,
        )

        # ── Embed the query ────────────────────────────────────────────
        query_vector = self._embedder.embed_query(query)

        # ── ANN search ─────────────────────────────────────────────────
        # n_results cannot exceed the number of stored vectors
        n = min(k, total)
        raw = self._collection.query(
            query_embeddings=[query_vector],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        # ── Build typed results ────────────────────────────────────────
        results = self._parse_search_results(raw)

        logger.info(
            "Retrieval results | returned=%d | top_score=%.4f",
            len(results),
            results[0].score if results else 0.0,
        )
        return results

    def document_exists(self, file_name: str) -> bool:
        """
        Check whether any chunks from a given PDF are already stored.

        Used by the ingestion pipeline to detect duplicate ingestion attempts
        and log a warning before proceeding with the upsert.

        Args:
            file_name: PDF filename to check, e.g. "Leave_Policy.pdf".

        Returns:
            True if at least one chunk from this file exists in the collection.
        """
        results = self._collection.get(
            where={"source_document_name": file_name},
            limit=1,
            include=[],
        )
        exists = len(results["ids"]) > 0

        if exists:
            logger.info(
                "Duplicate check | file='%s' | status=EXISTS — will be skipped or overwritten",
                file_name,
            )
        return exists

    def get_stats(self) -> CollectionStats:
        """
        Return a snapshot of collection health metrics.

        Fetches all metadata from the collection (IDs + metadata only,
        no embeddings or documents to keep it lightweight) and computes:
            - total vector count
            - number of unique source documents
            - sorted list of document names

        Returns:
            CollectionStats dataclass instance.
        """
        total = self._collection.count()

        if total == 0:
            return CollectionStats(
                collection_name=self._collection.name,
                total_vectors=0,
                unique_documents=0,
                document_names=[],
            )

        # Fetch all metadata — include=[] means IDs only, which is fastest.
        # We need metadatas to extract document names, so include that.
        all_meta = self._collection.get(include=["metadatas"])
        doc_names = sorted(
            {m["source_document_name"] for m in all_meta["metadatas"]}
        )

        stats = CollectionStats(
            collection_name=self._collection.name,
            total_vectors=total,
            unique_documents=len(doc_names),
            document_names=doc_names,
        )

        logger.info(
            "Collection stats | total_vectors=%d | unique_docs=%d | docs=%s",
            stats.total_vectors,
            stats.unique_documents,
            stats.document_names,
        )
        return stats

    def count(self) -> int:
        """Return total number of vectors in the collection."""
        return self._collection.count()

    def query(self, query_embedding: list[float], top_k: int) -> dict:
        """
        Raw ANN search used by RetrievalService.

        Returns the unprocessed ChromaDB response dict so RetrievalService
        can apply its own domain logic (threshold filtering, model conversion).
        External callers that want typed results should use search() instead.

        Args:
            query_embedding: Pre-computed 384-dim query vector.
            top_k:           Maximum number of nearest neighbours.

        Returns:
            Raw ChromaDB result dict: {ids, documents, metadatas, distances}
        """
        if self._collection.count() == 0:
            logger.warning("query() called on empty collection")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

    # ── Private helpers ────────────────────────────────────────────────

    @staticmethod
    def _parse_search_results(raw: dict) -> list[SearchResult]:
        """
        Convert raw ChromaDB query response into typed SearchResult objects.

        ChromaDB wraps results in a batch dimension (list of lists) because
        it supports multi-query calls. We always send one query, so we
        unwrap with [0].

        Distance → similarity conversion:
            ChromaDB cosine space: distance = 1 - cosine_similarity
            Therefore:             score    = 1 - distance
            Range with sentence-transformers: approximately [0.0, 1.0]
            Score of 1.0 = identical vectors (exact match)
            Score of 0.0 = orthogonal vectors (completely unrelated)

        Missing metadata fields are handled defensively with .get() +
        fallback values so a single malformed record never crashes retrieval.

        Args:
            raw: Direct return value from collection.query().

        Returns:
            List of SearchResult objects sorted by descending score.
        """
        documents = raw["documents"][0]   # list[str]  — chunk texts
        metadatas = raw["metadatas"][0]   # list[dict] — stored metadata
        distances = raw["distances"][0]   # list[float] — cosine distances

        results: list[SearchResult] = []

        for text, meta, distance in zip(documents, metadatas, distances):
            # Guard: skip records with invalid/missing metadata
            if not meta:
                logger.warning("Skipping result with missing metadata")
                continue

            # Guard: skip records with invalid embeddings (NaN distance)
            if distance != distance:  # NaN check (NaN != NaN is always True)
                logger.warning("Skipping result with NaN distance")
                continue

            score = round(1.0 - distance, 4)

            results.append(
                SearchResult(
                    content=text or meta.get("chunk_text_preview", ""),
                    source=meta.get("source_document_name", "unknown"),
                    page=int(meta.get("page_number", 0)),
                    score=score,
                )
            )

        # Sort descending by score — ChromaDB returns ascending distance,
        # which is equivalent, but explicit sorting is safer after filtering.
        results.sort(key=lambda r: r.score, reverse=True)
        return results
