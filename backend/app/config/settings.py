"""
config/settings.py
──────────────────
Single source of truth for all application configuration.

Design:
- Loads values from .env via python-dotenv
- Exposes a singleton `settings` object imported across the app
- Using dataclass-style Pydantic BaseSettings keeps validation free
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings  # pydantic v2 split package


class Settings(BaseSettings):
    # ── Directory paths ────────────────────────────────────────────────
    pdf_dir: Path = Field(default="data/pdfs")
    processed_dir: Path = Field(default="data/processed")
    chroma_db_dir: Path = Field(default="data/chroma_db")

    # ── ChromaDB ───────────────────────────────────────────────────────
    chroma_collection_name: str = Field(default="sws_ai_knowledge_base")

    # ── Embedding ──────────────────────────────────────────────────────
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    # ── Chunking ───────────────────────────────────────────────────────
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)

    # ── Retrieval ──────────────────────────────────────────────────────
    top_k: int = Field(default=3)                    # Number of chunks to retrieve
    similarity_threshold: float = Field(default=0.0) # Minimum score to include a result

    # ── Gemini LLM ────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")

    # ── Logging ────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Module-level singleton — import this everywhere
settings = Settings()
