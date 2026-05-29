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

from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="SWS-AI Enterprise Knowledge Assistant",
    description="Phase 1 — Document Ingestion Pipeline",
    version="1.0.0",
)


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """Liveness probe — confirms the API is running."""
    return JSONResponse({"status": "ok", "phase": "1 — Ingestion Pipeline"})


@app.post("/ingest", tags=["Ingestion"])
async def trigger_ingestion() -> JSONResponse:
    """
    Trigger the document ingestion pipeline programmatically.

    In production this would be called by a scheduler or event trigger
    (e.g. S3 upload event via Lambda → API Gateway → this endpoint).
    """
    from scripts.ingest_documents import run_ingestion_pipeline  # lazy import

    try:
        run_ingestion_pipeline()
        return JSONResponse({"status": "success", "message": "Ingestion complete"})
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
