"""
main.py
────────
FastAPI application entry point.

Phases implemented:
    Phase 1 — Document Ingestion Pipeline  (POST /ingest)
    Phase 2 — Retrieval Layer              (POST /retrieve)
    Phase 3 — Chat API                     (POST /api/chat)  ← new

Service wiring strategy:
    All heavyweight services (embedding model, ChromaDB client, Gemini client)
    are instantiated ONCE here at module load time and injected into routers.
    This ensures:
    - The embedding model is not reloaded on every request (critical for latency)
    - A single ChromaDB connection is reused across all requests
    - Startup failures are caught immediately, not on the first request

Run from /backend:
    uvicorn main:app --reload --port 8000
"""

from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE importing settings — settings reads env vars at import time
load_dotenv(Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api import chat as chat_router
from app.config.settings import settings
from app.retrieval.retrieval_service import RetrievalService
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SWS-AI Enterprise Knowledge Assistant",
    description=(
        "Production RAG system — "
        "Phase 1: Ingestion | Phase 2: Retrieval | Phase 3: Chat API"
    ),
    version="2.0.0",
)

# ── Service singletons (initialised once at startup) ───────────────────────────

_base_dir = Path(__file__).resolve().parent

# 1. Embedding model — loaded from HuggingFace cache (~80 MB, ~2s on first run)
_embedding_svc = EmbeddingService(model_name=settings.embedding_model)

# 2. ChromaDB — connects to the persisted local vector store
_chroma_svc = ChromaService(
    db_dir=_base_dir / settings.chroma_db_dir,
    embedding_service=_embedding_svc,
    collection_name=settings.chroma_collection_name,
)

# 3. Retrieval — wires embedding + chroma, no additional resources
_retrieval_svc = RetrievalService(
    embedding_service=_embedding_svc,
    chroma_service=_chroma_svc,
    top_k=settings.top_k,
    similarity_threshold=settings.similarity_threshold,
)

# 4. Gemini — authenticates with Google AI Studio API key
_gemini_svc = GeminiService(
    api_key=settings.gemini_api_key,
    model_name=settings.gemini_model,
)

# Inject singletons into the chat router via its setter function.
# This avoids circular imports (chat.py does not import main.py).
chat_router.set_services(
    retrieval_service=_retrieval_svc,
    gemini_service=_gemini_svc,
)

# ── Mount routers ──────────────────────────────────────────────────────────────

app.include_router(chat_router.router)

# ── Inline schemas for legacy endpoints ───────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """Liveness probe — confirms the API is running."""
    return JSONResponse({"status": "ok", "version": "2.0.0"})


@app.post("/ingest", tags=["Ingestion"])
async def trigger_ingestion() -> JSONResponse:
    """
    Trigger the document ingestion pipeline.
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
    Low-level retrieval endpoint — returns raw chunks with similarity scores.
    Used for debugging and evaluation; the /api/chat endpoint is for end users.
    """
    try:
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
