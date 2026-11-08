"""Database engine and session helpers for runtime application code.

Alembic migrations connect as the owner role directly (see alembic/env.py),
this module is for the running application, which always connects as the
least-privilege "aperture_app" role.
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from aperture.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database.app_sqlalchemy_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine())


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped session."""

    session_factory = get_sessionmaker()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
