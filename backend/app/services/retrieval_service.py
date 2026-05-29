from __future__ import annotations

from dataclasses import dataclass

from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    source_document: str
    page_number: int
    score: float


class RetrievalService:
    """
    Embeds a query and retrieves the top-k most relevant chunks from ChromaDB.

    Sits between the raw ChromaService and the RAG orchestrator — its only
    job is to return typed, ranked RetrievedChunk objects.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chroma_service: ChromaService,
        top_k: int = 5,
    ) -> None:
        self._embedder = embedding_service
        self._chroma = chroma_service
        self._top_k = top_k

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        """
        Embed query → ANN search → return ranked chunks.

        Returns empty list if collection is empty or query yields no results.

        Raises:
            ValueError: If query is blank.
            RuntimeError: If ChromaDB query fails.
        """
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty.")

        logger.info("Retrieving | query='%s' | top_k=%d", query, self._top_k)

        try:
            query_vector = self._embedder.embed_query(query)
            raw = self._chroma.query(query_embedding=query_vector, top_k=self._top_k)
        except Exception as exc:
            logger.error("ChromaDB query failed: %s", exc)
            raise RuntimeError(f"Vector store query failed: {exc}") from exc

        chunks = self._parse(raw)
        logger.info("Retrieved %d chunk(s)", len(chunks))
        return chunks

    @staticmethod
    def _parse(raw: dict) -> list[RetrievedChunk]:
        documents = raw["documents"][0]
        metadatas = raw["metadatas"][0]
        distances = raw["distances"][0]

        results: list[RetrievedChunk] = []
        for text, meta, dist in zip(documents, metadatas, distances):
            if not meta or dist != dist:  # skip missing meta or NaN distance
                continue
            results.append(
                RetrievedChunk(
                    text=text or meta.get("chunk_text_preview", ""),
                    source_document=meta.get("source_document_name", "unknown"),
                    page_number=int(meta.get("page_number", 0)),
                    score=round(1.0 - dist, 4),
                )
            )

        results.sort(key=lambda r: r.score, reverse=True)
        return results
