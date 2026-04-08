# TutorRAG — Current State Audit and 100% Completion Plan

## 0. Purpose of this document

This document has two goals:

1. **Record the real current state of the project** based on the repository structure and code that has already been reviewed.
2. **Define a detailed execution plan to complete the system to the full target architecture described in `rag.tex`**, including:
   - what is already done,
   - what is only MVP / fallback / temporary,
   - what still needs to be built,
   - exactly which files and folders should be edited or created next,
   - how each missing part should be implemented.

This is written as a working engineering document, not as a marketing summary.

---

## 1. Important scope note

This document distinguishes between 3 different notions of “done”:

### 1.1 Confirmed in repository structure
These are files/folders that are already present in the project tree.

### 1.2 Implemented in code or already designed through the review
These are modules that either:
- already exist and have working logic, or
- have already been redesigned in detail during the review and can be considered part of the intended current implementation baseline.

### 1.3 Not yet fully complete relative to `rag.tex`
These are the remaining gaps between:
- the current MVP / deterministic fallback implementation, and
- the final target system envisioned by the roadmap in `rag.tex`.

This distinction matters because some parts are already **runnable**, but are not yet **100% production-complete**.

---

## 2. Current confirmed repository structure

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

The project already has the right **top-level modular decomposition** for a grounded RAG backend:
- API
- core infra
- DB
- ingestion
- prompts
- reasoning
- retrieval
- schemas
- services
- storage
- verification
- tests

That is a strong foundation and matches the high-level direction of `rag.tex`.

---

## 3. What has been achieved so far

## 3.1 Architecture-level achievements

The project already has the correct **system shape** for a TutorRAG-style backend:

### Done
- Clear separation between **offline ingestion/indexing** and **online query/reasoning**.
- Separate modules for:
  - parsing,
  - normalization,
  - chunking,
  - retrieval,
  - reasoning,
  - verification,
  - API orchestration,
  - database persistence.
- Pydantic schemas for data contracts.
- Async SQLAlchemy foundation.
- FastAPI application entrypoint.
- Test folder already present.

### Why this matters
This means the repo is **not a toy script** anymore.  
It already has the shape of a scalable backend, which is exactly what the roadmap in `rag.tex` expects.

---

## 3.2 API layer status (`app/api/`)

### What is already present
- `routes_health.py`
- `routes_documents.py`
- `routes_chat.py`
- `routes_search.py`
- central router wiring in `app/api/__init__.py`

### Current capability
The project already has an API layer for:
- health checking,
- document metadata operations,
- search,
- tutoring/chat.

### Current maturity
- **Good enough for MVP routing**
- still thin, which is good
- but some endpoints are still **service-contract dependent**
- document route is still mainly **metadata-oriented**, not full binary upload orchestration yet

### Current conclusion
**API foundation is done.**  
What remains is endpoint hardening and extending document upload to the full file-ingestion flow.

---

## 3.3 Core infrastructure status (`app/core/`)

### What is already present
- `config.py`
- `logging.py`
- `exceptions.py`
- `constants.py`
- `__init__.py`

### What has effectively been achieved
- centralized settings
- logging bootstrap
- custom exception structure
- common constants
- stable import surface for core utilities

### Current maturity
- good for local MVP
- strong enough to support further system integration
- still missing some later-stage production concerns like:
  - secret management beyond `.env`
  - environment segmentation (dev/test/prod)
  - more granular app-wide error classes
  - possibly provider registry / LLM config registry

### Current conclusion
**Core is in a good MVP state** and no longer blocks the main pipeline.

---

## 3.4 Database layer status (`app/db/`)

### What is already present
- async DB base / engine / session handling
- ORM models
- repositories for:
  - documents
  - chunks
  - answers
  - feedback

### What has effectively been achieved
- a single SQLAlchemy base can be used
- document records can be persisted
- chunk records can be persisted
- feedback records can be persisted
- answers and citations have a representable persistence path

### Current maturity
- enough for local DB-backed MVP
- schema is still relatively simple
- migration system not yet formalized
- no Alembic setup yet
- no persistent query log / session log tables yet
- no concept/graph tables yet

### Current conclusion
**DB is sufficient for MVP**, but still not at the “100% system” level defined by `rag.tex`.

---

## 3.5 Ingestion status (`app/ingestion/`)

### What is already present
- parser for PDF
- parser for DOCX
- parser for PPTX
- normalizer
- chunker

