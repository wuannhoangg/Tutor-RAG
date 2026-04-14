# TutorRAG

**TutorRAG** is a production-ready grounded Retrieval-Augmented Generation (RAG) system for self-study over personal learning materials.

The project is built around one central principle:

> **Grounded first, reasoning second.**

Instead of answering from unconstrained model memory, TutorRAG retrieves relevant evidence from user documents first, then performs synthesis and verification on top of that evidence. The result is a tutoring-oriented system that emphasizes traceability, source awareness, and explicit handling of insufficient evidence.

---

## Live Deployment

### Public web app
```text
https://wuannlab.id.vn/
```

### Backend deployment
```text
https://huggingface.co/spaces/wuann/tutor-rag-backend
```

### Frontend deployment
```text
https://dashboard.render.com/web/srv-d7dqqogsfn5c738gv900
```

---

## Project Status

TutorRAG is no longer just an MVP skeleton. The project has been completed into a full end-to-end system with:

- authenticated multi-user access,
- document upload and ingestion,
- local + database-backed metadata persistence,
- grounded retrieval and tutoring flows,
- streaming chat responses,
- citation-aware output,
- deployment of both frontend and backend.

The current version is a working full-stack application composed of:

- a **FastAPI backend**,
- a **React / Next.js frontend**,
- **Supabase Auth + PostgreSQL**,
- **Qdrant vector storage**,
- and configurable **LLM provider integration**.

---

## Project Goal

TutorRAG is designed to help users learn from their own materials by allowing them to:

1. upload study documents,
2. organize documents into folders,
3. index and retrieve evidence from those documents,
4. ask grounded questions over uploaded materials,
5. receive answers with citations and source traceability,
6. verify whether the answer is sufficiently supported,
7. use the system through a deployed web interface with authentication.

---

## Core Design Principles

### 1. Evidence First
Every meaningful answer should be grounded in retrieved chunks.

### 2. No Unsupported Claims
If evidence is insufficient, the system should say so explicitly.

### 3. Source-Aware Output
Answers preserve source traceability through document, chunk, and page metadata.

### 4. Grounded First, Reasoning Second
Retrieval comes before synthesis. Reasoning operates on evidence, not on unconstrained speculation.

### 5. Modular Architecture
Each major layer is separated so retrieval, reasoning, ingestion, storage, and API behavior can be improved independently.

### 6. Practical Deployment
The project is built not only to run locally, but also to operate as a real deployed application for end users.

---

## Main Features

### Authentication and user isolation
- signup and login using Supabase Auth,
- JWT-based backend protection,
- automatic synchronization of authenticated users into the local application database,
- per-user document and folder isolation.

### Document management
- create folders,
- list folders,
- upload files into folders,
- list uploaded documents,
- retrieve document metadata.

### Supported file types
- PDF
- DOCX
- PPTX

### Ingestion pipeline
- file storage,
- parser selection by file extension,
- text extraction,
- normalization,
- chunking with overlap,
- metadata attachment,
- optional persistence to database,
- indexing into retrieval components.

### Retrieval pipeline
- dense retrieval,
- sparse retrieval using BM25,
- hybrid retrieval,
- reranking,
- evidence construction.

### Tutoring pipeline
- query classification,
- decomposition for multi-step questions,
- bounded planning,
- grounded synthesis,
- answer verification,
- claim checking,
- citation-aware response construction.

### Streaming experience
- server-sent events (SSE) based chat streaming,
- staged status updates during classification, planning, retrieval, generation, and verification.

### Runtime flexibility
- platform default LLM mode,
- BYOK mode for provider-based user configuration,
- configurable provider/model/base URL flow.

---

## High-Level System Architecture

TutorRAG is organized into two major domains.

---

### 1. Offline Ingestion / Indexing

This domain transforms raw uploaded files into searchable chunks.

#### Pipeline
1. receive uploaded file bytes,
2. store file locally,
3. choose parser by file type,
4. extract raw text and page/slide hints,
5. normalize text,
6. split text into chunks with overlap,
7. attach metadata such as:
   - document ID,
   - source file,
   - page range,
   - chunk offsets,
   - subject,
   - language,
   - source type,
   - user ID,
8. optionally persist document and chunk metadata to PostgreSQL,
9. generate embeddings and retrieval artifacts,
10. index into vector store and sparse index.

---

### 2. Online Query / Grounded Reasoning

This domain answers user questions over uploaded materials.

