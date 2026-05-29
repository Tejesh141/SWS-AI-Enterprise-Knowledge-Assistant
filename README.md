# SWS-AI Enterprise Knowledge Assistant

A production-grade **Retrieval-Augmented Generation (RAG)** system that lets employees query internal company documents using natural language and receive grounded, cited answers powered by Google Gemini.

---

## Architecture Overview

```
PDF Documents
    │
    ▼
DocumentLoader          ← PyMuPDF: extract text page-by-page
    │
    ▼
TextChunker             ← LangChain RecursiveCharacterTextSplitter (500/50)
    │
    ▼
EmbeddingService        ← sentence-transformers/all-MiniLM-L6-v2 (384-dim)
    │
    ▼
ChromaService           ← Persist vectors to sws_ai_knowledge_base
    │
    ▼
RetrievalService        ← ANN search → top-k ranked chunks
    │
    ▼
GeminiService           ← Grounded prompt → answer + citations
    │
    ▼
POST /api/chat          ← FastAPI endpoint
```

---

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── chat.py                  # POST /api/chat router
│   ├── config/
│   │   └── settings.py              # Centralised config (pydantic-settings)
│   ├── ingestion/
│   │   ├── document_loader.py       # PDF → RawDocument (PyMuPDF)
│   │   └── text_chunker.py          # RawDocument → DocumentChunk (LangChain)
│   ├── models/
│   │   └── document.py              # All Pydantic domain models
│   ├── retrieval/
│   │   └── retrieval_service.py     # Query → embed → ANN search → RetrievalResult
│   ├── services/
│   │   ├── chroma_service.py        # ChromaDB gateway (insert, search, delete, stats)
│   │   ├── embedding_service.py     # SentenceTransformer wrapper
│   │   └── gemini_service.py        # Gemini prompt builder + API call
│   └── utils/
│       └── logger.py                # Structured logging factory
├── data/
│   ├── pdfs/                        # Drop source PDFs here
│   ├── processed/                   # Reserved for future pre-processing cache
│   └── chroma_db/                   # ChromaDB SQLite + HNSW index (auto-created)
├── scripts/
│   ├── ingest_documents.py          # Run ingestion pipeline
│   └── test_retrieval.py            # Validate retrieval end-to-end
├── .env                             # Environment configuration
├── main.py                          # FastAPI app entry point
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Edit `backend/.env`:

```env
GEMINI_API_KEY=your-google-ai-studio-key-here
GEMINI_MODEL=gemini-1.5-flash
CHROMA_COLLECTION_NAME=sws_ai_knowledge_base
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Ingest documents

```bash
# Drop PDF files into backend/data/pdfs/
python scripts/ingest_documents.py
```

### 4. Test retrieval

```bash
python scripts/test_retrieval.py
```

### 5. Start the API

```bash
uvicorn main:app --reload --port 8000
```

### 6. Query the knowledge base

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the annual leave entitlement?"}'
```

Response:

```json
{
  "answer": "Employees are entitled to 20 days of annual leave per year...",
  "sources": [
    { "document": "Leave Policy", "page": 2 }
  ]
}
```

---

## API Reference

| Method | Endpoint     | Description                              |
|--------|--------------|------------------------------------------|
| GET    | /health      | Liveness probe                           |
| POST   | /ingest      | Trigger ingestion pipeline               |
| POST   | /retrieve    | Raw chunk retrieval with similarity scores |
| POST   | /api/chat    | RAG chat — grounded answer + citations   |

Interactive docs: http://localhost:8000/docs

---

# Why ChromaDB?

ChromaDB was selected as the vector database for this project after evaluating several alternatives (FAISS, Pinecone, Weaviate, Qdrant). Here is the full rationale:

## Local Setup — Zero Infrastructure

ChromaDB runs entirely in-process as a Python library. There is no Docker container, no server process, no cloud account, and no network configuration required.

```bash
pip install chromadb
```

That single command is the entire setup. Compare this to alternatives:

- **Pinecone** — requires account creation, API key, and network access
- **Weaviate** — requires Docker or a managed cloud instance
- **Qdrant** — requires a running server process

For a local development environment or an assessment project, ChromaDB's zero-infrastructure model is a significant advantage.

## Fast Semantic Search

ChromaDB uses an **HNSW (Hierarchical Navigable Small World)** index for approximate nearest-neighbour search. HNSW is the industry-standard algorithm for high-dimensional vector search, offering:

- Sub-linear query time: O(log n) vs O(n) for brute-force
- Configurable precision/speed trade-off via `ef_construction` and `M` parameters
- Cosine similarity natively supported (`hnsw:space: cosine`)

For the 384-dimensional embeddings produced by `all-MiniLM-L6-v2`, ChromaDB returns top-3 results in under 10ms on a standard laptop CPU.