### What has effectively been achieved
The ingestion pipeline concept is already complete:

1. read file
2. parse raw text
3. normalize
4. chunk with metadata
5. send to persistence/indexing layers

### Current maturity
- document parsing exists for the 3 important formats
- normalizer preserves structure better than trivial whitespace flattening
- chunker supports overlap and metadata
- page-level hints can be propagated

### Current limitations
- no OCR fallback
- no layout-aware semantic chunking yet
- no table-aware extraction
- no robust image/diagram extraction
- no parser benchmarking / quality scoring
- no document-type-specific heuristics yet

### Current conclusion
**Ingestion MVP is done**, but `rag.tex` expects a stronger ingestion/indexing subsystem than the current baseline.

---

## 3.6 Prompt layer status (`app/prompts/`)

### What is already present
- reasoning prompts
- verification prompts
- centralized exports

### What has effectively been achieved
- prompts are centralized
- templates are reusable
- builder helpers can be used to render prompts cleanly
- the prompt layer is structured in a way that is ready for future real LLM integration

### Current limitations
- current reasoning/verification flow can run deterministically without calling real LLMs
- prompt quality exists, but prompt execution is not yet the main runtime path
- no provider-specific prompt adaptation yet

### Current conclusion
**Prompt repository is ready enough** for the next stage, but the real LLM runtime integration is still pending.

---

## 3.7 Reasoning status (`app/reasoning/`)

### What is already present
- query classification
- query decomposition
- planner
- synthesizer
- citation builder

### What has effectively been achieved
The project already has a structured reasoning pipeline:

1. classify query
2. decide whether decomposition is required
3. generate a bounded plan
4. retrieve evidence
5. synthesize answer
6. attach source-aware citations

### Current maturity
- reasoning can run even without a real LLM
- deterministic fallback logic exists or has already been designed
- bounded planning is conceptually aligned with `rag.tex`
- citation formatting is already part of the pipeline

### Current limitations
- still heuristic / deterministic rather than truly LLM-driven
- no multi-step memory-aware planner state object yet
- no structured reasoning trace persistence yet
- no claim-to-evidence alignment map yet
- no explicit “unsupported claim rejection at sentence level” beyond simple verification heuristics
- no graph-aware reasoning yet

### Current conclusion
**Reasoning MVP exists**, but the final `rag.tex` target is significantly richer.

---

## 3.8 Retrieval status (`app/retrieval/`)

### What is already present
- embedder
- sparse encoder
- dense retriever
- sparse retriever
- hybrid retriever
- reranker
- metadata filters
- evidence builder
- vector store

### What has effectively been achieved
The retrieval stack already has the correct moving parts:

- dense retrieval
- sparse retrieval
- hybrid merge
- reranking
- evidence shaping

### Current maturity
- local runnable retrieval path exists
- in-memory-first fallback means the project can work without external vector infra
- metadata filters exist
- evidence objects are structurally available

### Current limitations
- vector store is not yet finalized as production Qdrant integration
- sparse retrieval is still basic lexical encoding, not true BM25 or SPLADE-style sparse retrieval
- reranker is deterministic / lightweight, not model-based
- no retrieval calibration, score normalization, or systematic error analysis
- no retrieval evaluation framework integrated yet

### Current conclusion
**Retrieval MVP is done**, but production-grade retrieval is not yet complete.

---

## 3.9 Schema status (`app/schemas/`)

### What is already present
- document schemas
- chunk schemas
- query schemas
- answer schemas
- evidence schemas
- feedback schemas
- concept schemas
- common metadata schemas

### What has effectively been achieved
The project has the necessary DTO / validation layer for:
- API requests,
- API responses,
- ingestion metadata,
- retrieval evidence,
- answer packaging,
- feedback collection.

### Current maturity
- good shape for internal consistency
- aliases and flexible compatibility are possible
- enough for cross-layer integration

### Current limitations
- concept schema exists, but concept subsystem does not yet fully exist
- no explicit evaluation schema pack yet
- no graph-edge schema pack yet beyond prerequisites
- no schema versioning conventions yet

### Current conclusion
**Schemas are already a strong part of the system** and do not block future work.

---

## 3.10 Services status (`app/services/`)

### What is already present
- `document_service.py`
- `ingestion_service.py`
- `retrieval_service.py`
- `tutoring_service.py`

