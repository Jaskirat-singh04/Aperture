"""Unit tests for the audit writer, using a stand-in session (no DB)."""

from unittest.mock import MagicMock

from aperture.audit.writer import record_query


def test_record_query_builds_expected_audit_log_entry() -> None:
    session = MagicMock()

    entry = record_query(
        session,
        tenant_id="acme",
        user_id="alice",
        question="What is our refund policy?",
        document_ids_used=["doc-acme-finance-policy"],
    )

    assert entry.tenant_id == "acme"
    assert entry.user_id == "alice"
    assert entry.question == "What is our refund policy?"
    assert entry.document_ids_used == ["doc-acme-finance-policy"]
    session.add.assert_called_once_with(entry)
    session.flush.assert_called_once()


def test_record_query_does_not_commit() -> None:
    """record_query must not commit, the caller owns the transaction."""

    session = MagicMock()
    record_query(
        session,
        tenant_id="acme",
        user_id="bob",
        question="q",
        document_ids_used=[],
    )
    session.commit.assert_not_called()
