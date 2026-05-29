"""
api/chat.py
────────────
Responsibility (Single Responsibility Principle):
    Handle HTTP concerns for the POST /api/chat endpoint only.
    No business logic lives here — it delegates entirely to injected services.

Clean Architecture boundary:
    HTTP layer (this file)
        → RetrievalService   (vector search)
        → GeminiService      (LLM generation)
        → ChatResponse       (typed response contract)

FastAPI dependency injection is used to supply services, which means:
    - Services are created once at app startup (not per request)
    - This router is independently testable by injecting mock services
    - Adding auth, rate-limiting, or caching only requires changes here,
      not in the business logic services
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.document import ChatRequest, ChatResponse
from app.retrieval.retrieval_service import RetrievalService
from app.services.gemini_service import GeminiService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# APIRouter lets us mount this at any prefix in main.py without changing this file.
# tag="Chat" groups this endpoint cleanly in the auto-generated Swagger UI.
router = APIRouter(prefix="/api", tags=["Chat"])


# ── Dependency provider functions ──────────────────────────────────────────────
# These are called by FastAPI's DI system. The actual singleton instances are
# set by main.py via `chat.set_services(...)` before the app starts serving.
# This pattern avoids circular imports and keeps the router decoupled from
# the application wiring code in main.py.

_retrieval_service: Optional[RetrievalService] = None
_gemini_service: Optional[GeminiService] = None


def set_services(
    retrieval_service: RetrievalService,
    gemini_service: GeminiService,
) -> None:
    """
    Inject service singletons from main.py at startup.

    Called once during application startup (lifespan or module-level wiring).
    Using a setter instead of a global import prevents circular dependencies
    between main.py and this router module.

    Args:
        retrieval_service: Configured RetrievalService instance.
        gemini_service:    Configured GeminiService instance.
    """
    global _retrieval_service, _gemini_service
    _retrieval_service = retrieval_service
    _gemini_service = gemini_service


def _get_retrieval_service() -> RetrievalService:
    """FastAPI dependency: provides the RetrievalService singleton."""
    if _retrieval_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RetrievalService not initialised",
        )
    return _retrieval_service


def _get_gemini_service() -> GeminiService:
    """FastAPI dependency: provides the GeminiService singleton."""
    if _gemini_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GeminiService not initialised",
        )
    return _gemini_service


# ── Endpoint ───────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question against the enterprise knowledge base",
    responses={
        200: {"description": "Grounded answer with source citations"},
        422: {"description": "Validation error — question field is required"},
        500: {"description": "Internal server error during retrieval or generation"},
    },
)
async def chat(
    request: ChatRequest,
    retrieval_svc: RetrievalService = Depends(_get_retrieval_service),
    gemini_svc: GeminiService = Depends(_get_gemini_service),
) -> ChatResponse:
    """
    RAG chat endpoint — the core of the enterprise knowledge assistant.

    Full request lifecycle:
        1. FastAPI validates the request body against ChatRequest schema.
        2. RetrievalService embeds the question and fetches top-3 chunks
           from ChromaDB using approximate nearest-neighbour search.
        3. GeminiService builds a grounded prompt and calls the Gemini API.
        4. The answer and deduplicated source citations are returned.

    Request body:
        { "question": "What is the annual leave entitlement?" }

    Response body:
        {
            "answer": "Employees are entitled to 20 days of annual leave...",
            "sources": [
                { "document": "Leave Policy", "page": 3 }
            ]
        }

    Error handling:
        - Empty question     → 422 Unprocessable Entity (Pydantic validation)
        - Retrieval failure  → 500 with descriptive message
        - Gemini API failure → 500 with descriptive message
    """
    question = request.question.strip()

    # Pydantic validates presence of `question`, but we guard against blank strings
    # here because "   " passes Pydantic's str check but is semantically empty.
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question must not be empty or whitespace.",
        )

    logger.info("Chat request received | question='%s'", question)

    # ── Step 1: Retrieve relevant context chunks ───────────────────────
    try:
        context_chunks = retrieval_svc.retrieve(question)
    except Exception as exc:
        logger.error("Retrieval failed | question='%s' | error=%s", question, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context from knowledge base.",
        ) from exc

    logger.info(
        "Context retrieved | chunks=%d | question='%s'",
        len(context_chunks),
        question,
    )

    # ── Step 2: Generate grounded answer via Gemini ────────────────────
    try:
        response = gemini_svc.generate(
            question=question,
            context_chunks=context_chunks,
        )
    except RuntimeError as exc:
        logger.error("Gemini generation failed | question='%s' | error=%s", question, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer from language model.",
        ) from exc

    logger.info(
        "Chat response ready | sources=%d | answer_length=%d",
        len(response.sources),
        len(response.answer),
    )

    return response