### What has effectively been achieved
The project already has a service/orchestration layer to connect:
- storage,
- ingestion,
- DB persistence,
- retrieval,
- reasoning,
- verification.

### Current maturity
- correct abstraction layer exists
- services can coordinate multi-step workflows
- good direction for end-to-end execution

### Current limitations
- some flows are still MVP-grade
- no robust job orchestration for large ingestion tasks
- no background job queue
- no persistent status tracking per ingestion job
- no feedback service yet
- no evaluation service yet

### Current conclusion
**Service architecture is correct**, but there are several missing service modules for the full target system.

---

## 3.11 Storage status (`app/storage/`)

### What is already present
- local storage abstraction
- file manager abstraction

### What has effectively been achieved
- local file persistence exists
- services can save uploaded bytes
- file path resolution is possible

### Current limitations
- no cloud storage backend
- no checksum enforcement workflow
- no storage cleanup / dedup policy
- no document versioning

### Current conclusion
**Local MVP storage is done**, but not the final storage architecture.

---

## 3.12 Verification status (`app/verification/`)

### What is already present
- answer verifier
- claim checker

### What has effectively been achieved
The project already includes a separate verification stage after synthesis, which is important and directly aligned with the “grounded first” principle.

### Current maturity
- support checking exists
- answer-level and claim-level verification are conceptually separated

### Current limitations
- still deterministic fallback / heuristic
- no true citation alignment scoring
- no NLI-style verifier
- no contradiction detector
- no abstention-confidence calibration

### Current conclusion
**Verification MVP exists**, but the full anti-hallucination layer from the ideal roadmap is not yet complete.

---

## 3.13 Testing status (`tests/`)

### What is already present
- ingestion tests
- reasoning pipeline tests
- retrieval tests

### What has effectively been achieved
- there is already a place for automated validation
- core system areas are covered conceptually

### Current limitations
- tests need to be aligned tightly with the final code contracts
- coverage is still limited
- no database integration tests
- no document parsing regression corpus
- no evaluation benchmark tests
- no end-to-end API test suite for full upload → ingest → retrieve → answer

### Current conclusion
**Testing exists as a foundation**, but not yet as a robust release-quality safety net.

---

## 4. Overall maturity assessment relative to `rag.tex`

## 4.1 What is already strong
These areas are already on the right trajectory and mostly match the MVP intent of `rag.tex`:

- modular repository structure
- API/service/repository layering
- ingestion pipeline skeleton
- hybrid retrieval structure
- reasoning stage separation
- verification stage separation
- grounded-answer philosophy
- source-aware metadata handling

## 4.2 What is still only MVP / fallback
These areas exist, but are not yet final:

- in-memory vector store instead of production vector backend
- heuristic/deterministic reasoning instead of real LLM orchestration
- heuristic verification instead of stronger verifier
- metadata upload route instead of full file-ingestion API route
- no proper migration system
- no evaluation subsystem
- no concept graph / relation graph runtime
- no production deployment hardening

## 4.3 What is still genuinely missing for 100%
These are the major missing blocks relative to the final roadmap:

1. **real ingestion API for file bytes**
2. **Alembic migrations**
3. **persistent indexing backend**
4. **real sparse retrieval / lexical index**
5. **real reranker model**
6. **real LLM client integration**
7. **concept extraction and concept index**
8. **relation graph / knowledge graph**
9. **graph-aware retrieval / graph-enhanced reasoning**
10. **evaluation framework**
11. **feedback-driven improvement loop**
12. **deployment / observability / production hardening**

---

# PART II — Detailed plan to complete the system to 100%

---

## 5. Guiding principle for the remaining work

To finish the system in a way that is faithful to `rag.tex`, the work should be done in this order:

1. **stabilize the current MVP so everything boots and tests pass**
2. **finish the ingestion + indexing path end to end**
3. **upgrade retrieval to production-grade**
4. **upgrade reasoning from deterministic fallback to real grounded LLM flow**
5. **upgrade verification**
6. **add concept index and relation graph**
7. **add evaluation and benchmarking**
8. **add deployment hardening**

Do **not** jump directly to GraphRAG / agents / Neo4j before the MVP path is stable.

---

## 6. Phase 0 — Stabilize the current repository baseline

## 6.1 Goal
Make the current project:
- boot successfully,
- run tests,
- ingest documents,
- index chunks,
- answer grounded queries locally.

## 6.2 Files to finalize now
These files should be treated as the first stabilization pass:

