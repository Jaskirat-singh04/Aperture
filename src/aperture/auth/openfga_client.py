"""Shared OpenFGA client, used by retrieval (permission checks) and
ingestion (writing permission tuples for a newly ingested document).

store_id and authorization_model_id are resolved lazily if not set in
config: deploy/openfga/seed.py is the only thing that creates the store
and authorization model, there is no separate "deployment" step that
would know their IDs ahead of time, so this looks them up by the same
store name the seed script uses, and caches the result in-process.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from openfga_sdk import ClientConfiguration, OpenFgaClient

from aperture.config import get_settings

STORE_NAME = "aperture"

_cached_ids: tuple[str, str] | None = None
_cache_lock = asyncio.Lock()


async def _resolve_ids() -> tuple[str, str]:
    """Return (store_id, authorization_model_id), from config if both are
    set, otherwise looked up from the running OpenFGA server and cached.
    """

    global _cached_ids

    settings = get_settings().openfga
    if settings.store_id and settings.authorization_model_id:
        return settings.store_id, settings.authorization_model_id

    if _cached_ids is not None:
        return _cached_ids

    async with _cache_lock:
        if _cached_ids is not None:
            return _cached_ids

        configuration = ClientConfiguration(api_url=settings.api_url)
        async with OpenFgaClient(configuration) as client:
            store_id = settings.store_id
            if not store_id:
                stores = await client.list_stores()
                matches = [s.id for s in stores.stores or [] if s.name == STORE_NAME]
                if not matches:
                    raise RuntimeError(
                        f'No OpenFGA store named "{STORE_NAME}" found, '
                        "run deploy/openfga/seed.py first."
                    )
                store_id = matches[0]

            model_id = settings.authorization_model_id
            if not model_id:
                client.set_store_id(store_id)
                models = await client.read_authorization_models()
                if not models.authorization_models:
                    raise RuntimeError(
                        f'OpenFGA store "{STORE_NAME}" has no authorization model, '
                        "run deploy/openfga/seed.py first."
                    )
                # OpenFGA returns authorization models newest first.
                model_id = models.authorization_models[0].id

        _cached_ids = (store_id, model_id)
        return _cached_ids


def clear_resolved_ids_cache() -> None:
    """Drop the cached store/model IDs, for example in tests."""

    global _cached_ids
    _cached_ids = None


@asynccontextmanager
async def get_openfga_client() -> AsyncIterator[OpenFgaClient]:
    settings = get_settings().openfga
    store_id, model_id = await _resolve_ids()
    configuration = ClientConfiguration(
        api_url=settings.api_url,
        store_id=store_id,
        authorization_model_id=model_id,
    )
    async with OpenFgaClient(configuration) as client:
        yield client
