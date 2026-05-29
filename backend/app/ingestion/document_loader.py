"""
ingestion/document_loader.py
─────────────────────────────
Responsibility (Single Responsibility Principle):
    Load PDF files from disk and extract raw text page-by-page.

This module ONLY handles I/O and text extraction.
It does NOT chunk, embed, or store anything.

Key design decisions:
- Generator pattern (`yield`) keeps memory usage flat for large PDF sets
- Per-file error handling ensures one bad PDF never kills the whole pipeline
- PyMuPDF (fitz) is used because it is the fastest pure-Python PDF parser
  and handles malformed PDFs more gracefully than pdfplumber/pypdf
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import fitz  # PyMuPDF

from app.models.document import RawDocument
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """
    Scans a directory for PDF files and yields RawDocument objects
    (one per page) for downstream processing.

    Usage:
        loader = DocumentLoader(pdf_dir=Path("data/pdfs"))
        for raw_doc in loader.load():
            process(raw_doc)
    """

    def __init__(self, pdf_dir: Path) -> None:
        """
        Args:
            pdf_dir: Directory that contains the PDF files to ingest.
        """
        self.pdf_dir = pdf_dir

    # ── Public API ─────────────────────────────────────────────────────

    def load(self) -> Generator[RawDocument, None, None]:
        """
        Discover all PDFs in `pdf_dir` and yield one RawDocument per page.

        Yields:
            RawDocument for each non-empty page across all PDFs.
        """
        pdf_files = list(self.pdf_dir.glob("*.pdf"))

        if not pdf_files:
            logger.warning("No PDF files found in '%s'", self.pdf_dir)
            return

        logger.info("Found %d PDF file(s) to process", len(pdf_files))

        for pdf_path in pdf_files:
            yield from self._extract_pages(pdf_path)

    # ── Private helpers ────────────────────────────────────────────────

    def _extract_pages(self, pdf_path: Path) -> Generator[RawDocument, None, None]:
        """
        Open a single PDF and yield one RawDocument per page.

        Handles:
        - Corrupted / unreadable PDFs  → logs error, skips file
        - Empty PDFs (0 pages)         → logs warning, skips file
        - Pages with no extractable text → skips page silently
        """
        file_name = pdf_path.name

        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            # Corrupted or password-protected PDF — skip gracefully
            logger.error("Failed to open '%s': %s", file_name, exc)
            return

        total_pages = len(doc)

        if total_pages == 0:
            logger.warning("'%s' has 0 pages — skipping", file_name)
            doc.close()
            return

        logger.info("Processing '%s' (%d pages)", file_name, total_pages)
        pages_extracted = 0

        for page_index in range(total_pages):
            page = doc[page_index]
            text = page.get_text("text").strip()  # "text" mode = plain UTF-8

            if not text:
                # Scanned image page with no OCR layer — skip
                continue

            pages_extracted += 1
            yield RawDocument(
                file_name=file_name,
                page_number=page_index + 1,   # Convert to 1-based
                text=text,
                total_pages=total_pages,
            )

        doc.close()
        logger.info(
            "'%s' → %d/%d pages extracted", file_name, pages_extracted, total_pages
        )
