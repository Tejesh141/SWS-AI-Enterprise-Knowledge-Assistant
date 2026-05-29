"""
retrieval/retrieval_service.py
───────────────────────────────
Responsibility (Single Responsibility Principle):
    Accept a natural-language query, find the most semantically relevant
    chunks in the knowledge base, and return structured results.

Where this sits in the RAG architecture:
    User query
        → RetrievalService.retrieve()   ← THIS FILE
            → EmbeddingService          (encode query → vector)
            → ChromaService.query()     (ANN search → raw results)
            → _build_results()          (raw → typed RetrievalResult list)
        → [Phase 2] LLM prompt builder  (inject chunks as context)
        → [Phase 2] LLM response        (grounded answer)

Design decisions:
- RetrievalService depends on ABSTRACTIONS (EmbeddingService, ChromaService)
  injected via __init__, not created internally → Dependency Inversion Principle.
  This makes the class trivially unit-testable with mocks.

- Similarity score conversion:
    ChromaDB cosine space stores  distance = 1 - cosine_similarity
    So:  similarity_score = 1 - distance
    Score of 1.0 = identical vectors, 0.0 = orthogonal (completely unrelated).

- similarity_threshold filters out noise: results below the threshold are
  dropped before returning, preventing the LLM from being fed irrelevant context.

- All logging uses structured key=value style for easy parsing by log aggregators
  (CloudWatch, Datadog, ELK, etc.).
"""

from __future__ import annotations

from app.models.document import RetrievalResult
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetrievalService:
    """
    Orchestrates the full query → embed → search → rank pipeline.

    This class owns NO model weights and NO database connections directly.
    It coordinates EmbeddingService and ChromaService, which are injected
    at construction time (Dependency Injection pattern).

    Usage:
        retrieval = RetrievalService(
            embedding_service=EmbeddingService(model_name=...),
            chroma_service=ChromaService(db_dir=..., collection_name=...),
            top_k=3,
            similarity_threshold=0.0,
        )
        results = retrieval.retrieve("What is the refund policy?")
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chroma_service: ChromaService,
        top_k: int = 3,
        similarity_threshold: float = 0.0,
    ) -> None:
        """
        Args:
            embedding_service:    Encodes text queries into dense vectors.
            chroma_service:       Executes ANN search against the vector store.
            top_k:                Maximum number of results to return.
            similarity_threshold: Minimum cosine similarity [0.0–1.0] to include
                                  a result. Raise this (e.g. 0.4) to filter weak
                                  matches; keep at 0.0 to always return top_k.
        """
        self._embedder   = embedding_service
        self._chroma     = chroma_service
        self._top_k      = top_k
        self._threshold  = similarity_threshold

    # ── Public API ─────────────────────────────────────────────────────

    def retrieve(self, query: str) -> list[RetrievalResult]:
        """
        Find the top-k most semantically relevant chunks for a user query.

        Steps:
            1. Validate the query is non-empty.
            2. Embed the query using the same model used during ingestion.
               (Critical: query and document embeddings MUST share the same
                model and tokeniser, otherwise similarity scores are meaningless.)
            3. Run approximate nearest-neighbour (ANN) search in ChromaDB.
            4. Convert raw distances → similarity scores.
            5. Filter by similarity_threshold.
            6. Return as a list of typed RetrievalResult objects, ranked by
               descending similarity (most relevant first).

        Args:
            query: Natural-language question or search phrase from the user.

        Returns:
            List of RetrievalResult objects (may be empty if nothing passes
            the threshold or the collection is empty).

        Raises:
            ValueError: If query is blank.
        """
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty")

        logger.info("Retrieval request | query='%s' | top_k=%d", query, self._top_k)

        # ── Step 1: Embed the query ────────────────────────────────────
        # encode() on a single string returns a 1-D numpy array.
        # We reuse EmbeddingService's loaded model via a dedicated method
        # rather than calling embed_chunks() (which expects DocumentChunk objects).
        query_vector: list[float] = self._embedder.embed_query(query)

        # ── Step 2: ANN search in ChromaDB ────────────────────────────
        raw = self._chroma.query(
            query_embedding=query_vector,
            top_k=self._top_k,
        )

        # ── Step 3: Build typed results ────────────────────────────────
        results = self._build_results(raw)

        logger.info(
            "Retrieval complete | returned=%d | threshold=%.2f",
            len(results),
            self._threshold,
        )
        return results

    # ── Private helpers ────────────────────────────────────────────────

    def _build_results(self, raw: dict) -> list[RetrievalResult]:
        """
        Convert the raw ChromaDB query response into RetrievalResult objects.

        ChromaDB query() returns parallel lists nested under a single-query
        batch wrapper, so we index [0] to unwrap the outer batch dimension:
            raw["documents"][0]  → list of chunk texts
            raw["metadatas"][0]  → list of metadata dicts
            raw["distances"][0]  → list of cosine distances

        Distance → similarity conversion:
            ChromaDB cosine space: distance ∈ [0, 2]
            Normalised similarity: score = 1 - distance
            Practical range with sentence-transformers: score ∈ [0.0, 1.0]

        Args:
            raw: Direct return value from ChromaService.query().

        Returns:
            Filtered, sorted list of RetrievalResult (best match first).
        """
        documents  = raw["documents"][0]   # list[str]
        metadatas  = raw["metadatas"][0]   # list[dict]
        distances  = raw["distances"][0]   # list[float]

        results: list[RetrievalResult] = []

        for text, meta, distance in zip(documents, metadatas, distances):
            # Convert cosine distance → similarity score
            similarity_score = round(1.0 - distance, 4)

            # Drop results that don't meet the minimum quality bar
            if similarity_score < self._threshold:
                logger.debug(
                    "Filtered out chunk '%s' | score=%.4f < threshold=%.2f",
                    meta.get("chunk_id", "unknown"),
                    similarity_score,
                    self._threshold,
                )
                continue

            results.append(
                RetrievalResult(
                    chunk_text=text,
                    similarity_score=similarity_score,
                    source_document=meta["source_document_name"],
                    page_number=meta["page_number"],
                )
            )

            logger.debug(
                "Result | source='%s' | page=%d | score=%.4f | preview='%s...'",
                meta["source_document_name"],
                meta["page_number"],
                similarity_score,
                text[:60].replace("\n", " "),
            )

        # Results come pre-sorted by ChromaDB (ascending distance = descending similarity)
        # but we sort explicitly to guarantee order after threshold filtering
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results
