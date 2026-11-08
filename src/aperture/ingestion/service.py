"""Document ingestion.

Not implemented yet. Intended flow:

1. Pull source documents from a connector (Google Drive, a file share, ...)
   along with whatever access control information the source exposes
   (sharing lists, ACL entries, folder permissions).
2. Parse each document with Docling (see docs/adr/0002-docling-for-parsing.md
   for why Docling over Unstructured).
3. Chunk and embed with LlamaIndex, writing to the pgvector store managed by
   LlamaIndex's PGVectorStore integration. Every chunk's metadata must
   include tenant_id and document_id, retrieval filters on these fields.
4. Write a row to the `documents` table (source, title, uri) and translate
   the source's access control information into OpenFGA relationship
   tuples (direct_viewer / group_viewer / tenant), using deploy/openfga/
   seed.py as a reference for the tuple shapes.

Permissions must be recorded before the document's chunks become visible to
retrieval, an ingested-but-not-yet-authorized document must not be
retrievable by anyone.
"""

from dataclasses import dataclass


@dataclass
class IngestResult:
    """Outcome of ingesting one source document."""

    document_id: str
    chunk_count: int


class IngestionService:
    """Stub. See module docstring for the intended flow."""

    async def ingest_document(self, source_uri: str, tenant_id: str) -> IngestResult:
        """Parse, chunk, embed and authorize one source document.

        TODO: implement using Docling for parsing and LlamaIndex for
        chunking, embedding and pgvector storage, then write the
        corresponding OpenFGA tuples before returning.
        """

        raise NotImplementedError("Document ingestion is not implemented yet.")