### API
- `app/api/__init__.py`
- `app/api/routes_chat.py`
- `app/api/routes_documents.py`
- `app/api/routes_health.py`
- `app/api/routes_search.py`

### Core
- `app/core/__init__.py`
- `app/core/config.py`
- `app/core/logging.py`
- `app/core/exceptions.py`

### DB
- `app/db/__init__.py`
- `app/db/base.py`
- `app/db/models.py`
- `app/db/repositories/*.py`

### Ingestion
- `app/ingestion/*.py`

### Prompts
- `app/prompts/*.py`

### Reasoning
- `app/reasoning/*.py`

### Retrieval
- `app/retrieval/*.py`

### Schemas
- `app/schemas/*.py`

### Services
- `app/services/*.py`

### Storage
- `app/storage/*.py`

### Verification
- `app/verification/*.py`

### App bootstrap
- `app/main.py`

### Tests
- `tests/*.py`

## 6.3 Required result
At the end of Phase 0, the following commands should work:

```bash
poetry install
cp .env.example .env
poetry run uvicorn app.main:app --reload
poetry run pytest
```

## 6.4 Extra files to add in Phase 0
Create:

### `scripts/`
New folder to hold utility scripts:
- `scripts/smoke_test.py`
- `scripts/dev_ingest_sample.py`
- `scripts/dev_query_sample.py`

### What each should do

#### `scripts/smoke_test.py`
Run a minimal end-to-end check:
1. initialize app DB,
2. create a sample document metadata record,
3. ingest a local sample file,
4. index chunks,
5. run one retrieval call,
6. run one tutoring call,
7. print success/failure.

#### `scripts/dev_ingest_sample.py`
Allow:
```bash
poetry run python scripts/dev_ingest_sample.py path/to/file.pdf
```

It should:
- read file bytes,
- call `IngestionService.ingest_and_index(...)`,
- print chunk count and document id.

#### `scripts/dev_query_sample.py`
Allow:
```bash
poetry run python scripts/dev_query_sample.py "What is BCNF?"
```

It should:
- construct a `QueryRequest`,
- call `process_chat_query(...)`,
- print answer JSON.

---

## 7. Phase 1 — Finish true document ingestion API

The current API already has document endpoints, but to match the system goal, the backend must support **real file upload**.

## 7.1 New file to create
Create:

- `app/api/routes_upload.py`

## 7.2 Why create a separate route file
Keep responsibilities clean:
- `routes_documents.py` → metadata CRUD
- `routes_upload.py` → file-byte upload + ingestion orchestration

## 7.3 What `routes_upload.py` should contain
Add endpoint:

```text
POST /api/v1/upload/file
```

### Request
Use `UploadFile` + form fields:
- `file: UploadFile`
- `user_id: str`
- `subject: Optional[str]`
- `language: Optional[str]`

### Response
Return:
- document metadata
- chunk count
- maybe first few chunk previews
- ingestion status

## 7.4 Files to modify
- `app/api/__init__.py`  
  include new upload router
- `app/services/ingestion_service.py`  
  ensure service signature cleanly supports API use
- `app/schemas/document.py`  
  add response schema for ingestion summary if needed
- `app/README.md` or root `README.md`  
  document the endpoint

## 7.5 Optional new schema file
Create:
- `app/schemas/ingestion.py`

### Add
- `IngestionResult`
- `IngestionStatus`
- `ChunkPreview`

---

## 8. Phase 2 — Formalize DB migrations

Right now local DB boot can rely on create-all.  
For a 100% complete system, this is not enough.

## 8.1 New files/folders to create

