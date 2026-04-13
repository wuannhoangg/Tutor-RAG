---
title: Tutor Rag Backend
emoji: 📉
colorFrom: gray
colorTo: blue
sdk: docker
pinned: false
license: apache-2.0
short_description: backend for tutor rag system
---


# TutorRAG Backend

TutorRAG Backend is a Docker-based FastAPI service for grounded Retrieval-Augmented Generation (RAG) over personal study materials.

This Space hosts the **backend only**.

## What this backend does
- accepts authenticated requests
- ingests uploaded documents
- parses PDF / DOCX / PPTX
- normalizes and chunks text
- indexes chunks for retrieval
- runs retrieval + reranking
- synthesizes grounded answers
- verifies answer support

## Runtime
- SDK: Docker
- Port: 7860
- App entrypoint: `app.main:app`

## Important notes

### Free hardware
This Space can run on Hugging Face free CPU hardware for initial testing.

### Persistent file storage
By default, free Spaces only provide **non-persistent** disk.
If you want uploaded files to survive restarts/rebuilds, mount a **Storage Bucket**.

### Recommended mount path
If you want to keep the current backend code unchanged, mount your bucket to:

```text
/code/local_storage
```

because the current backend saves uploaded files into `local_storage/` by default.

### Environment variables
Set backend secrets in **Space Settings → Variables and secrets**.

Typical variables:
- `API_V1_STR`
- `SECRET_KEY`
- `LOG_LEVEL`
- `LOG_DIR`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_JWT_SECRET`
- `SUPABASE_ANON_KEY`
- `PLATFORM_LLM_PROVIDER`
- `PLATFORM_LLM_API_KEY`
- `PLATFORM_LLM_MODEL`
- `PLATFORM_LLM_BASE_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME`
- `BACKEND_CORS_ORIGINS`
- `AUTO_CREATE_TABLES`

## Recommended deployment order
1. Push this backend code to the Space.
2. Add all required Variables/Secrets.
3. Start the Space and confirm `/api/v1/health/` works.
4. Connect the frontend to this backend URL.
5. Only then decide whether to mount a persistent bucket.
