"""
services/gemini_service.py
───────────────────────────
Responsibility (Single Responsibility Principle):
    Build a grounded RAG prompt from retrieved context chunks and call
    the Google Gemini API to generate a factual, citation-safe answer.

Where this sits in the RAG architecture:
    RetrievalService.retrieve()  →  list[RetrievalResult]
        → GeminiService.generate()          ← THIS FILE
            → _build_prompt()               (assemble system + context + question)
            → Gemini API call               (generate grounded answer)
        → ChatResponse                      (answer + sources)

Prompt engineering strategy:
    The system instruction enforces three hard rules:
        1. Answer ONLY from the provided context — no world knowledge
        2. Never fabricate or infer beyond what is explicitly stated
        3. If the answer is absent, return the exact fallback phrase

    This is the standard "grounded RAG" pattern used in enterprise
    document Q&A systems to prevent hallucination and ensure auditability.

Design decisions:
    - GeminiService is stateless after __init__; each generate() call is
      independent, making it safe for concurrent async requests.
    - The model is configured with temperature=0 to maximise determinism.
      For creative tasks you would raise this; for factual Q&A, 0 is correct.
    - Source deduplication happens here (not in the router) because it is
      business logic, not HTTP concerns.
"""

from __future__ import annotations

import google.generativeai as genai

from app.models.document import ChatResponse, RetrievalResult, SourceReference
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Exact phrase returned when the answer is not found in the knowledge base.
# Defined as a constant so it can be asserted in unit tests without magic strings.
FALLBACK_ANSWER = "I don't have that information in the company documents."


