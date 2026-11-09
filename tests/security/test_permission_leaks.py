"""Permission-leak tests. This is a release gate: the target is zero leaks.

These run against the live docker compose stack (Postgres, OpenFGA, Ollama),
not mocks, because the whole point is to catch a real leak in the real
retrieval and generation path. Each test ingests fresh documents as one
user and asserts another user cannot retrieve or be answered from them.

Requires `make up`, migrations applied (`uv run alembic upgrade head`) and
OpenFGA seeded (`uv run python deploy/openfga/seed.py`). The
"permission-leak-tests" CI job runs exactly this file.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from aperture.auth.models import CurrentUser
from aperture.config import get_settings
from aperture.generation import GenerationService
from aperture.ingestion import IngestionService
from aperture.retrieval import RetrievalService

pytestmark = pytest.mark.security

ALICE = CurrentUser(subject="alice", tenant_id="acme", groups=["finance"])
BOB = CurrentUser(subject="bob", tenant_id="acme", groups=["engineering"])
CAROL = CurrentUser(subject="carol", tenant_id="globex", groups=["finance"])

# Distinctive text so a leak would be unmistakable if it surfaced.
SECRET_TEXT = (
    "The acme finance quarterly bonus multiplier is seven point three "
    "for every employee in the finance organization."
)


@pytest.fixture(autouse=True)
def _fresh_vector_store_per_loop():
    """LlamaIndex's PGVectorStore holds an asyncpg pool bound to the event
    loop it was first used on. pytest-asyncio gives each test its own loop,
    so the lru_cache would hand back a store tied to a closed loop. Clear
    the per-process caches around each test, this is a test-isolation
    concern only, the API runs on a single long-lived loop.
    """

    from aperture import vector_store
    from aperture.auth import openfga_client

    vector_store.get_vector_store.cache_clear()
    vector_store.get_embed_model.cache_clear()
    openfga_client.clear_resolved_ids_cache()
    yield
    vector_store.get_vector_store.cache_clear()
    vector_store.get_embed_model.cache_clear()


@pytest.fixture
def session():
    engine = create_engine(get_settings().database.app_sqlalchemy_url)
    with Session(engine) as s:
        yield s


async def _ingest_as(session, user: CurrentUser, **kwargs) -> str:
    service = IngestionService(session)
    result = await service.ingest_text(
        tenant_id=user.tenant_id,
        title=f"leak-test-{uuid.uuid4().hex[:8]}",
        text=SECRET_TEXT,
        **kwargs,
    )
    session.commit()
    return result.document_id


async def test_cross_tenant_retrieval_returns_nothing(session) -> None:
    """A user in tenant globex must never retrieve an acme document, even
    for a question whose wording matches it closely.
    """

    doc_id = await _ingest_as(session, ALICE, viewer_groups=["finance"])

    chunks = await RetrievalService().retrieve(CAROL, "quarterly bonus multiplier")

    assert all(c.document_id != doc_id for c in chunks)


async def test_user_without_document_access_gets_no_chunks_from_it(session) -> None:
    """Bob (same tenant, different group, no grant) must get zero chunks
    from a finance-only document.
    """

    doc_id = await _ingest_as(session, ALICE, viewer_groups=["finance"])

    chunks = await RetrievalService().retrieve(BOB, "quarterly bonus multiplier")

    assert all(c.document_id != doc_id for c in chunks)


async def test_answer_never_cites_a_document_the_user_cannot_read(session) -> None:
    """The generated answer for a user without access must not cite the
    document, and must not leak its distinctive content.
    """

    await _ingest_as(session, ALICE, viewer_groups=["finance"])

    chunks = await RetrievalService().retrieve(BOB, "quarterly bonus multiplier")
    answer = await GenerationService().generate("quarterly bonus multiplier", chunks)

    assert answer.cited_document_ids == []
    assert "seven point three" not in answer.text.lower()


async def test_owner_can_retrieve_their_own_document(session) -> None:
    """Sanity check the leak tests above are meaningful: the authorized
    user (alice, finance) does retrieve the document the others cannot.
    """

    doc_id = await _ingest_as(session, ALICE, viewer_groups=["finance"])

    chunks = await RetrievalService().retrieve(ALICE, "quarterly bonus multiplier")

    assert any(c.document_id == doc_id for c in chunks)
