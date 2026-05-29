"""
services/embedding_service.py
──────────────────────────────
Responsibility (Single Responsibility Principle):
    Convert DocumentChunk text into dense vector embeddings.

Why sentence-transformers/all-MiniLM-L6-v2?
- 384-dimensional embeddings — compact yet highly accurate for semantic search
- Runs fully locally (no API key, no cost, no latency to external service)
- Best-in-class speed/quality trade-off for enterprise RAG pipelines

Design:
- Model is loaded ONCE at construction time (expensive operation)
- `embed_chunks` accepts a batch for efficiency (GPU/CPU parallelism)
- Returns EmbeddedChunk objects ready for ChromaDB insertion
"""

from sentence_transformers import SentenceTransformer

from app.models.document import DocumentChunk, EmbeddedChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """
    Wraps a SentenceTransformer model and produces EmbeddedChunk objects.

    Usage:
        service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2")
        embedded = service.embed_chunks(chunks)
    """

    def __init__(self, model_name: str) -> None:
        """
        Load the embedding model from HuggingFace Hub (cached locally after first run).

        Args:
            model_name: HuggingFace model identifier.
        """
        logger.info("Loading embedding model: %s", model_name)
        # SentenceTransformer handles device selection (CPU/GPU) automatically
        self._model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    # ── Public API ─────────────────────────────────────────────────────

    def embed_chunks(self, chunks: list[DocumentChunk]) -> list[EmbeddedChunk]:
        """
        Embed a batch of DocumentChunks.

        Batching all texts in one `encode()` call is significantly faster
        than encoding one chunk at a time because the model can parallelise
        across the batch dimension.

        Args:
            chunks: List of DocumentChunk objects to embed.

        Returns:
            List of EmbeddedChunk objects with populated `embedding` field.
        """
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]

        logger.info("Generating embeddings for %d chunk(s)...", len(texts))

        # show_progress_bar=False keeps logs clean in production pipelines
        vectors = self._model.encode(
            texts,
            batch_size=64,          # Tune based on available RAM/VRAM
            show_progress_bar=False,
            convert_to_numpy=True,  # numpy arrays are faster to convert to list
        )

        embedded_chunks = [
            EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                file_name=chunk.file_name,
                page_number=chunk.page_number,
                text=chunk.text,
                embedding=vector.tolist(),  # ChromaDB expects plain Python list[float]
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        logger.info("Embeddings generated: %d vector(s)", len(embedded_chunks))
        return embedded_chunks