class GeminiService:
    """
    Wraps the Google Gemini generative model for grounded RAG responses.

    Usage:
        svc = GeminiService(api_key="...", model_name="gemini-1.5-flash")
        response = svc.generate(question="...", context_chunks=[...])
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        """
        Configure the Gemini SDK and instantiate the generative model.

        Args:
            api_key:    Google AI Studio API key (from .env / settings).
            model_name: Gemini model identifier, e.g. "gemini-1.5-flash".

        Raises:
            ValueError: If api_key is empty — fail fast at startup, not at
                        request time, so misconfiguration is caught immediately.
        """
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )

        genai.configure(api_key=api_key)

        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=0.0,
                max_output_tokens=2048,
            ),
        )

        logger.info("GeminiService ready | model=%s", model_name)

    # ── Public API ─────────────────────────────────────────────────────

    def generate(
        self,
        question: str,
        context_chunks: list[RetrievalResult],
    ) -> ChatResponse:
        """
        Generate a grounded answer for the user's question.

        Steps:
            1. If no context chunks were retrieved, return the fallback answer
               immediately — no LLM call needed (saves latency + API cost).
            2. Build the full prompt (system instruction + numbered context + question).
            3. Call Gemini and extract the text response.
            4. Deduplicate and format source citations.
            5. Return a typed ChatResponse.

        Args:
            question:       The user's natural-language question.
            context_chunks: Top-k RetrievalResult objects from RetrievalService.

        Returns:
            ChatResponse with `answer` and `sources`.
        """
        # ── Guard: empty knowledge base or no relevant chunks ──────────
        if not context_chunks:
            logger.warning("No context chunks available — returning fallback answer")
            return ChatResponse(answer=FALLBACK_ANSWER, sources=[])

        # ── Build prompt ───────────────────────────────────────────────
        prompt = self._build_prompt(question, context_chunks)
        logger.info(
            "Calling Gemini | model=%s | context_chunks=%d | question='%s'",
            self._model.model_name,
            len(context_chunks),
            question,
        )

        # ── Call Gemini API ────────────────────────────────────────────
        try:
            response = self._model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as exc:
            # Surface the error clearly rather than returning a silent empty answer
            logger.error("Gemini API call failed: %s", exc)
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

        logger.info("Gemini response received | answer_length=%d chars", len(answer))

        # ── Build deduplicated source citations ────────────────────────
        sources = self._build_sources(context_chunks)

        return ChatResponse(answer=answer, sources=sources)

    # ── Private helpers ────────────────────────────────────────────────

    def _build_prompt(
        self,
        question: str,
        context_chunks: list[RetrievalResult],
    ) -> str:
        """
        Assemble the full prompt sent to Gemini.

        Prompt structure:
            [SYSTEM INSTRUCTION]   — hard rules for the model
            [CONTEXT BLOCK]        — numbered retrieved passages with source labels
            [QUESTION]             — the user's question
            [INSTRUCTION]          — final reminder to stay grounded

        The numbered context format (CONTEXT 1, CONTEXT 2 ...) makes it easy
        to extend this prompt to ask Gemini to cite which context it used,
        which is a common enterprise requirement for auditability.

        Args:
            question:       User's question string.
            context_chunks: Retrieved chunks, ordered by descending similarity.

        Returns:
            Complete prompt string ready to send to Gemini.
        """
        # ── System instruction block ───────────────────────────────────
        system_instruction = (
            "You are an enterprise knowledge assistant. "
            "Your job is to answer employee questions strictly based on the "
            "company documents provided below.\n\n"
            "RULES — you must follow these without exception:\n"
            "1. Answer ONLY using information explicitly present in the CONTEXT below.\n"
            "2. Do NOT use any external knowledge, assumptions, or inferences.\n"
            "3. Do NOT hallucinate facts, names, dates, or policies.\n"
            f'4. If the answer cannot be found in the context, respond with exactly:\n'
            f'   "{FALLBACK_ANSWER}"\n'
            "5. Provide a COMPLETE and DETAILED answer — do not truncate or summarise prematurely.\n"
            "6. Format your answer using Markdown: use **bold** for key terms, "
            "bullet points (- item) for lists, and numbered lists (1. item) for steps or ordered items.\n"
            "7. Cover ALL relevant details present in the context for the question asked.\n"
        )

        # ── Context block ──────────────────────────────────────────────
        # Each chunk is labelled with its source file and page number so the
        # model can (optionally) reference them in its answer.
        context_lines = []
        for i, chunk in enumerate(context_chunks, start=1):
            source_label = (
                f"[Source: {chunk.source_document}, Page {chunk.page_number}]"
            )
            context_lines.append(
                f"CONTEXT {i} {source_label}:\n{chunk.chunk_text}"
            )

        context_block = "\n\n".join(context_lines)

        # ── Assemble final prompt ──────────────────────────────────────
        prompt = (
            f"{system_instruction}\n"
            f"{'─' * 60}\n"
            f"{context_block}\n"
            f"{'─' * 60}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER (based strictly on the context above):"
        )

        return prompt

    @staticmethod
    def _build_sources(chunks: list[RetrievalResult]) -> list[SourceReference]:
        """
        Convert RetrievalResult objects into deduplicated SourceReference citations.

        Deduplication key: (document_name, page_number)
        — The same page can appear in multiple chunks (due to overlap), so we
          deduplicate to avoid showing the same citation twice in the UI.

        Document name formatting:
            "Leave_Policy.pdf"  →  "Leave Policy"
            Strips .pdf extension and replaces underscores with spaces for
            clean display in the frontend.

        Args:
            chunks: Retrieved chunks from RetrievalService.

        Returns:
            Ordered, deduplicated list of SourceReference objects.
            Order matches the original chunk ranking (best match first).
        """
        seen: set[tuple[str, int]] = set()
        sources: list[SourceReference] = []

        for chunk in chunks:
            # Format: strip extension, replace underscores/hyphens with spaces
            display_name = (
                chunk.source_document
                .removesuffix(".pdf")
                .replace("_", " ")
                .replace("-", " ")
            )
            key = (display_name, chunk.page_number)

            if key not in seen:
                seen.add(key)
                sources.append(
                    SourceReference(document=display_name, page=chunk.page_number)
                )

        return sources
