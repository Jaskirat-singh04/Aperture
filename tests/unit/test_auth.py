"""Unit tests for OIDC token validation and identity parsing."""

import time

import pytest
from authlib.jose import JsonWebKey, jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from aperture.auth import oidc
from aperture.config import get_settings


@pytest.fixture
def signing_key():
    return JsonWebKey.generate_key("RSA", 2048, is_private=True, options={"kid": "test-kid"})


def _make_token(signing_key, groups: list[str], **overrides) -> str:
    settings = get_settings()
    payload = {
        "iss": settings.oidc.issuer,
        "aud": settings.oidc.audience,
        "sub": "alice",
        "email": "alice@acme.test",
        "exp": int(time.time()) + 300,
        "groups": groups,
        **overrides,
    }
    header = {"alg": "RS256", "kid": "test-kid"}
    return jwt.encode(header, payload, signing_key).decode("utf-8")


def test_parse_groups_claim_splits_tenant_and_groups() -> None:
    tenant_id, groups = oidc._parse_groups_claim(["tenant:acme", "group:finance"])
    assert tenant_id == "acme"
    assert groups == ["finance"]


def test_parse_groups_claim_requires_exactly_one_tenant() -> None:
    with pytest.raises(HTTPException):
        oidc._parse_groups_claim(["group:finance"])
    with pytest.raises(HTTPException):
        oidc._parse_groups_claim(["tenant:acme", "tenant:globex"])


async def test_get_current_user_accepts_valid_token(signing_key, monkeypatch) -> None:
    public_jwk = signing_key.as_dict(is_private=False)
    keyset = JsonWebKey.import_key_set({"keys": [public_jwk]})
    monkeypatch.setattr(oidc, "_get_jwks", lambda: keyset)

    token = _make_token(signing_key, groups=["tenant:acme", "group:finance"])
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    user = await oidc.get_current_user(credentials)

    assert user.subject == "alice"
    assert user.tenant_id == "acme"
    assert user.groups == ["finance"]
    assert user.openfga_group_ids() == ["acme-finance"]


async def test_get_current_user_rejects_expired_token(signing_key, monkeypatch) -> None:
    public_jwk = signing_key.as_dict(is_private=False)
    keyset = JsonWebKey.import_key_set({"keys": [public_jwk]})
    monkeypatch.setattr(oidc, "_get_jwks", lambda: keyset)

    token = _make_token(signing_key, groups=["tenant:acme"], exp=int(time.time()) - 10)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await oidc.get_current_user(credentials)
    assert exc_info.value.status_code == 401


async def test_get_current_user_rejects_wrong_audience(signing_key, monkeypatch) -> None:
    public_jwk = signing_key.as_dict(is_private=False)
    keyset = JsonWebKey.import_key_set({"keys": [public_jwk]})
    monkeypatch.setattr(oidc, "_get_jwks", lambda: keyset)

    token = _make_token(signing_key, groups=["tenant:acme"], aud="someone-else")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await oidc.get_current_user(credentials)
    assert exc_info.value.status_code == 401