Create:
- `alembic.ini`
- `migrations/`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/0001_initial_schema.py`

## 8.2 What to include in `0001_initial_schema.py`
Create all tables currently needed:
- users
- documents
- chunks
- answers
- citations
- feedback

## 8.3 Later migration files
Reserve future migrations for:
- concept index tables
- relation graph tables
- query/session logs
- evaluation results
- ingestion jobs

## 8.4 Files to modify
- `pyproject.toml`  
  add Alembic if not present
- `README.md`  
  add migration commands

## 8.5 Commands to support
```bash
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "..."
```

---

## 9. Phase 3 — Make retrieval production-grade

Current retrieval is structurally correct but still fallback-heavy.

## 9.1 Split vector store abstraction cleanly

### Current problem
`vector_store.py` is currently carrying the store abstraction itself.

### Better final structure
Create:

- `app/retrieval/base_store.py`
- `app/retrieval/in_memory_store.py`
- `app/retrieval/qdrant_store.py`
- `app/retrieval/store_factory.py`

### Responsibility
- `base_store.py` → abstract interface
- `in_memory_store.py` → local fallback
- `qdrant_store.py` → production vector DB implementation
- `store_factory.py` → choose store based on settings

## 9.2 Sparse retrieval upgrade

### Current limitation
Sparse retrieval is basic lexical weighting.

### Add new file
Create:
- `app/retrieval/bm25_index.py`

### What it should do
- build BM25-like term stats
- score chunks lexically
- support filtering by metadata

### Files to modify
- `app/retrieval/sparse_retriever.py`
- `app/retrieval/sparse_encoder.py`
- `app/services/retrieval_service.py`

## 9.3 Reranker upgrade

### New file
Create:
- `app/retrieval/cross_encoder_reranker.py`

### What it should do
- optionally load a real reranker model
- score `(query, chunk_text)` pairs
- return reranked candidate list

### Keep current fallback
Keep deterministic `reranker.py` as fallback, but make final service able to choose:
- simple reranker,
- cross-encoder reranker.

## 9.4 Evidence building upgrade
Modify:
- `app/retrieval/evidence_builder.py`

### Add stronger fields
Each evidence item should include:
- `document_id`
- `chunk_id`
- `page_start`
- `page_end`
- `text`
- `snippet`
- `score`
- `retrieved_for`
- `retrieval_stage`
- `dense_score`
- `sparse_score`
- `rerank_score`

This is important for later evaluation and debugging.

---

## 10. Phase 4 — Real LLM integration

This is one of the biggest remaining gaps relative to `rag.tex`.

## 10.1 New files to create

Create:

- `app/core/llm_client.py`
- `app/core/llm_types.py`
- `app/core/model_registry.py`

Optional provider-specific split:
- `app/core/providers/openai_client.py`
- `app/core/providers/local_llm_client.py`

## 10.2 What `llm_client.py` should expose
A small interface like:

- `complete(prompt: str, temperature: float = 0.0) -> str`
- `chat(messages: list[dict], temperature: float = 0.0) -> str`
- possibly `complete_json(...)`

## 10.3 Files to modify
- `app/reasoning/query_classifier.py`
- `app/reasoning/query_decomposer.py`
- `app/reasoning/planner.py`
- `app/reasoning/synthesizer.py`
- `app/verification/answer_verifier.py`
- `app/verification/claim_checker.py`

## 10.4 Strategy
Do **not** remove fallback logic.  
Instead, each module should support:

1. real LLM path if configured
2. deterministic fallback if not configured

This keeps local development easy while enabling 100% system completion.

---

## 11. Phase 5 — Stronger reasoning outputs

The final target system should be more than a simple string answer.

## 11.1 New schema additions
Modify or extend:
- `app/schemas/answer.py`
- `app/schemas/query.py`
- possibly create `app/schemas/reasoning.py`

### Add structured outputs
- reasoning trace summary
- cited sentence blocks
- insufficiency notes
- comparison structure
- answer type (fact, explanation, comparison, procedure)

## 11.2 New reasoning files to create
Create:
- `app/reasoning/output_parser.py`
- `app/reasoning/reasoning_trace.py`

### Responsibilities
- `output_parser.py`  
  parse LLM JSON output into typed schemas
- `reasoning_trace.py`  
  represent internal bounded reasoning steps for logging and evaluation

## 11.3 Modify synthesizer
`app/reasoning/synthesizer.py` should eventually:
- take structured evidence,
- build prompt,
- call LLM,
- parse structured JSON output,
- preserve citation alignment,
- refuse unsupported synthesis,
- emit `AnswerResponse`.

---

## 12. Phase 6 — Stronger verification layer

Current verification is good as a fallback, but not enough for the final architecture.

## 12.1 New files to create
Create:

- `app/verification/attribution_checker.py`
- `app/verification/contradiction_checker.py`
- `app/verification/verdict_builder.py`

## 12.2 What each file should do

### `attribution_checker.py`
Check whether each important statement has evidence backing and proper citation mapping.

### `contradiction_checker.py`
Check whether the answer contradicts retrieved evidence.

### `verdict_builder.py`
Combine:
- support status
- contradiction status
- citation completeness
- insufficiency detection

into a final verification verdict.

## 12.3 Files to modify
- `app/verification/answer_verifier.py`
- `app/verification/claim_checker.py`
- `app/services/tutoring_service.py`

## 12.4 Final verification behavior
The final answer flow should be:

1. synthesize draft answer
2. verify support
3. verify attribution
4. verify contradiction
5. either:
   - accept,
   - repair,
   - abstain

This is much closer to the spirit of `rag.tex`.

---

## 13. Phase 7 — Add concept index and relation graph

This is one of the major pieces still missing.

`rag.tex` explicitly goes beyond plain chunk retrieval toward a richer knowledge structure.

## 13.1 New folder to create
Create:

- `app/knowledge/`

## 13.2 New files inside `app/knowledge/`
Create:

- `app/knowledge/__init__.py`
- `app/knowledge/concept_extractor.py`
- `app/knowledge/concept_index.py`
- `app/knowledge/relation_extractor.py`
- `app/knowledge/relation_graph.py`
- `app/knowledge/graph_store.py`

## 13.3 What each file should do

### `concept_extractor.py`
Extract concepts from chunks:
- term
- definition
- aliases
- source document
- chunk origin

### `concept_index.py`
Store and retrieve concepts:
- by exact name
- by alias
- by semantic similarity
- by subject

### `relation_extractor.py`
Extract relationships such as:
- prerequisite
- part-of
- causes
- contrasts-with
- equivalent-to

### `relation_graph.py`
Build graph structure over concepts.

### `graph_store.py`
Persist graph data.
For MVP:
- SQLite tables or JSON graph store
Later:
- Neo4j or graph database if needed

## 13.4 DB/schema changes needed

### Modify / extend schemas
- `app/schemas/concept.py`
- create `app/schemas/graph.py`

### Create DB models
Modify `app/db/models.py` or split into separate model files later to add:
- `concepts`
- `concept_aliases`
- `relations`

### Create repositories
Create:
- `app/db/repositories/concept_repo.py`
- `app/db/repositories/relation_repo.py`

## 13.5 Service integration
Create:
- `app/services/knowledge_service.py`

### Responsibilities
- extract concepts after ingestion
- build/update relation graph
- expose concept lookup to retrieval/reasoning

---

## 14. Phase 8 — Graph-enhanced retrieval

Once concept index and relation graph exist, retrieval should be upgraded.

## 14.1 New file to create
Create:
- `app/retrieval/concept_retriever.py`
- `app/retrieval/graph_retriever.py`

## 14.2 What to retrieve
The final retrieval layer should retrieve from multiple sources:

1. chunk index
2. concept index
3. relation graph neighborhood

## 14.3 Update hybrid retrieval
Modify:
- `app/retrieval/hybrid_retriever.py`

### New hybrid merge inputs
- dense chunk results
- sparse chunk results
- concept hits
- graph neighborhood hits

### Merge logic should consider
- relevance
- support type
- graph distance
- entity overlap

---

## 15. Phase 9 — Better tutoring flow and session-aware behavior

The final system should behave like a tutoring assistant, not only a search engine.

## 15.1 New files to create
Create:

- `app/services/session_service.py`
- `app/services/feedback_service.py`

Optional:
- `app/services/progress_service.py`

## 15.2 DB additions
Add tables for:
- query logs
- session history
- answer history
- user feedback records linked to answers

## 15.3 New API routes
Create:
- `app/api/routes_feedback.py`
- `app/api/routes_sessions.py`

### Endpoints to add
- `POST /api/v1/feedback`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/answers/{answer_id}`

