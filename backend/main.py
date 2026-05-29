"""
main.py
────────
FastAPI application entry point for Phase 1.

Phase 1 exposes a single health-check endpoint and an ingestion trigger
endpoint. The full retrieval/chat API will be added in Phase 2.

Run from /backend:
    uvicorn main:app --reload --port 8000
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config.settings import settings
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.retrieval.retrieval_service import RetrievalService
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="SWS-AI Enterprise Knowledge Assistant",
    description="Phase 1 — Document Ingestion Pipeline | Phase 2 — Retrieval Layer",
    version="1.1.0",
)

# ── Shared service instances (initialised once at startup) ─────────────────────
# These are module-level singletons. In a larger app, use FastAPI lifespan events
# or a dependency injection container (e.g. dependency-injector library).
_base_dir       = Path(__file__).resolve().parent
_embedding_svc  = EmbeddingService(model_name=settings.embedding_model)
_chroma_svc     = ChromaService(
    db_dir=_base_dir / settings.chroma_db_dir,
    collection_name=settings.chroma_collection_name,
)
_retrieval_svc  = RetrievalService(
    embedding_service=_embedding_svc,
    chroma_service=_chroma_svc,
    top_k=settings.top_k,
    similarity_threshold=settings.similarity_threshold,
)


# ── Request / Response schemas ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None   # Optional per-request override of the default top_k


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """Liveness probe — confirms the API is running."""
    return JSONResponse({"status": "ok", "version": "1.1.0"})


@app.post("/ingest", tags=["Ingestion"])
async def trigger_ingestion() -> JSONResponse:
    """
    Trigger the document ingestion pipeline programmatically.
    Drop PDFs into data/pdfs/ then call this endpoint.
    """
    from scripts.ingest_documents import run_ingestion_pipeline
    try:
        run_ingestion_pipeline()
        return JSONResponse({"status": "success", "message": "Ingestion complete"})
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@app.post("/retrieve", tags=["Retrieval"])
async def retrieve(request: QueryRequest) -> JSONResponse:
    """
    Retrieve the top-k most relevant chunks for a natural-language query.

    Request body:
        { "query": "What is the refund policy?", "top_k": 3 }

    Response:
        [
          {
            "chunk_text":       "...",
            "similarity_score": 0.87,
            "source_document":  "policy_v2.pdf",
            "page_number":      4
          },
          ...
        ]
    """
    try:
        # Allow per-request top_k override; fall back to service default
        svc = _retrieval_svc
        if request.top_k is not None:
            svc = RetrievalService(
                embedding_service=_embedding_svc,
                chroma_service=_chroma_svc,
                top_k=request.top_k,
                similarity_threshold=settings.similarity_threshold,
            )

        results = svc.retrieve(request.query)
        return JSONResponse([r.model_dump() for r in results])

    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception as exc:
        logger.error("Retrieval failed: %s", exc)
        return JSONResponse({"error": "Internal retrieval error"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
