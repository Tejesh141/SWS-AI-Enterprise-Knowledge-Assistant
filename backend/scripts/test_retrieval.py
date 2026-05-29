"""
scripts/test_retrieval.py
──────────────────────────
Standalone script to validate the full retrieval pipeline end-to-end.

What this tests:
    1. ChromaDB connection and collection load
    2. Query embedding generation
    3. Similarity search against ingested documents
    4. Result formatting and score display

Prerequisites:
    - Run `python scripts/ingest_documents.py` first to populate the collection
    - At least one PDF must be ingested (e.g. a Leave Policy document)

Run from /backend:
    python scripts/test_retrieval.py

Expected output (if Leave Policy PDF is ingested):
    ════════════════════════════════════════════════════════════
    SWS-AI Enterprise Knowledge Assistant — Retrieval Test
    ════════════════════════════════════════════════════════════
    Query : "What is the leave policy?"
    Top-K : 3
    ────────────────────────────────────────────────────────────
    Result #1
      Score    : 0.8742
      Source   : Leave_Policy.pdf
      Page     : 2
      Content  : Employees are entitled to 20 days of annual leave...
    ...
    ════════════════════════════════════════════════════════════
    Test PASSED — 3 result(s) retrieved
    ════════════════════════════════════════════════════════════
"""

import sys
from pathlib import Path

# ── Ensure /backend is on sys.path ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.config.settings import settings
from app.services.chroma_service import ChromaService
from app.services.embedding_service import EmbeddingService
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Test configuration ─────────────────────────────────────────────────────────
# Modify TEST_QUERIES to add more test cases. Each entry is a (query, description)
# tuple so the output clearly labels what each query is testing.
TEST_QUERIES: list[tuple[str, str]] = [
    ("What is the leave policy?",          "Primary test — leave entitlement"),
    ("How many days of annual leave?",     "Synonym variation test"),
    ("sick leave rules and regulations",   "Topic variation test"),
]

TOP_K = 3   # Number of results to retrieve per query


def _separator(char: str = "═", width: int = 60) -> str:
    return char * width


def run_retrieval_test() -> None:
    """
    Execute all test queries and print detailed results to stdout.

    Exit codes:
        0 — all queries returned at least one result
        1 — collection is empty (ingestion pipeline has not been run)
        2 — one or more queries returned zero results (possible data issue)
    """
    print(_separator())
    print("SWS-AI Enterprise Knowledge Assistant — Retrieval Test")
    print(_separator())

    base_dir   = Path(__file__).resolve().parents[1]
    chroma_dir = base_dir / settings.chroma_db_dir

    # ── Initialise services ────────────────────────────────────────────
    logger.info("Loading embedding model: %s", settings.embedding_model)
    embedder = EmbeddingService(model_name=settings.embedding_model)

    chroma = ChromaService(
        db_dir=chroma_dir,
        embedding_service=embedder,
        collection_name=settings.chroma_collection_name,
    )

    # ── Pre-flight: check collection is not empty ──────────────────────
    stats = chroma.get_stats()
    print(f"\nCollection   : {stats.collection_name}")
    print(f"Total vectors: {stats.total_vectors}")
    print(f"Documents    : {stats.unique_documents}")
    print(f"Sources      : {stats.document_names or ['(none — run ingestion first)']}")
    print()

    if stats.total_vectors == 0:
        print("✗ COLLECTION IS EMPTY")
        print("  Run: python scripts/ingest_documents.py")
        sys.exit(1)

    # ── Run each test query ────────────────────────────────────────────
    all_passed = True

    for query, description in TEST_QUERIES:
        print(_separator("─"))
        print(f'Test     : {description}')
        print(f'Query    : "{query}"')
        print(f'Top-K    : {TOP_K}')
        print(_separator("─"))

        results = chroma.search(query=query, k=TOP_K)

        if not results:
            print("  ✗ No results returned — check ingestion pipeline")
            all_passed = False
            print()
            continue

        # ── Print each result ──────────────────────────────────────────
        for i, result in enumerate(results, start=1):
            # Visual score bar: each █ = 0.1 similarity
            bar_length = int(result.score * 10)
            score_bar  = "█" * bar_length + "░" * (10 - bar_length)

            print(f"\n  Result #{i}")
            print(f"    Score    : {result.score:.4f}  [{score_bar}]")
            print(f"    Source   : {result.source}")
            print(f"    Page     : {result.page}")
            # Truncate long content for readability; full text is in ChromaDB
            preview = result.content.replace("\n", " ").strip()
            if len(preview) > 200:
                preview = preview[:200] + "..."
            print(f"    Content  : {preview}")

        print(f"\n  ✓ {len(results)} result(s) retrieved")
        print()

    # ── Final verdict ──────────────────────────────────────────────────
    print(_separator())
    if all_passed:
        print(f"✓ ALL TESTS PASSED — retrieval pipeline is working correctly")
    else:
        print("✗ SOME TESTS FAILED — review logs above")
    print(_separator())

    sys.exit(0 if all_passed else 2)


if __name__ == "__main__":
    run_retrieval_test()
