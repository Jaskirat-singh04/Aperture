"""Document ingestion: parse, chunk, embed, store, and authorize.

Flow, see docs/adr/0002-docling-for-parsing.md and
docs/adr/0007-structural-tenant-isolation-in-openfga-model.md for why the
parsing and authorization pieces look the way they do:

1. Parse the source into plain text. Plain text input is used as-is,
   file input goes through Docling.
2. Chunk with a LlamaIndex SentenceSplitter and embed each chunk with the
   configured (LiteLLM) embedding model. Every chunk's metadata carries
   tenant_id and document_id, retrieval filters on exactly these fields.
3. Write a row to the `documents` table (source, title, uri).
4. Write OpenFGA tuples for this document: exactly one `tenant` tuple, plus
   a `direct_viewer` tuple per given user and a `group_viewer` tuple per
   given group. A document is not retrievable by anyone until this step
   completes, permissions are recorded as part of ingestion, not after it.
"""

import io
import uuid
from dataclasses import dataclass

from llama_index.core import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from openfga_sdk.client.models import ClientTuple, ClientWriteRequest
from sqlalchemy.orm import Session

from aperture.audit.models import Document as DocumentRow
from aperture.audit.tenants import ensure_tenant_exists
from aperture.auth.openfga_client import get_openfga_client
from aperture.vector_store import get_embed_model, get_vector_store

_CHUNK_SIZE = 512
_CHUNK_OVERLAP = 50


@dataclass
class IngestResult:
    """Outcome of ingesting one source document."""

    document_id: str
    chunk_count: int


class IngestionService:
    def __init__(self, session: Session):
        self._session = session

    async def ingest_text(
        self,
        *,
        tenant_id: str,
        title: str,
        text: str,
        source: str = "manual",
        uri: str | None = None,
        direct_viewers: list[str] | None = None,
        viewer_groups: list[str] | None = None,
    ) -> IngestResult:
        """Ingest already-extracted plain text (no parsing step)."""

        return await self._ingest(
            tenant_id=tenant_id,
            title=title,
            text=text,
            source=source,
            uri=uri or f"manual://{title}",
            direct_viewers=direct_viewers or [],
            viewer_groups=viewer_groups or [],
        )

    async def ingest_file(
        self,
        *,
        tenant_id: str,
        title: str,
        filename: str,
        content: bytes,
        direct_viewers: list[str] | None = None,
        viewer_groups: list[str] | None = None,
    ) -> IngestResult:
        """Ingest a file (PDF, DOCX, HTML, ...), parsed with Docling."""

        # Imported lazily, Docling pulls in torch and is slow to import,
        # no need to pay that cost for ingest_text-only callers.
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(DocumentStream(name=filename, stream=io.BytesIO(content)))
        text = result.document.export_to_markdown()

        return await self._ingest(
            tenant_id=tenant_id,
            title=title,
            text=text,
            source="upload",
            uri=f"upload://{filename}",
            direct_viewers=direct_viewers or [],
            viewer_groups=viewer_groups or [],
        )

    async def _ingest(
        self,
        *,
        tenant_id: str,
        title: str,
        text: str,
        source: str,
        uri: str,
        direct_viewers: list[str],
        viewer_groups: list[str],
    ) -> IngestResult:
        document_id = f"doc-{uuid.uuid4().hex[:12]}"

        # id_=document_id (not a "document_id" metadata key) is deliberate:
        # LlamaIndex's own node metadata serialization already writes a
        # top-level "document_id" key derived from the source Document's
        # id_ (aliasing doc_id/ref_doc_id), setting id_ here makes that
        # key equal to our document_id instead of colliding with it (a
        # custom "document_id" metadata entry would silently be
        # overwritten by LlamaIndex's own alias of the same name).
        llama_doc = LlamaDocument(
            id_=document_id,
            text=text,
            metadata={"tenant_id": tenant_id},
        )
        splitter = SentenceSplitter(chunk_size=_CHUNK_SIZE, chunk_overlap=_CHUNK_OVERLAP)
        nodes = splitter.get_nodes_from_documents([llama_doc])

        embed_model = get_embed_model()
        for node in nodes:
            node.embedding = await embed_model.aget_text_embedding(node.get_content())

        if nodes:
            await get_vector_store().async_add(nodes)

        ensure_tenant_exists(self._session, tenant_id)
        self._session.add(
            DocumentRow(id=document_id, tenant_id=tenant_id, source=source, title=title, uri=uri)
        )
        self._session.flush()

        await self._write_permission_tuples(
            document_id=document_id,
            tenant_id=tenant_id,
            direct_viewers=direct_viewers,
            viewer_groups=viewer_groups,
        )

        return IngestResult(document_id=document_id, chunk_count=len(nodes))

    async def _write_permission_tuples(
        self,
        *,
        document_id: str,
        tenant_id: str,
        direct_viewers: list[str],
        viewer_groups: list[str],
    ) -> None:
        document_object = f"document:{document_id}"
        tuples = [
            ClientTuple(user=f"tenant:{tenant_id}", relation="tenant", object=document_object)
        ]
        for user in direct_viewers:
            tuples.append(
                ClientTuple(user=f"user:{user}", relation="direct_viewer", object=document_object)
            )
        for group in viewer_groups:
            # Group ids are tenant-scoped, see CurrentUser.openfga_group_ids
            # and docs/adr/0003-dex-groups-claim-for-tenant-and-group.md.
            group_object = f"group:{tenant_id}-{group}#member"
            tuples.append(
                ClientTuple(user=group_object, relation="group_viewer", object=document_object)
            )

        async with get_openfga_client() as client:
            await client.write(ClientWriteRequest(writes=tuples))
