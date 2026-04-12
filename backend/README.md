# TutorRAG

TutorRAG is a grounded Retrieval-Augmented Generation (RAG) backend for self-learning from personal study materials.  
The project is organized around one core principle:

> **Grounded first, reasoning second.**

The system is designed to answer questions using only retrieved evidence from user documents, avoid unsupported claims, and expose a clean FastAPI backend that can evolve from an MVP into a stronger tutoring-oriented RAG system.

---

## Project Goal

TutorRAG aims to provide a runnable backend that can:

1. manage document metadata and local storage,
2. parse and normalize study documents,
3. chunk documents with traceable metadata,
4. index chunks for dense + sparse retrieval,
5. retrieve relevant evidence for a user query,
6. synthesize grounded answers with source-aware citations,
7. verify whether the produced answer is sufficiently supported.

---

## Core Design Principles

1. **Evidence First**  
   Every important statement should be grounded in retrieved chunks.

2. **No Unsupported Claims**  
   If evidence is insufficient, the system should say so explicitly.

3. **Source-Aware Output**  
   Answers should preserve traceability through document/chunk/page metadata.

4. **Grounded First, Reasoning Second**  
   Retrieval comes before synthesis. Reasoning operates on evidence, not on free-form speculation.

5. **Modular MVP First**  
   The current codebase prioritizes a runnable, locally testable architecture before integrating heavier production components.

---

## Current Implementation Status

### Implemented now

- FastAPI application bootstrap
- API routing for:
  - health check
  - document metadata endpoints
  - chat endpoint
  - search endpoint
- Async SQLAlchemy database layer
- Local file storage
- PDF / DOCX / PPTX parsing
- text normalization
- chunk generation with overlap and source metadata
- in-memory-first indexing and retrieval
- dense + sparse + hybrid retrieval
- deterministic reranking
- deterministic reasoning fallback
- deterministic answer verification and claim checking
- pytest-based test suite for ingestion, retrieval, and reasoning pipeline

### Current MVP limitation

The codebase is intentionally runnable without requiring:
- Qdrant
- external LLM APIs
- reranker model servers
- production-scale retrieval infra

That means:
- retrieval currently uses an **in-memory vector store fallback**,
- reasoning and verification currently use **deterministic fallback logic**,
- the document API currently focuses on **document metadata**, while the full byte-level ingestion flow is already implemented at the service layer and can be exposed through a dedicated upload endpoint next.

---

## Repository Structure

```text
Main/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── ingestion/
│   ├── prompts/
│   ├── reasoning/
│   ├── retrieval/
│   ├── schemas/
│   ├── services/
│   ├── storage/
│   ├── verification/
│   ├── __init__.py
│   └── main.py
├── docs/
├── logs/
├── plan/
├── tests/
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

### `app/api/`
Thin FastAPI routers:
- `routes_health.py`
- `routes_documents.py`
- `routes_chat.py`
- `routes_search.py`

### `app/core/`
Shared application infrastructure:
- settings/config
- logging
- constants
- exceptions

### `app/db/`
Async SQLAlchemy database layer:
- base / engine / sessions
- ORM models
- repositories for documents, chunks, answers, feedback

### `app/ingestion/`
Offline ingestion utilities:
- file parsing
- normalization
- chunking

### `app/prompts/`
Centralized prompt templates and prompt builders for reasoning and verification flows.

### `app/reasoning/`
Reasoning components:
- query classification
- query decomposition
- bounded planning
- synthesis
- citation formatting

### `app/retrieval/`
Retrieval components:
- embedder
- sparse encoder
- dense retriever
- sparse retriever
- hybrid retriever
- reranker
- evidence builder
- vector store

### `app/schemas/`
Pydantic schemas shared across API, services, ingestion, retrieval, and DB-adjacent flows.

### `app/services/`
High-level orchestration layer:
- document ingestion flow
- retrieval flow
- tutoring flow

### `app/storage/`
Local file persistence helpers.

### `app/verification/`
Post-synthesis validation:
- answer verification
- claim support checking

### `tests/`
Project tests for:
- ingestion
- retrieval
- reasoning pipeline

---

## High-Level Architecture

TutorRAG is organized into two main domains.

### 1. Offline Ingestion / Indexing

This layer is responsible for turning raw study documents into searchable chunks.

Pipeline:

1. save uploaded bytes to local storage
2. choose parser based on file type
3. extract raw text + source location hints
4. normalize text while preserving useful structure
5. chunk the text with overlap
6. attach metadata such as:
   - document id
   - source file
   - page range
   - chunk offsets
7. optionally persist chunk metadata to DB
8. index chunks for retrieval

### 2. Online Query / Reasoning

This layer is responsible for answering user questions.

Pipeline:

1. receive query
2. classify query type
3. decompose query if needed
4. generate a bounded plan
5. retrieve evidence using hybrid retrieval
6. rerank results
7. build structured evidence objects
8. synthesize a grounded answer
9. verify whether the answer is supported
10. return structured output to the API layer

---

## Main API Endpoints

The API base path is:

```text
/api/v1
```

### Health
- `GET /api/v1/health/`

Simple health check for application + database connectivity.

### Documents
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents/{document_id}`

