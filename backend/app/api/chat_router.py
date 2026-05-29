from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.chat_request import ChatRequest
from app.models.chat_response import ChatResponse
from app.services.rag_service import RAGService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])

# Singleton injected by main.py via set_rag_service()
_rag_service: RAGService | None = None


def set_rag_service(rag_service: RAGService) -> None:
    """Called once at startup by main.py to inject the RAGService singleton."""
    global _rag_service
    _rag_service = rag_service


def _get_rag_service() -> RAGService:
    if _rag_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAGService not initialised.",
        )
    return _rag_service


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="RAG Chat — Ask the Knowledge Base",
    description=(
        "Submit a natural-language question and receive a **grounded answer** "
        "with source citations, powered by Google Gemini.\n\n"
        "**Pipeline:**\n"
        "1. Embed question using `all-MiniLM-L6-v2`\n"
        "2. Retrieve top-5 semantically relevant chunks from ChromaDB\n"
        "3. Build a strict grounded prompt\n"
        "4. Call Gemini — answer is based **only** on retrieved context\n"
        "5. Return answer + deduplicated source citations\n\n"
        "**Example questions:**\n"
        "- *What is the annual leave policy?*\n"
        "- *How many sick leaves do employees get?*\n"
        "- *What is the notice period for resignation?*\n"
        "- *What are the WFH guidelines?*"
    ),
    responses={
        200: {"description": "Grounded answer with deduplicated source citations"},
        422: {"description": "Validation error — question is required and must not be blank"},
        500: {"description": "Retrieval or Gemini generation failure"},
        503: {"description": "Service not initialised — restart the server"},
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "Leave Policy": {
                            "summary": "Annual leave entitlement",
                            "value": {"question": "What is the annual leave policy?"},
                        },
                        "Sick Leave": {
                            "summary": "Sick leave allowance",
                            "value": {"question": "How many sick leaves do employees get?"},
                        },
                        "Resignation": {
                            "summary": "Notice period",
                            "value": {"question": "What is the notice period for resignation?"},
                        },
                        "WFH": {
                            "summary": "Work from home guidelines",
                            "value": {"question": "What are the WFH guidelines?"},
                        },
                        "Password Policy": {
                            "summary": "Password requirements",
                            "value": {"question": "What is the password policy?"},
                        },
                    }
                }
            }
        }
    },
)
async def chat(
    request: ChatRequest,
    rag_svc: RAGService = Depends(_get_rag_service),
) -> ChatResponse:
    """
    RAG chat endpoint.

    Full pipeline:
        1. Validate question (Pydantic + blank-string guard).
        2. Embed question → retrieve top-5 chunks from ChromaDB.
        3. Build grounded prompt → call Gemini → return answer + citations.

    Example request:
        POST /api/chat
        { "question": "What is the annual leave policy?" }

    Example response:
        {
            "answer": "Employees are entitled to 20 days of annual leave...",
            "sources": [{ "document": "Leave Policy", "page": 2 }]
        }
    """
    logger.info("POST /api/chat | question='%s'", request.question)

    try:
        response = rag_svc.answer(request.question)
    except RuntimeError as exc:
        logger.error("RAG pipeline failed | question='%s' | error=%s", request.question, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return response