## No Cloud Dependency

All data stays on the local machine. This matters for:

- **Data privacy** — company documents never leave the local environment
- **Compliance** — no data residency concerns during development
- **Cost** — no per-query or per-vector pricing
- **Offline operation** — works without internet access after the embedding model is cached

## Easy Persistence

ChromaDB's `PersistentClient` writes every upsert to a local SQLite database and HNSW index files under the configured directory:

```
data/chroma_db/
├── chroma.sqlite3          ← metadata, document text, collection config
└── <uuid>/
    ├── data_level0.bin     ← HNSW graph (the actual vector index)
    ├── header.bin
    ├── length.bin
    └── link_lists.bin
```

Data survives application restarts automatically. No manual `.persist()` call is needed. The collection is loaded from disk on the next `PersistentClient` instantiation.

## Suitable for Assessment Projects

ChromaDB is the right choice for this stage of the project because:

1. **Reproducible** — any reviewer can clone the repo and run it with one command
2. **Inspectable** — the SQLite file can be opened with any SQLite browser for debugging
3. **No secrets required** — no API keys or cloud credentials needed for the vector store
4. **Well-documented** — extensive official docs and active community

## Scales Well for Future Migration

When this project moves to production at scale, ChromaDB's API is compatible with managed alternatives. The `ChromaService` class in this project is the single gateway to ChromaDB — no other module imports `chromadb` directly. This means migrating to a managed vector database requires changes in exactly one file:

```
Current:  chromadb.PersistentClient  →  local disk
Future:   chromadb.HttpClient        →  ChromaDB Cloud
Or:       Replace ChromaService      →  Pinecone / Weaviate / Qdrant
```

The rest of the application (ingestion pipeline, retrieval service, chat API) remains completely unchanged.

### Migration path example

```python
# Current (local development)
client = chromadb.PersistentClient(path="data/chroma_db")

# Future (production — ChromaDB Cloud)
client = chromadb.HttpClient(
    host="api.trychroma.com",
    ssl=True,
    headers={"X-Chroma-Token": os.environ["CHROMA_API_KEY"]},
)

# Future (production — self-hosted server)
client = chromadb.HttpClient(host="chroma.internal", port=8000)
```

The collection API (`get_or_create_collection`, `upsert`, `query`, `delete`) is identical across all client types.

---

## Collection Schema

Every chunk stored in `sws_ai_knowledge_base` has the following fields:

| Field                | Type         | Description                                      |
|----------------------|--------------|--------------------------------------------------|
| `id`                 | string       | `{filename}_p{page}_c{index}` — globally unique  |
| document             | string       | The chunk text (ChromaDB native document field)  |
| embedding            | float[384]   | Dense vector from all-MiniLM-L6-v2               |
| `source_document_name` | string     | Original PDF filename                            |
| `page_number`        | int          | 1-based page number                              |
| `chunk_index`        | int          | 0-based position within the page's chunks        |
| `chunk_id`           | string       | Duplicate of `id` for metadata-only queries      |
| `chunk_text_preview` | string       | First 120 chars of text for fast metadata queries|

---

## Environment Variables

| Variable                  | Default                              | Description                    |
|---------------------------|--------------------------------------|--------------------------------|
| `PDF_DIR`                 | `data/pdfs`                          | Source PDF directory           |
| `CHROMA_DB_DIR`           | `data/chroma_db`                     | ChromaDB persistence directory |
| `CHROMA_COLLECTION_NAME`  | `sws_ai_knowledge_base`              | Collection name                |
| `EMBEDDING_MODEL`         | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace model ID       |
| `CHUNK_SIZE`              | `500`                                | Max characters per chunk       |
| `CHUNK_OVERLAP`           | `50`                                 | Overlap between chunks         |
| `TOP_K`                   | `3`                                  | Chunks retrieved per query     |
| `SIMILARITY_THRESHOLD`    | `0.0`                                | Minimum score to include result|
| `GEMINI_API_KEY`          | *(required)*                         | Google AI Studio API key       |
| `GEMINI_MODEL`            | `gemini-1.5-flash`                   | Gemini model identifier        |
| `LOG_LEVEL`               | `INFO`                               | Logging verbosity              |

---

## Design Principles

This codebase follows **SOLID principles** throughout:

- **S** — Each class has one responsibility: `DocumentLoader` only loads, `TextChunker` only chunks, `EmbeddingService` only embeds, `ChromaService` only persists/retrieves
- **O** — `ChromaService` can be extended with new methods without modifying existing ones
- **L** — All services accept their dependencies via constructor injection and can be substituted with mocks in tests
- **I** — No service is forced to depend on methods it doesn't use
- **D** — High-level modules (`RetrievalService`, `GeminiService`) depend on injected abstractions, not concrete implementations
