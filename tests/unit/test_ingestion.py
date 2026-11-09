"""Unit tests for ingestion, with the vector store, embedding model and
OpenFGA mocked out. See tests/integration for the real-stack version.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

from aperture.ingestion.service import IngestionService


def _fake_openfga_client():
    client = MagicMock()
    client.write = AsyncMock()

    @asynccontextmanager
    async def _ctx():
        yield client

    return _ctx, client


def _patch_common(monkeypatch):
    embed_model = MagicMock()
    embed_model.aget_text_embedding = AsyncMock(return_value=[0.1, 0.2])
    monkeypatch.setattr("aperture.ingestion.service.get_embed_model", lambda: embed_model)

    vector_store = MagicMock()
    vector_store.async_add = AsyncMock()
    monkeypatch.setattr("aperture.ingestion.service.get_vector_store", lambda: vector_store)

    ctx, client = _fake_openfga_client()
    monkeypatch.setattr("aperture.ingestion.service.get_openfga_client", ctx)

    return vector_store, client


async def test_ingest_text_writes_document_row_and_chunks(monkeypatch) -> None:
    vector_store, _ = _patch_common(monkeypatch)
    session = MagicMock()
    service = IngestionService(session)

    result = await service.ingest_text(
        tenant_id="acme", title="Refund Policy", text="Refunds within 30 days. " * 50
    )

    assert result.document_id.startswith("doc-")
    assert result.chunk_count > 0
    vector_store.async_add.assert_awaited_once()
    session.add.assert_called_once()
    added_row = session.add.call_args[0][0]
    assert added_row.tenant_id == "acme"
    assert added_row.title == "Refund Policy"
    assert added_row.id == result.document_id


async def test_ingest_text_writes_tenant_and_viewer_tuples(monkeypatch) -> None:
    _, client = _patch_common(monkeypatch)
    service = IngestionService(MagicMock())

    result = await service.ingest_text(
        tenant_id="acme",
        title="t",
        text="short document",
        direct_viewers=["bob"],
        viewer_groups=["finance"],
    )

    client.write.assert_awaited_once()
    (write_request,), _ = client.write.call_args
    written = {(t.user, t.relation, t.object) for t in write_request.writes}
    document_object = f"document:{result.document_id}"
    assert ("tenant:acme", "tenant", document_object) in written
    assert ("user:bob", "direct_viewer", document_object) in written
    assert ("group:acme-finance#member", "group_viewer", document_object) in written


async def test_ingest_text_embeds_every_chunk_before_storing(monkeypatch) -> None:
    embed_model = MagicMock()
    embed_model.aget_text_embedding = AsyncMock(return_value=[0.1, 0.2])
    monkeypatch.setattr("aperture.ingestion.service.get_embed_model", lambda: embed_model)

    vector_store = MagicMock()
    vector_store.async_add = AsyncMock()
    monkeypatch.setattr("aperture.ingestion.service.get_vector_store", lambda: vector_store)

    ctx, _ = _fake_openfga_client()
    monkeypatch.setattr("aperture.ingestion.service.get_openfga_client", ctx)

    service = IngestionService(MagicMock())
    result = await service.ingest_text(
        tenant_id="acme", title="t", text="Refunds within 30 days. " * 50
    )

    assert embed_model.aget_text_embedding.await_count == result.chunk_count
    (added_nodes,), _ = vector_store.async_add.call_args
    assert all(node.embedding == [0.1, 0.2] for node in added_nodes)
    assert all(node.metadata["tenant_id"] == "acme" for node in added_nodes)
