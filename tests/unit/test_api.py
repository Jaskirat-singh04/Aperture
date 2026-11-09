"""Unit tests for the FastAPI app.

/ingest and /ask are tested with the ingestion/retrieval/generation
services mocked out, these are unit tests for the API layer (routing,
auth, request/response shapes, audit logging), not the services
themselves (see test_ingestion.py, test_retrieval.py, test_generation.py)
or the full stack (see tests/integration).
"""

import time
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from authlib.jose import JsonWebKey, jwt
from fastapi.testclient import TestClient

from aperture.api.main import app
from aperture.auth import oidc
from aperture.config import get_settings
from aperture.db import get_session
from aperture.generation import Answer
from aperture.ingestion import IngestResult
from aperture.retrieval import RetrievedChunk


@pytest.fixture
def signing_key():
    return JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "test-kid"})


@pytest.fixture(autouse=True)
def _patch_jwks(signing_key, monkeypatch):
    keyset = JsonWebKey.import_key_set({"keys": [signing_key.as_dict(is_private=False)]})
    monkeypatch.setattr(oidc, "_get_jwks", lambda: keyset)


def _auth_header(signing_key, *, subject: str = "alice", groups: list[str] | None = None) -> dict:
    settings = get_settings()
    payload = {
        "iss": settings.oidc.issuer,
        "aud": settings.oidc.audience,
        "sub": subject,
        "exp": int(time.time()) + 300,
        "groups": groups or ["tenant:acme", "group:finance"],
    }
    token = jwt.encode({"alg": "RS256", "kid": "test-kid"}, payload, signing_key).decode("utf-8")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fake_session() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(fake_session: MagicMock) -> Iterator[TestClient]:
    app.dependency_overrides[get_session] = lambda: fake_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_requires_authentication(client: TestClient) -> None:
    response = client.post("/ingest", json={"title": "t", "text": "hello"})
    assert response.status_code == 401  # no Authorization header at all


def test_ask_requires_authentication(client: TestClient) -> None:
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 401  # no Authorization header at all


def test_ingest_calls_ingestion_service_with_callers_tenant(
    client: TestClient, signing_key, monkeypatch, fake_session: MagicMock
) -> None:
    mock_ingest_text = AsyncMock(return_value=IngestResult(document_id="doc-1", chunk_count=3))
    monkeypatch.setattr(
        "aperture.api.main.IngestionService.ingest_text",
        mock_ingest_text,
    )

    response = client.post(
        "/ingest",
        json={"title": "Refund Policy", "text": "...", "direct_viewers": ["bob"]},
        headers=_auth_header(signing_key),
    )

    assert response.status_code == 200
    assert response.json() == {"document_id": "doc-1", "chunk_count": 3}
    mock_ingest_text.assert_awaited_once()
    _, kwargs = mock_ingest_text.call_args
    assert kwargs["tenant_id"] == "acme"  # from the token, not request input
    assert kwargs["direct_viewers"] == ["bob"]
    fake_session.commit.assert_called_once()


def test_ask_returns_answer_and_writes_audit_log(
    client: TestClient, signing_key, monkeypatch, fake_session: MagicMock
) -> None:
    chunks = [RetrievedChunk(document_id="doc-1", text="refunds within 30 days", score=0.9)]
    monkeypatch.setattr(
        "aperture.api.main.RetrievalService.retrieve", AsyncMock(return_value=chunks)
    )
    monkeypatch.setattr(
        "aperture.api.main.GenerationService.generate",
        AsyncMock(return_value=Answer(text="30 days [doc-1]", cited_document_ids=["doc-1"])),
    )

    response = client.post(
        "/ask", json={"question": "refund policy?"}, headers=_auth_header(signing_key)
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "30 days [doc-1]", "cited_document_ids": ["doc-1"]}
    fake_session.add.assert_called_once()
    added_entry = fake_session.add.call_args[0][0]
    assert added_entry.tenant_id == "acme"
    assert added_entry.user_id == "alice"
    assert added_entry.document_ids_used == ["doc-1"]
    fake_session.commit.assert_called_once()


def test_ask_with_no_permitted_chunks_cites_nothing(
    client: TestClient, signing_key, monkeypatch, fake_session: MagicMock
) -> None:
    monkeypatch.setattr("aperture.api.main.RetrievalService.retrieve", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "aperture.api.main.GenerationService.generate",
        AsyncMock(return_value=Answer(text="I don't know.", cited_document_ids=[])),
    )

    response = client.post(
        "/ask", json={"question": "anything?"}, headers=_auth_header(signing_key)
    )

    assert response.status_code == 200
    assert response.json()["cited_document_ids"] == []
