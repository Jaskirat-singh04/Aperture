"""Permission-aware retrieval.

Not implemented yet. This module documents the intended flow so the
permission boundary is clear before any retrieval code is written:

1. Resolve the set of document IDs the asking user may read, BEFORE any
   vector search runs:
   a. Call OpenFGA's ListObjects (or equivalent batched Check calls) for
      relation "can_view", type "document", user "user:<subject>".
   b. OpenFGA itself enforces tenant isolation (see deploy/openfga/model.fga,
      can_view requires both viewer access and tenant membership), so the
      returned document IDs are already scoped to the caller's tenant.
2. Restrict the LlamaIndex / pgvector query to that exact set of document
   IDs, using a metadata filter (document_id IN [...]) passed to the
   pgvector vector store query, not a post-filter applied after retrieval.
   Chunks are never fetched for documents outside the allowed set.
3. Return the matching chunks with their source document IDs, so the
   generation step can cite only documents the user is allowed to read.

The permission check in step 1 must complete, and the resulting document ID
list must be non-empty-or-explicitly-empty, before step 2 runs. Retrieval
must never run against the full, unfiltered document set.
"""

from dataclasses import dataclass

from aperture.auth.models import CurrentUser


@dataclass
class RetrievedChunk:
    """A chunk returned from a permission-filtered retrieval query."""

    document_id: str
    text: str
    score: float


class RetrievalService:
    """Stub. See module docstring for the intended flow."""

    async def list_permitted_document_ids(self, user: CurrentUser) -> list[str]:
        """Return the document IDs `user` may read, via OpenFGA ListObjects.

        TODO: call the OpenFGA client's list_objects with
        type="document", relation="can_view", user=f"user:{user.subject}".
        """

        raise NotImplementedError("Permission-aware retrieval is not implemented yet.")

    async def retrieve(self, user: CurrentUser, question: str) -> list[RetrievedChunk]:
        """Retrieve chunks for `question`, restricted to documents `user`
        may read and to `user`'s tenant.

        TODO: call list_permitted_document_ids first, then query the
        LlamaIndex pgvector store with a metadata filter on document_id
        (and tenant_id as a second, redundant filter) before any chunk is
        returned.
        """

        raise NotImplementedError("Permission-aware retrieval is not implemented yet.")
