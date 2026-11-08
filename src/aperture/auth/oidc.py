"""OIDC token validation against the local Dex instance, using Authlib.

Tokens are validated for signature, issuer, audience and expiry. The JWKS
is fetched from Dex and cached; call clear cache if keys are rotated.
"""

from functools import lru_cache

import httpx
from authlib.jose import JsonWebKey, JWTClaims, KeySet, jwt
from authlib.jose.errors import JoseError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aperture.auth.models import CurrentUser
from aperture.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=True)


@lru_cache
def _get_jwks() -> KeySet:
    settings = get_settings()
    response = httpx.get(settings.oidc.jwks_url, timeout=5.0)
    response.raise_for_status()
    return JsonWebKey.import_key_set(response.json())


def clear_jwks_cache() -> None:
    """Drop the cached JWKS, for example after a signing key rotation."""

    _get_jwks.cache_clear()


def _parse_groups_claim(groups: list[str]) -> tuple[str, list[str]]:
    """Split the token's "groups" claim into (tenant_id, group_names).

    See deploy/dex/config.yaml for the "tenant:<id>" / "group:<name>"
    convention this expects.
    """

    tenant_ids = [g.removeprefix("tenant:") for g in groups if g.startswith("tenant:")]
    group_names = [g.removeprefix("group:") for g in groups if g.startswith("group:")]

    if len(tenant_ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token must carry exactly one tenant membership.",
        )

    return tenant_ids[0], group_names


def _claims_to_user(claims: JWTClaims) -> CurrentUser:
    tenant_id, groups = _parse_groups_claim(claims.get("groups", []))
    return CurrentUser(
        subject=claims["sub"],
        email=claims.get("email"),
        tenant_id=tenant_id,
        groups=groups,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    """FastAPI dependency that validates the bearer token against Dex and
    returns the resolved identity.
    """

    settings = get_settings()
    claims_options = {
        "iss": {"essential": True, "values": [settings.oidc.issuer]},
        "aud": {"essential": True, "values": [settings.oidc.audience]},
    }

    try:
        claims = jwt.decode(
            credentials.credentials,
            _get_jwks(),
            claims_options=claims_options,
        )
        claims.validate()
    except JoseError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    return _claims_to_user(claims)