Current behavior:
- `POST /documents/upload` stores **document metadata**
- the full file-byte ingestion pipeline is currently implemented in services and can be connected to a dedicated upload endpoint later

### Chat
- `POST /api/v1/chat/ask`

Runs the grounded tutoring flow:
- classify
- plan
- retrieve
- synthesize
- verify

### Search
- `POST /api/v1/search/`

Runs retrieval and returns structured evidence.

---

## Example Request Shapes

### Chat request

```json
{
  "question": "What is BCNF?",
  "user_id": "user_1",
  "chat_history": [],
  "subject_hint": "database"
}
```

### Search request

```json
{
  "question": "Find the chunks that explain BCNF",
  "user_id": "user_1",
  "chat_history": [],
  "subject_hint": "database"
}
```

### Document metadata request

```json
{
  "document_id": "doc_001",
  "user_id": "user_1",
  "subject": "database",
  "title": "Normalization Notes",
  "source_type": "pdf",
  "language": "vi",
  "file_name": "normalization.pdf",
  "file_path": "/absolute/path/to/normalization.pdf",
  "mime_type": "application/pdf",
  "checksum_sha256": null,
  "tags": ["normalization", "bcnf"],
  "status": "uploaded"
}
```

---

## Technology Stack

- **Python 3.10+**
- **FastAPI**
- **Pydantic v2**
- **SQLAlchemy 2.x (async)**
- **SQLite + aiosqlite** for local development
- **PyPDF / PyPDF2**
- **python-docx**
- **python-pptx**
- **pytest / pytest-asyncio**

Optional / future-oriented:
- sentence-transformers
- production vector database integration
- external LLM client integration
- stronger reranking / evaluation stack

---

## Configuration

Example `.env`:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=a_very_long_random_secret_key_string
API_V1_STR=/api/v1
LOG_LEVEL=INFO
LOG_DIR=./logs
VECTOR_STORE_HOST=localhost
VECTOR_STORE_PORT=6333
VECTOR_STORE_API_KEY=
```

### Important note

For the current async DB setup, SQLite URLs should use:

```dotenv
sqlite+aiosqlite:///./your_db_file.db
```

not plain `sqlite:///...`.

---

## Quick Start

### 1. Install dependencies

Using Poetry:

```bash
poetry install
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Then update the values if needed.

### 3. Run the API

```bash
poetry run uvicorn app.main:app --reload
```

### 4. Open Swagger UI

```text
http://localhost:8000/docs
```

---

## Running Tests

Run all tests:

```bash
poetry run pytest
```

Run one test file:

```bash
poetry run pytest tests/test_retrieval.py
```

---

## Current Retrieval Strategy

The current retrieval layer is designed to stay runnable in local development without external infrastructure.

### Dense retrieval
- uses an embedding model if available
- falls back to deterministic hash-based embeddings if the model is unavailable

### Sparse retrieval
- uses normalized lexical term weighting

### Hybrid retrieval
- merges dense and sparse candidates
- deduplicates candidates
- combines scores

### Reranking
- uses deterministic lexical overlap boosting

### Vector store
- currently defaults to an in-memory store
- keeps module boundaries compatible with later production vector DB integration

---

## Current Reasoning and Verification Strategy

The current reasoning layer is intentionally deterministic so the project can run end-to-end before LLM integration.

### Reasoning
- query classification via heuristic routing
- decomposition for multi-part questions
- bounded planning
- answer synthesis from retrieved evidence

### Verification
- answer-level support checking
- claim-level support checking

This lets the system maintain the intended architecture now, while leaving a clean extension path toward real LLM-driven reasoning later.

---

## Development Roadmap

### Completed
- Foundation skeleton
- Core config / logging / DB setup
- Ingestion MVP
- Retrieval MVP
- Reasoning + verification fallback MVP

### Next
- dedicated file upload endpoint integrated with ingestion service
- persistent vector backend integration
- stronger reranking model
- real LLM client integration
- better citation-aware synthesis
- evaluation and benchmarking
- final demo hardening

---

## Recommended Next Technical Tasks

1. expose byte-level document upload through API
2. persist indexed chunk metadata more deeply
3. add feedback endpoints if needed
4. add evaluation scripts
5. connect production vector DB
6. connect production LLM backend
7. improve verification granularity
8. add end-to-end API tests for document ingestion + retrieval + tutoring

---

## Project Philosophy

TutorRAG is being built as a practical, modular tutoring backend:
- easy to boot locally,
- strict about grounded answers,
- structured for future scaling,
- and designed so each layer can be upgraded independently.

That means the current version prioritizes:
- correctness of flow,
- module boundaries,
- local testability,
over early optimization or external-service dependence.

---

## License / Notes

This repository is currently a project codebase under active development.  
Adjust authorship, licensing, deployment settings, and production dependencies as needed for your final release.
