"""Append-only audit logging.

This is plain glue around the audit_log table (see
aperture.audit.models.AuditLog and the initial Alembic migration, which
revokes UPDATE and DELETE on this table for the application's database
role). There is no business logic here, every query the API serves must
call record_query with the user, tenant, question and document IDs used.
"""

from sqlalchemy.orm import Session

from aperture.audit.models import AuditLog


def record_query(
    session: Session,
    *,
    tenant_id: str,
    user_id: str,
    question: str,
    document_ids_used: list[str],
) -> AuditLog:
    """Insert one append-only audit record and return it.

    Does not commit, callers control the transaction boundary (for example
    committing together with other work in the same request).
    """

    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        question=question,
        document_ids_used=document_ids_used,
    )
    session.add(entry)
    session.flush()
    return entry
