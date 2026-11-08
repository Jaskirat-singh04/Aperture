"""Unit tests for the FastAPI app: health check and stub endpoint auth."""

import time

import pytest
from authlib.jose import JsonWebKey, jwt
from fastapi.testclient import TestClient

from aperture.api.main import app
from aperture.auth import oidc
from aperture.config import get_settings


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_requires_authentication(client: TestClient) -> None:
    response = client.post("/ingest", json={"source_uri": "gdrive://doc-1"})
    assert response.status_code == 401  # no Authorization header at all


def test_ask_requires_authentication(client: TestClient) -> None:
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 401  # no Authorization header at all


def test_ask_returns_501_for_authenticated_user(client: TestClient, monkeypatch) -> None:
    signing_key = JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "test-kid"})
    keyset = JsonWebKey.import_key_set({"keys": [signing_key.as_dict(is_private=False)]})
    monkeypatch.setattr(oidc, "_get_jwks", lambda: keyset)

    settings = get_settings()
    payload = {
        "iss": settings.oidc.issuer,
        "aud": settings.oidc.audience,
        "sub": "alice",
        "exp": int(time.time()) + 300,
        "groups": ["tenant:acme", "group:finance"],
    }
    token = jwt.encode({"alg": "RS256", "kid": "test-kid"}, payload, signing_key).decode("utf-8")

    response = client.post(
        "/ask",
        json={"question": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 501
