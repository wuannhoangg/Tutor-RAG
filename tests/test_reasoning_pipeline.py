import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.query import QueryRequest
from app.services.tutoring_service import process_chat_query


class StubRetrievalService:
    def retrieve_and_build_evidence(self, query, filters=None, top_k=5):
        return [
            {
                "document_id": "doc_readme",
                "chunk_id": "chunk_1",
                "text": "The primary goal of the RAG backend is to provide grounded answers based only on personal study materials.",
                "page_start": 1,
                "page_end": 1,
                "metadata": {"document_id": "doc_readme", "chunk_id": "chunk_1", "page_start": 1, "page_end": 1},
                "score": 0.95,
            },
            {
                "document_id": "doc_readme",
                "chunk_id": "chunk_2",
                "text": "If evidence is insufficient, the system must explicitly say the material is insufficient.",
                "page_start": 2,
                "page_end": 2,
                "metadata": {"document_id": "doc_readme", "chunk_id": "chunk_2", "page_start": 2, "page_end": 2},
                "score": 0.9,
            },
        ]


@pytest.mark.asyncio
async def test_process_chat_query_factoid():
    req = QueryRequest(
        query_text="What is the primary goal of the RAG backend?",
        user_id="user_1",
        subject_hint="rag",
    )

    result = await process_chat_query(
        query_request=req,
        retrieval_service=StubRetrievalService(),
    )

    assert result["query"] == "What is the primary goal of the RAG backend?"
    assert result["classification"]["label"] in {"FACTUAL_QA", "DECOMPOSITION_REQUIRED"}
    assert "answer" in result
    assert result["answer"]["answer_text"]


def test_chat_endpoint_success(monkeypatch):
    async def fake_process_chat_query(*args, **kwargs):
        return {
            "query": "What is BCNF?",
            "classification": {"label": "FACTUAL_QA", "reason": "Single focused question."},
            "sub_questions": [],
            "plan": [{"step": 1, "action": "retrieve"}],
            "evidence": [],
            "answer": {"answer_text": "BCNF is a stricter normal form."},
            "verification": {"is_supported": True, "reasoning": "Supported.", "corrected_answer": "BCNF is a stricter normal form."},
        }

    monkeypatch.setattr("app.api.routes_chat.process_chat_query", fake_process_chat_query)

    client = TestClient(app)
    response = client.post(
        "/api/v1/chat/ask",
        json={
            "question": "What is BCNF?",
            "user_id": "user_1",
            "chat_history": [],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["answer"]["answer_text"] == "BCNF is a stricter normal form."