## 15.4 Tutoring-specific improvements
Modify:
- `app/services/tutoring_service.py`

Add logic for:
- follow-up question context resolution
- response style by study mode
- answer summaries
- explanation vs definition vs comparison modes

---

## 16. Phase 10 — Evaluation subsystem

This is a major missing block.

The system cannot be called “complete” relative to `rag.tex` without evaluation.

## 16.1 New folder to create
Create:
- `app/evaluation/`

## 16.2 New files inside
Create:

- `app/evaluation/__init__.py`
- `app/evaluation/retrieval_eval.py`
- `app/evaluation/answer_eval.py`
- `app/evaluation/verification_eval.py`
- `app/evaluation/benchmark_runner.py`

## 16.3 Scripts to create
Create:

- `scripts/run_eval.py`
- `scripts/build_eval_dataset.py`

## 16.4 What to measure

### Retrieval metrics
- Recall@k
- MRR
- nDCG
- filter correctness

### Answer metrics
- support rate
- insufficiency behavior
- citation completeness
- answer relevance

### Verification metrics
- false support rate
- false rejection rate
- contradiction catch rate

## 16.5 Dataset folder to create
Create:

- `evaluation_data/`
- `evaluation_data/questions.jsonl`
- `evaluation_data/gold_evidence.jsonl`
- `evaluation_data/gold_answers.jsonl`

