"""
main.py
────────
FastAPI application entry point.

Service wiring:
    All heavyweight services are instantiated ONCE at module load time
    and injected into routers — the embedding model is never reloaded
    per request, and a single ChromaDB connection is reused throughout.

Run from /backend:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE importing settings — settings reads env vars at import time
load_dotenv(Path(__file__).resolve().parent / ".env")

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api import chat_router
from app.config.settings import settings
from app.retrieval.retrieval_service import RetrievalService as LegacyRetrievalService
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Application ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SWS-AI Enterprise Knowledge Assistant",
    description="""
## Overview
A production-grade **Retrieval-Augmented Generation (RAG)** system that lets employees
query internal company documents using natural language and receive grounded, cited answers
powered by **Google Gemini**.

## RAG Pipeline
```
Question → Embed → ChromaDB ANN Search → Top-5 Chunks → Gemini Prompt → Answer + Citations
```

## Key Features
- 🔍 **Semantic Search** — sentence-transformers/all-MiniLM-L6-v2 (384-dim embeddings)
- 🧠 **Grounded Answers** — Gemini answers strictly from retrieved context, no hallucination
- 📄 **Source Citations** — every answer includes document name and page number
- ⚡ **Fast Retrieval** — ChromaDB HNSW index, sub-10ms ANN search
- 🏢 **Enterprise Ready** — structured logging, error handling, typed contracts

## Quick Start
1. Drop PDFs into `data/pdfs/`
2. `POST /ingest` to index documents
3. `POST /api/chat` to query the knowledge base
    """,
    version="3.0.0",
    contact={
        "name": "SWS-AI Engineering Team",
        "email": "engineering@sws-ai.com",
    },
    license_info={
        "name": "Proprietary — SWS AI Internal Use Only",
    },
    openapi_tags=[
        {
            "name": "Chat",
            "description": "RAG-powered chat endpoint. Submit a question and receive a grounded answer with source citations.",
        },
        {
            "name": "Ingestion",
            "description": "Document ingestion pipeline. Drop PDFs into `data/pdfs/` then trigger ingestion to index them into ChromaDB.",
        },
        {
            "name": "Retrieval",
            "description": "Low-level semantic retrieval. Returns raw chunks with similarity scores — useful for debugging and evaluation.",
        },
        {
            "name": "System",
            "description": "Health and liveness probes for monitoring and orchestration.",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared service singletons ──────────────────────────────────────────────────

_base_dir = Path(__file__).resolve().parent

_embedding_svc = EmbeddingService(model_name=settings.embedding_model)

_chroma_svc = ChromaService(
    db_dir=_base_dir / settings.chroma_db_dir,
    embedding_service=_embedding_svc,
    collection_name=settings.chroma_collection_name,
)

# ── RAG pipeline services (new) ────────────────────────────────────────────────

_retrieval_svc = RetrievalService(
    embedding_service=_embedding_svc,
    chroma_service=_chroma_svc,
    top_k=5,
)

_llm_svc = LLMService(
    api_key=settings.gemini_api_key,
    model_name=settings.gemini_model,
)

_rag_svc = RAGService(
    retrieval_service=_retrieval_svc,
    llm_service=_llm_svc,
)

chat_router.set_rag_service(_rag_svc)

# ── Legacy retrieval service (kept for /retrieve endpoint) ────────────────────

_legacy_retrieval_svc = LegacyRetrievalService(
    embedding_service=_embedding_svc,
    chroma_service=_chroma_svc,
    top_k=settings.top_k,
    similarity_threshold=settings.similarity_threshold,
)

# ── Mount routers ──────────────────────────────────────────────────────────────

app.include_router(chat_router.router)

# ── Inline schemas ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        example="What is the annual leave policy?",
        description="Natural-language search query",
    )
    top_k: Optional[int] = Field(
        default=None,
        example=5,
        description="Number of chunks to retrieve (overrides server default of 5)",
    )


class HealthResponse(BaseModel):
    status: str = Field(example="ok")
    version: str = Field(example="3.0.0")
    collection: str = Field(example="sws_ai_knowledge_base")
    vectors: int = Field(example=128)
    documents: int = Field(example=4)


class IngestionResponse(BaseModel):
    status: str = Field(example="success")
    message: str = Field(example="Ingestion complete")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["System"],
    response_model=HealthResponse,
    summary="Health Check",
    description=(
        "Returns API liveness status and ChromaDB collection statistics. "
        "Use as a readiness/liveness probe in container orchestration."
    ),
)
async def health_check() -> HealthResponse:
    stats = _chroma_svc.get_stats()
    return HealthResponse(
        status="ok",
        version="3.0.0",
        collection=stats.collection_name,
        vectors=stats.total_vectors,
        documents=stats.unique_documents,
    )


@app.post(
    "/ingest",
    tags=["Ingestion"],
    response_model=IngestionResponse,
    summary="Trigger Document Ingestion",
    description=(
        "Runs the full ingestion pipeline: **PDF → chunks → embeddings → ChromaDB**. "
        "Drop PDF files into `data/pdfs/` before calling this endpoint. "
        "Re-ingesting an existing document overwrites stale vectors (idempotent)."
    ),
    responses={
        200: {"description": "Ingestion completed successfully"},
        500: {"description": "Ingestion failed — check server logs for details"},
    },
)
async def trigger_ingestion() -> JSONResponse:
    from scripts.ingest_documents import run_ingestion_pipeline
    try:
        run_ingestion_pipeline()
        return JSONResponse({"status": "success", "message": "Ingestion complete"})
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@app.post(
    "/retrieve",
    tags=["Retrieval"],
    summary="Semantic Chunk Retrieval",
    description=(
        "Embeds the query and returns the top-k most semantically similar chunks "
        "from ChromaDB with **cosine similarity scores**. "
        "Intended for debugging and pipeline evaluation — use `POST /api/chat` for end-user queries."
    ),
    responses={
        200: {"description": "Ranked list of chunks with similarity scores"},
        422: {"description": "Empty or invalid query"},
        500: {"description": "Internal retrieval error"},
    },
)
async def retrieve(request: QueryRequest) -> JSONResponse:
    try:
        svc = _legacy_retrieval_svc
        if request.top_k is not None:
            svc = LegacyRetrievalService(
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
