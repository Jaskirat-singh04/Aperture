"""Permission-leak tests. This is a release gate: the target is zero leaks.

These tests are skipped until retrieval and generation are implemented
(see aperture.retrieval.service and aperture.generation.service). Each one
describes a specific leak that must never happen, they are not placeholders
for "someday", they are the acceptance criteria for those modules.

The "permission-leak-tests" CI job (.github/workflows/ci.yml) runs this
file specifically and must pass before release, once these tests are
un-skipped and passing, that job becomes a real gate rather than a no-op.
"""

import pytest

pytestmark = pytest.mark.security


@pytest.mark.skip(reason="Retrieval is not implemented yet, see aperture.retrieval.service")
async def test_cross_tenant_retrieval_returns_nothing() -> None:
    """A user in tenant A must never retrieve tenant B's documents, even
    for a question whose wording matches tenant B content closely.

    Expected behavior once implemented:
    - Seed a document only in tenant "globex" (for example via
      deploy/openfga/seed.py's doc-globex-finance-policy).
    - Ask the same question as a user in tenant "acme" (for example bob).
    - Assert the retrieved chunks list is empty, not just that the final
      answer "happens" to omit it. Retrieval itself must not read any
      globex chunk for an acme user, per the model in
      deploy/openfga/model.fga (can_view requires tenant membership).
    """


@pytest.mark.skip(reason="Retrieval is not implemented yet, see aperture.retrieval.service")
async def test_user_without_document_access_gets_no_chunks_from_it() -> None:
    """A user who is not a direct_viewer or group_viewer on a document must
    get zero chunks from that document, even within their own tenant.

    Expected behavior once implemented:
    - Seed doc-acme-alice-private as direct_viewer-only for alice.
    - Ask a question as bob (same tenant, no access to this document).
    - Assert none of the retrieved chunks have
      document_id == "doc-acme-alice-private".
    """


@pytest.mark.skip(
    reason="Retrieval and generation are not implemented yet, "
    "see aperture.retrieval.service and aperture.generation.service"
)
async def test_answer_never_cites_a_document_the_user_cannot_read() -> None:
    """The final generated answer's citations must be a subset of the
    document IDs that were permission-filtered into retrieval, never a
    document the asking user is not permitted to read.

    Expected behavior once implemented:
    - Ask a question as a user with access to some, not all, matching
      documents.
    - Assert every cited document ID in the answer is in the set of
      document IDs retrieval returned for that user, and that set itself
      only contains documents OpenFGA's can_view allowed.
    """