---

## 17. Phase 11 — Observability and debugging infrastructure

To make the system truly maintainable, add observability.

## 17.1 New files to create
Create:
- `app/core/telemetry.py`
- `app/core/request_context.py`

Optional:
- `app/core/tracing.py`

## 17.2 What to log per request
- request id
- session id
- query text
- classification result
- decomposition result
- retrieval filter
- retrieved chunk ids
- rerank order
- synthesized answer
- verification verdict
- latency per stage

## 17.3 Add request correlation
Modify:
- `app/api/routes_chat.py`
- `app/api/routes_search.py`
- `app/services/tutoring_service.py`
- `app/services/retrieval_service.py`

---

## 18. Phase 12 — Deployment hardening

This is the final stage before a “100% complete” release.

## 18.1 Files to create
Create:

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml`

Optional:
- `Makefile`

## 18.2 Environment separation
Extend config to support:
- dev
- test
- prod

Possible file strategy:
- `.env.dev`
- `.env.test`
- `.env.prod`

## 18.3 Production concerns
Add:
- proper secret handling
- health/readiness checks
- structured logging
- exception middleware
- request timeout handling
- input size limits for uploads
- background task support for large ingestions

## 18.4 Optional production dependencies
Later you may add:
- Redis
- Celery / RQ / Dramatiq
- Qdrant production backend
- model-serving layer
- S3/MinIO storage backend

---

## 19. Recommended exact folder/file additions for the final target

Below is the concrete list of **new files/folders** that should be added to reach the final system shape.

## 19.1 New folders
Create:
- `app/knowledge/`
- `app/evaluation/`
- `scripts/`
- `migrations/`
- `evaluation_data/`

## 19.2 New API files
Create:
- `app/api/routes_upload.py`
- `app/api/routes_feedback.py`
- `app/api/routes_sessions.py`

## 19.3 New schema files
Create:
- `app/schemas/ingestion.py`
- `app/schemas/graph.py`
- `app/schemas/reasoning.py`
- `app/schemas/evaluation.py`

## 19.4 New DB repository files
Create:
- `app/db/repositories/concept_repo.py`
- `app/db/repositories/relation_repo.py`
- `app/db/repositories/query_log_repo.py`
- `app/db/repositories/session_repo.py`
- `app/db/repositories/citation_repo.py`

## 19.5 New knowledge files
Create:
- `app/knowledge/concept_extractor.py`
- `app/knowledge/concept_index.py`
- `app/knowledge/relation_extractor.py`
- `app/knowledge/relation_graph.py`
- `app/knowledge/graph_store.py`

## 19.6 New retrieval files
Create:
- `app/retrieval/base_store.py`
- `app/retrieval/in_memory_store.py`
- `app/retrieval/qdrant_store.py`
- `app/retrieval/store_factory.py`
- `app/retrieval/bm25_index.py`
- `app/retrieval/concept_retriever.py`
- `app/retrieval/graph_retriever.py`
- `app/retrieval/cross_encoder_reranker.py`

## 19.7 New reasoning files
Create:
- `app/reasoning/output_parser.py`
- `app/reasoning/reasoning_trace.py`

## 19.8 New verification files
Create:
- `app/verification/attribution_checker.py`
- `app/verification/contradiction_checker.py`
- `app/verification/verdict_builder.py`

## 19.9 New service files
Create:
- `app/services/knowledge_service.py`
- `app/services/feedback_service.py`
- `app/services/session_service.py`
- `app/services/evaluation_service.py`

## 19.10 New evaluation files
Create:
- `app/evaluation/retrieval_eval.py`
- `app/evaluation/answer_eval.py`
- `app/evaluation/verification_eval.py`
- `app/evaluation/benchmark_runner.py`

## 19.11 New scripts
Create:
- `scripts/smoke_test.py`
- `scripts/dev_ingest_sample.py`
- `scripts/dev_query_sample.py`
- `scripts/run_eval.py`
- `scripts/build_eval_dataset.py`
- `scripts/reindex_all.py`

## 19.12 Migration files
Create:
- `alembic.ini`
- `migrations/env.py`
- `migrations/script.py.mako`
- `migrations/versions/0001_initial_schema.py`

---

## 20. Recommended execution order by week / milestone

This section converts the completion plan into a realistic build order.

## Milestone A — Stable runnable MVP
### Do first
1. finalize current files
2. make all tests pass
3. ensure app boots
4. ensure retrieval works locally
5. ensure tutoring flow works locally

## Milestone B — True ingestion and persistence
### Do next
1. add binary upload endpoint
2. connect API upload to ingestion service
3. persist doc + chunks properly
4. add smoke-test scripts

## Milestone C — Production retrieval
### Do next
1. split vector store implementations
2. add BM25-style sparse retrieval
3. add real reranker option
4. improve evidence builder metadata

## Milestone D — Real LLM reasoning
### Do next
1. add LLM client abstraction
2. switch classifier / decomposer / planner / synthesizer to provider-backed execution
3. keep deterministic fallback

## Milestone E — Strong verification
### Do next
1. add attribution checker
2. add contradiction checker
3. build final verdict merger
4. enforce abstention/repair path

## Milestone F — Knowledge layer
### Do next
1. add concept extraction
2. add concept index
3. add relation graph
4. add graph-aware retrieval

## Milestone G — Evaluation
### Do next
1. create evaluation dataset
2. add retrieval benchmarks
3. add answer/verification benchmarks
4. add benchmark runner scripts

## Milestone H — Release hardening
### Do last
1. add migrations
2. add Docker
3. add prod config
4. add observability
5. add deployment docs

---

## 21. Minimal “definition of done” for the final 100% system

The system can be considered complete relative to `rag.tex` when all of the following are true:

### Ingestion
- file upload works through API
- PDF/DOCX/PPTX parsing works reliably
- normalization preserves useful structure
- chunk metadata includes document/chunk/page traceability
- ingestion persists document/chunk data
- concept extraction runs after ingestion

### Retrieval
- dense retrieval works
- sparse retrieval works
- hybrid retrieval works
- reranking works
- metadata filtering works
- vector backend can run both locally and in production
- concept/graph retrieval is integrated

### Reasoning
- query classification works
- decomposition works
- bounded planning works
- synthesis uses only evidence
- citations are attached correctly
- unsupported claims are not emitted

### Verification
- answer support is checked
- claim support is checked
- attribution is checked
- contradiction is checked
- abstention path exists

### Evaluation
- retrieval quality is measurable
- answer quality is measurable
- verification quality is measurable
- benchmark scripts exist
- results can be reproduced

### Product/Operations
- app boots cleanly
- tests pass
- migrations work
- upload/query/search routes are documented
- logs and tracing are useful
- local dev workflow is simple
- production deployment path exists

---

## 22. Final practical recommendation

If the goal is to reach the final `rag.tex` vision efficiently, the best path is:

### Step 1
Lock the current reviewed codebase into a clean runnable baseline.

### Step 2
Make the document upload route truly ingest file bytes end to end.

### Step 3
Add migrations and production-grade retrieval plumbing.

### Step 4
Integrate real LLM execution while preserving fallback logic.

### Step 5
Build concept index + relation graph only after retrieval/reasoning/verification are stable.

### Step 6
Finish with evaluation, observability, and deployment.

This order is the safest way to avoid building advanced features on top of an unstable base.

---

## 23. Short final summary

### Already achieved
- strong modular project skeleton
- API/core/db/ingestion/retrieval/reasoning/verification separation
- runnable MVP direction
- document parsing + chunking path
- retrieval pipeline structure
- reasoning pipeline structure
- verification stage presence
- schemas and services foundation
- local storage and tests foundation

### Still needed for 100%
- true upload API
- migrations
- production vector backend
- real sparse retrieval
- real reranker
- real LLM integration
- concept index
- relation graph
- graph-aware retrieval
- evaluation subsystem
- feedback/session extensions
- deployment hardening

### Engineering truth
The project is already **well beyond an empty skeleton**, but it is still in the **MVP-to-full-system transition stage**.  
The remaining work is substantial, but the architecture is already good enough that this work can now be done systematically rather than by rewriting the repository from scratch.
