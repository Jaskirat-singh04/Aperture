"""Permission-aware retrieval.

Permissions are resolved before any chunk is fetched, see
docs/adr/0007-structural-tenant-isolation-in-openfga-model.md:

1. Resolve the set of document IDs the asking user may read via OpenFGA's
   ListObjects for relation "can_view", type "document". OpenFGA itself
   enforces tenant isolation (can_view requires both viewer access and
   tenant membership), so the returned IDs are already tenant-scoped.
2. If that set is empty, return no chunks, the vector store is never
   queried. Otherwise restrict the pgvector query to exactly that set of
   document IDs (a metadata filter, not a post-filter), plus the user's
   tenant_id as a second, redundant filter.
"""

from dataclasses import dataclass

from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
)
from openfga_sdk.client.models import ClientListObjectsRequest

from aperture.auth.models import CurrentUser
from aperture.auth.openfga_client import get_openfga_client
from aperture.vector_store import get_embed_model, get_vector_store

DEFAULT_TOP_K = 5


@dataclass
class RetrievedChunk:
    """A chunk returned from a permission-filtered retrieval query."""

    document_id: str
    text: str
    score: float


class RetrievalService:
    async def list_permitted_document_ids(self, user: CurrentUser) -> list[str]:
        """Document IDs `user` may read, via OpenFGA's ListObjects."""

        async with get_openfga_client() as client:
            response = await client.list_objects(
                ClientListObjectsRequest(
                    user=f"user:{user.subject}",
                    relation="can_view",
                    type="document",
                )
            )
        return [obj.removeprefix("document:") for obj in response.objects or []]

    async def retrieve(
        self, user: CurrentUser, question: str, top_k: int = DEFAULT_TOP_K
    ) -> list[RetrievedChunk]:
        """Retrieve chunks for `question`, restricted to documents `user`
        may read and to `user`'s tenant. Returns an empty list, without
        querying the vector store at all, if `user` may read nothing.
        """

        permitted_ids = await self.list_permitted_document_ids(user)
        if not permitted_ids:
            return []

        embed_model = get_embed_model()
        query_embedding = await embed_model.aget_query_embedding(question)

        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="document_id", value=permitted_ids, operator=FilterOperator.IN),
                MetadataFilter(key="tenant_id", value=user.tenant_id, operator=FilterOperator.EQ),
            ]
        )
        query = VectorStoreQuery(
            query_embedding=query_embedding, similarity_top_k=top_k, filters=filters
        )

        result = await get_vector_store().aquery(query)
        similarities = result.similarities or [0.0] * len(result.nodes or [])
        return [
            RetrievedChunk(
                # ref_doc_id, not node.metadata["document_id"]: ingestion
                # sets id_=document_id on the source Document (see
                # IngestionService._ingest), the vector store's own
                # (de)serialization reconstructs ref_doc_id from that and
                # strips document_id back out of the plain metadata dict.
                document_id=node.ref_doc_id or "",
                text=node.get_content(),
                score=score,
            )
            for node, score in zip(result.nodes or [], similarities, strict=False)
        ]
