from __future__ import annotations

import google.generativeai as genai

from app.services.retrieval_service import RetrievedChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

FALLBACK = "I don't have that information in the company documents."

_SYSTEM_PROMPT = """\
You are the official SWS AI Enterprise Knowledge Assistant.

Rules:
1. Answer ONLY using information explicitly present in the CONTEXT below.
2. Never use external knowledge, assumptions, or inferences.
3. Never hallucinate facts, names, dates, or policies.
4. If the answer cannot be found in the context, respond with exactly:
   "I don't have that information in the company documents."
5. Always provide concise and professional answers.
6. Mention relevant policy names when available.\
"""


class LLMService:
    """
    Builds a grounded RAG prompt and calls the Google Gemini API.

    Stateless after __init__ — safe for concurrent async requests.
    temperature=0 enforces deterministic, factual answers.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.GenerationConfig(
                temperature=0.0,
                max_output_tokens=1024,
            ),
        )
        logger.info("LLMService ready | model=%s", model_name)

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> str:
        """
        Generate a grounded answer from retrieved context chunks.

        Returns the fallback phrase immediately if no chunks were retrieved,
        saving an unnecessary API call.

        Raises:
            RuntimeError: If the Gemini API call fails.
        """
        if not chunks:
            logger.warning("No context chunks — returning fallback answer")
            return FALLBACK

        prompt = self._build_prompt(question, chunks)
        logger.info(
            "Calling Gemini | model=%s | chunks=%d | question='%s'",
            self._model.model_name, len(chunks), question,
        )

        try:
            response = self._model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise RuntimeError(f"Gemini generation failed: {exc}") from exc

        logger.info("Gemini response | length=%d chars", len(answer))
        return answer

    def _build_prompt(self, question: str, chunks: list[RetrievedChunk]) -> str:
        context_blocks = []
        for chunk in chunks:
            doc_name = (
                chunk.source_document
                .removesuffix(".pdf")
                .replace("_", " ")
                .replace("-", " ")
            )
            context_blocks.append(
                f"Document: {doc_name}\nPage: {chunk.page_number}\n\n{chunk.text}"
            )

        context = "\n\n---\n\n".join(context_blocks)

        return (
            f"{_SYSTEM_PROMPT}\n\n"
            f"{'─' * 60}\n"
            f"{context}\n"
            f"{'─' * 60}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER (based strictly on the context above):"
        )
