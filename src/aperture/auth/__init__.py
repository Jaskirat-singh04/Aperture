"""Authentication (OIDC via Dex) and identity types."""

from aperture.auth.models import CurrentUser
from aperture.auth.oidc import get_current_user

__all__ = ["CurrentUser", "get_current_user"]
