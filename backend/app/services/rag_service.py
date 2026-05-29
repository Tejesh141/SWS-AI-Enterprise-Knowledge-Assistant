from __future__ import annotations

from app.models.chat_response import ChatResponse, SourceReference
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Orchestrates the full RAG pipeline:
        question → retrieve chunks → build context → call LLM → return response

    This class owns no model weights or DB connections — it coordinates
    RetrievalService and LLMService, both injected at construction time.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ) -> None:
        self._retriever = retrieval_service
        self._llm = llm_service

    def answer(self, question: str) -> ChatResponse:
        """
        Run the full RAG pipeline for a user question.

        Steps:
            1. Retrieve top-5 semantically relevant chunks from ChromaDB.
            2. Pass chunks + question to Gemini for grounded answer generation.
            3. Deduplicate source citations and return typed ChatResponse.

        Raises:
            RuntimeError: Propagated from RetrievalService or LLMService on failure.
        """
        logger.info("RAG pipeline start | question='%s'", question)

        # Step 1 — Retrieve
        chunks = self._retriever.retrieve(question)
        logger.info("RAG pipeline | retrieved=%d chunks", len(chunks))

        # Step 2 — Generate
        answer_text = self._llm.generate(question=question, chunks=chunks)

        # Step 3 — Build deduplicated sources
        sources = self._build_sources(chunks)

        logger.info(
            "RAG pipeline complete | sources=%d | answer_length=%d",
            len(sources), len(answer_text),
        )
        return ChatResponse(answer=answer_text, sources=sources)

    @staticmethod
    def _build_sources(chunks) -> list[SourceReference]:
        seen: set[tuple[str, int]] = set()
        sources: list[SourceReference] = []

        for chunk in chunks:
            display = (
                chunk.source_document
                .removesuffix(".pdf")
                .replace("_", " ")
                .replace("-", " ")
            )
            key = (display, chunk.page_number)
            if key not in seen:
                seen.add(key)
                sources.append(SourceReference(document=display, page=chunk.page_number))

        return sources
