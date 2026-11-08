"""create tenants documents audit_log

Revision ID: 73cda59484c1
Revises:
Create Date: 2026-11-08 14:11:48.297937

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "73cda59484c1"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The least-privilege role the running application connects as. Created by
# deploy/postgres/init.sh. Distinct from the migration/owner role because
# Postgres table owners bypass GRANT/REVOKE checks, so audit_log can only be
# made append-only for a role that is not the owner.
APP_ROLE = "aperture_app"


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("uri", sa.String(), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", sa.String(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("document_ids_used", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_log_tenant_id", "audit_log", ["tenant_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])

    # gen_random_uuid() lives in pgcrypto on older Postgres, pgvector's base
    # image ships Postgres 16 where it is built in, this is a safety net.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Grant the app role the privileges it needs, and nothing more.
    # tenants and documents are regular read/write tables for the app.
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO "{APP_ROLE}"')
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO "{APP_ROLE}"')

    # audit_log is append-only: the app role may read and insert, never
    # update or delete. REVOKE is explicit here even though UPDATE/DELETE
    # were never granted, so the intent is clear and the statement is a
    # no-op (not an error) if grants ever change.
    op.execute(f'GRANT SELECT, INSERT ON audit_log TO "{APP_ROLE}"')
    op.execute(f'REVOKE UPDATE, DELETE ON audit_log FROM "{APP_ROLE}"')


def downgrade() -> None:
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_tenant_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_documents_tenant_id", table_name="documents")
    op.drop_table("documents")

    op.drop_table("tenants")