#### Pipeline
1. receive query,
2. authenticate user,
3. classify query type,
4. decompose the query if needed,
5. generate a bounded plan,
6. retrieve evidence using hybrid retrieval,
7. rerank candidates,
8. build structured evidence objects,
9. synthesize a grounded answer,
10. verify support for the answer,
11. perform claim support checking,
12. return structured results to the frontend.

---

## Repository Structure

```text
Main/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── graph/
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
├── migrations/
├── tests/
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Backend Module Breakdown

### `app/api/`
Thin FastAPI routers exposing backend functionality:

- `routes_health.py`
- `routes_documents.py`
- `routes_chat.py`
- `routes_search.py`
- `routes_upload.py`

### `app/core/`
Shared infrastructure:

- settings / environment configuration,
- logging,
- auth,
- constants,
- exceptions,
- LLM provider resolution,
- LLM client integration.

### `app/db/`
Async SQLAlchemy database layer:

- engine and sessions,
- ORM models,
- repository pattern,
- migration-compatible metadata base.

### `app/graph/`
Concept-centric utilities:

- concept extraction,
- concept routing.

### `app/ingestion/`
Document ingestion utilities:

- PDF / DOCX / PPTX parsing,
- normalization,
- chunking.

### `app/prompts/`
Central prompt templates and prompt builders for:

- reasoning,
- graph extraction,
- verification.

### `app/reasoning/`
Reasoning pipeline:

- query classification,
- query decomposition,
- planning,
- synthesis,
- citation formatting.

### `app/retrieval/`
Retrieval pipeline:

- embedder,
- BM25 index,
- dense retriever,
- sparse retriever,
- hybrid retriever,
- reranker,
- evidence builder,
- vector store abstraction and implementations.

### `app/schemas/`
Pydantic schemas shared across API, services, ingestion, retrieval, and verification flows.

### `app/services/`
High-level orchestration:

- document service,
- ingestion service,
- retrieval service,
- tutoring service,
- tutoring stream service.

### `app/storage/`
Local file persistence utilities.

### `app/verification/`
Support checking:

- answer verification,
- claim checking.

---

## Main API Endpoints

Base path:

```text
/api/v1
```

### Health
- `GET /api/v1/health/`

Checks application and database connectivity.

### Documents
- `POST /api/v1/documents/upload`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `GET /api/v1/documents/folders`
- `POST /api/v1/documents/folders`

Handles document metadata and folder management.

### Upload
- `POST /api/v1/upload/file`

Handles actual file upload, ingestion, chunking, indexing, and metadata creation.

### Chat
- `POST /api/v1/chat/ask`
- `POST /api/v1/chat/ask/stream`

Runs grounded tutoring with non-streaming and streaming modes.

### Search
- `POST /api/v1/search/`

Returns structured evidence from retrieval.

---

## Example Request Shapes

### Chat request

```json
{
  "question": "What is BCNF?",
  "chat_history": [],
  "subject_hint": "database"
}
```

### Search request

```json
{
  "question": "Find the chunks that explain BCNF",
  "chat_history": [],
  "subject_hint": "database"
}
```

### Folder creation request

```json
{
  "name": "Database"
}
```

---

## Technology Stack

The following technologies are already used in the completed project.

### Backend
- **Python 3.10+**
- **FastAPI**
- **Pydantic v2**
- **SQLAlchemy 2.x (async)**
- **Alembic**
- **Uvicorn**

### Database and authentication
- **Supabase PostgreSQL**
- **Supabase Auth**
- **JWT authentication**
- **asyncpg**

### Retrieval and indexing
- **Qdrant**
- **rank-bm25**
- **sentence-transformers**
- **cross-encoder reranking**
- fallback in-memory vector store
- fallback deterministic hash embedding

### LLM integration
- **LiteLLM**
- configurable provider routing
- support for:
  - Google AI
  - OpenAI
  - Anthropic
  - OpenAI-compatible endpoints
  - local-runtime style configuration patterns

### Document processing
- **pypdf / PyPDF2**
- **python-docx**
- **python-pptx**

### Frontend
- **Next.js**
- **React**
- **TypeScript**
- **Supabase JS client**
- **Framer Motion**
- **Tailwind CSS**
- **shadcn/ui**
- **Lucide React**

### Deployment
- **Hugging Face Spaces** for backend deployment
- **Render** for frontend deployment
- custom domain for public testing

### Testing
- **pytest**
- **pytest-asyncio**

---

## Retrieval Strategy

TutorRAG uses a layered retrieval design.

### Dense retrieval
- uses sentence embeddings when available,
- falls back to deterministic hash embeddings if model loading is unavailable.

### Sparse retrieval
- uses BM25 lexical retrieval.

### Hybrid retrieval
- merges dense and sparse candidates,
- deduplicates overlapping results,
- combines scores.

### Reranking
- uses a lexical reranker by default,
- upgrades to a cross-encoder reranker when available.

### Vector storage
- uses Qdrant in deployed environments,
- supports in-memory fallback for local development or degraded operation.

---

## Reasoning and Verification Strategy

TutorRAG applies reasoning only after evidence has been retrieved.

### Reasoning
- query classification,
- decomposition for multi-part questions,
- bounded planning,
- grounded synthesis,
- citation-aware answer packaging.

### Verification
- answer-level verification,
- claim-level support checking,
- deterministic fallback support checks when needed.

This helps keep the system aligned with the project’s grounding principle even when runtime conditions are imperfect.

---

## Frontend Experience

The deployed frontend supports:

- signup / login,
- session-aware protected access,
- folder creation,
- document upload,
- document listing,
- chat interaction,
- streaming answers,
- citation rendering,
- BYOK provider selection,
- runtime configuration switching between platform-default and user-supplied providers.

---

## Configuration

A typical environment includes configuration for:

- API base path,
- logging,
- database,
- Supabase auth,
- Qdrant,
- platform LLM provider,
- CORS origins.

Example local SQLite URL for async development:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

Example production-style async PostgreSQL URL pattern:

```dotenv
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DB_NAME
```

---

## Local Development

### 1. Install dependencies

```bash
poetry install
```

### 2. Create environment file

```bash
cp .env.example .env
```

### 3. Run migrations

```bash
poetry run alembic upgrade head
```

### 4. Start backend

```bash
poetry run uvicorn app.main:app --reload
```

### 5. Open API docs

```text
http://localhost:8000/docs
```

### 6. Start frontend
Run the frontend in its own environment using the appropriate Next.js dev command.

---

## Running Tests

Run the full suite:

```bash
poetry run pytest
```

Run a specific file:

```bash
poetry run pytest tests/test_retrieval.py
```

---

## Production Notes

The project is fully deployed and usable, but the current deployment relies heavily on **free-tier infrastructure**, which introduces some practical limitations.

### Current limitations

#### 1. Slow model responses
Because model infrastructure and runtime resources are limited, responses can be noticeably slower than on paid production infrastructure.

#### 2. Serverless / non-persistent behavior
The deployed services run on free-tier environments, which may sleep, cold start, or recycle instances. This can cause:
- delayed first response,
- temporary unavailability after idle periods,
- non-persistent local runtime state.

#### 3. Large file upload instability
Large files may fail during upload or processing because:
- parsing and chunking can take too long,
- vector indexing can take too long,
- the connection between frontend and backend may be interrupted,
- free-tier server timeouts may cut off long-running requests.

#### 4. Streaming interruptions
Streaming chat depends on long-lived HTTP connections. On free infrastructure, these connections may occasionally be interrupted during longer generations.

#### 5. Resource-constrained indexing
Dense indexing, concept extraction, reranking, and retrieval all share limited compute resources, so heavy ingestion workflows may feel slow.

These limitations are primarily deployment-resource limitations, not core architecture limitations.

---

## Completed Scope

TutorRAG in its current state already includes:

- completed end-to-end backend architecture,
- deployed public web interface,
- authenticated multi-user flow,
- full upload-to-index pipeline,
- grounded retrieval and tutoring,
- streaming interaction,
- deployment on public infrastructure.

In other words, the project has moved beyond a prototype and now functions as a real deployed system, even though the infrastructure tier still imposes practical constraints.

---

## Future Improvements

Potential next upgrades include:

1. move backend to persistent paid hosting,
2. move frontend and backend to higher-timeout infrastructure,
3. support larger file uploads more robustly,
4. improve long-document ingestion resilience,
5. improve citation rendering and answer faithfulness,
6. add stronger evaluation and benchmarking,
7. add more end-to-end tests for deployed behavior,
8. improve observability and monitoring.

---

## Project Philosophy

TutorRAG is built as a practical tutoring backend that prioritizes:

- grounded answers,
- modular design,
- real deployability,
- clear source traceability,
- extensibility for future improvements.

The current system already demonstrates the full intended architecture in production form, while still leaving room for stronger infrastructure and model improvements later.

---

## Notes

This repository is under active maintenance and can still be improved in terms of infrastructure, performance, and deployment robustness. The main remaining limitations come from free-tier hosting and runtime constraints, not from absence of core project functionality.
