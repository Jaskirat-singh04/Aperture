"""Tenant row bookkeeping.

Tenants are not provisioned through a separate admin flow yet (there is no
user/tenant management story beyond Dex's seeded demo users), so tenant
rows are created lazily the first time they are referenced, by ingestion
(a document's FK) or by the audit writer (an audit record's FK). The name
defaults to the tenant_id itself.
"""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from aperture.audit.models import Tenant


def ensure_tenant_exists(session: Session, tenant_id: str) -> None:
    """Upsert a tenants row (no-op if it already exists), so foreign keys
    that reference it are satisfied. Does not commit.
    """

    stmt = (
        pg_insert(Tenant)
        .values(id=tenant_id, name=tenant_id)
        .on_conflict_do_nothing(index_elements=["id"])
    )
    session.execute(stmt)
