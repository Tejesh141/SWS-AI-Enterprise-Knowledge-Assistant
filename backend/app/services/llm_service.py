from __future__ import annotations

import requests

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
6. Mention relevant policy names when available."""

_MODELS_TO_TRY = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro",
]


class LLMService:
    """
    Calls Gemini via direct REST API.
    Supports both OAuth2 tokens (AQ. prefix) and API keys (AIza prefix).
    Auto-tries multiple models until one succeeds.
    """

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
        self._api_key = api_key
        self._is_oauth = api_key.startswith("AQ.")
        # Put configured model first in the list
        self._models = [model_name] + [m for m in _MODELS_TO_TRY if m != model_name]
        logger.info("LLMService ready | auth=%s", "oauth" if self._is_oauth else "apikey")

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            logger.warning("No context chunks — returning fallback")
            return FALLBACK

        prompt = self._build_prompt(question, chunks)
        last_error = None

        for model in self._models:
            try:
                answer = self._call(model, prompt)
                logger.info("Gemini OK | model=%s | length=%d", model, len(answer))
                return answer
            except Exception as exc:
                logger.warning("Model %s failed: %s", model, str(exc)[:120])
                last_error = exc

        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    def _call(self, model: str, prompt: str) -> str:
        model_id = model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

        headers = {"Content-Type": "application/json"}
        if self._is_oauth:
            headers["Authorization"] = f"Bearer {self._api_key}"
        else:
            url += f"?key={self._api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1024},
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)

        if not resp.ok:
            raise RuntimeError(f"{resp.status_code} {resp.text[:300]}")

        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected response: {data}") from exc

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
            f"{'-' * 60}\n"
            f"{context}\n"
            f"{'-' * 60}\n\n"
            f"QUESTION: {question}\n\n"
            "ANSWER (based strictly on the context above):"
        )
