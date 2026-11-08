"""Integration tests that audit_log is really append-only at the database
level, for the role the application connects as (not the migration owner).

Requires the docker compose Postgres with migrations applied, see
deploy/docker-compose.yml and `make up`.
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from aperture.config import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture
def app_session():
    settings = get_settings()
    engine = create_engine(settings.database.app_sqlalchemy_url)
    with Session(engine) as session:
        yield session


@pytest.fixture
def seeded_tenant(app_session):
    app_session.execute(
        text(
            "INSERT INTO tenants (id, name) VALUES ('test-tenant', 'Test Tenant') "
            "ON CONFLICT (id) DO NOTHING"
        )
    )
    app_session.commit()
    return "test-tenant"


def test_app_role_can_insert_audit_log(app_session, seeded_tenant) -> None:
    app_session.execute(
        text(
            "INSERT INTO audit_log (tenant_id, user_id, question, document_ids_used) "
            "VALUES (:tenant_id, 'alice', 'q', '[]'::jsonb)"
        ),
        {"tenant_id": seeded_tenant},
    )
    app_session.commit()


def test_app_role_cannot_update_audit_log(app_session, seeded_tenant) -> None:
    app_session.execute(
        text(
            "INSERT INTO audit_log (tenant_id, user_id, question, document_ids_used) "
            "VALUES (:tenant_id, 'alice', 'q', '[]'::jsonb)"
        ),
        {"tenant_id": seeded_tenant},
    )
    app_session.commit()

    with pytest.raises(DBAPIError, match="permission denied"):
        app_session.execute(text("UPDATE audit_log SET question = 'tampered'"))
        app_session.commit()
    app_session.rollback()


def test_app_role_cannot_delete_audit_log(app_session, seeded_tenant) -> None:
    with pytest.raises(DBAPIError, match="permission denied"):
        app_session.execute(text("DELETE FROM audit_log"))
        app_session.commit()
    app_session.rollback()
