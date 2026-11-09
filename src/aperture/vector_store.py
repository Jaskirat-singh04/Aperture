"""Shared LlamaIndex pgvector store and LiteLLM-backed models.

Ingestion writes nodes here, retrieval queries it. The table itself is
created and managed entirely by LlamaIndex's PGVectorStore (not Alembic),
the app's database role has schema-level CREATE for exactly this reason,
see deploy/postgres/init.sh.
"""

from functools import lru_cache

from llama_index.embeddings.litellm import LiteLLMEmbedding
from llama_index.llms.litellm import LiteLLM
from llama_index.vector_stores.postgres import PGVectorStore

from aperture.config import get_settings


@lru_cache
def get_vector_store() -> PGVectorStore:
    """The pgvector-backed chunk store, connected as the app's own
    least-privilege database role (see DatabaseSettings.app_sqlalchemy_url
    for the SQLAlchemy equivalent used by the rest of the app).
    """

    settings = get_settings()
    db = settings.database
    return PGVectorStore.from_params(
        host=db.host,
        port=str(db.port),
        database=db.name,
        user=db.app_user,
        password=db.app_password,
        table_name="chunks",
        embed_dim=settings.llm.embedding_dimension,
        use_jsonb=True,
    )


@lru_cache
def get_embed_model() -> LiteLLMEmbedding:
    settings = get_settings().llm
    return LiteLLMEmbedding(
        model_name=settings.embedding_model,
        api_base=settings.api_base,
        api_key=settings.api_key,
        dimensions=settings.embedding_dimension,
    )


@lru_cache
def get_llm() -> LiteLLM:
    settings = get_settings().llm
    return LiteLLM(model=settings.model, api_base=settings.api_base, api_key=settings.api_key)
