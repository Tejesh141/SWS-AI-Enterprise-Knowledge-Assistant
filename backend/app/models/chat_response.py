from __future__ import annotations

from pydantic import BaseModel


class SourceReference(BaseModel):
    document: str
    page: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
