"""Seed script for the local OpenFGA instance.

Creates (or reuses) a store named "aperture", writes the authorization model
from model.json, and writes relationship tuples for the three demo users,
their tenants and groups, and a handful of sample documents.

Run with: uv run python deploy/openfga/seed.py
Requires the OpenFGA server from docker compose to be reachable.

The resulting store_id and authorization_model_id are printed so they can be
copied into .env (APERTURE_OPENFGA_STORE_ID / APERTURE_OPENFGA_AUTHORIZATION_MODEL_ID).
"""

import asyncio
import json
from pathlib import Path

from openfga_sdk import ClientConfiguration, OpenFgaClient
from openfga_sdk.client.models import ClientTuple, ClientWriteRequest

STORE_NAME = "aperture"
MODEL_PATH = Path(__file__).parent / "model.json"

# Demo users, as seeded into Dex: alice and bob are in tenant "acme",
# carol is in tenant "globex". Groups are tenant scoped (acme-finance and
# globex-finance are different group objects) so tenant isolation holds even
# when two groups share the same display name.
TENANTS = ["acme", "globex"]

GROUP_MEMBERS = {
    "acme-finance": ["alice"],
    "acme-engineering": ["bob"],
    "globex-finance": ["carol"],
}

TENANT_MEMBERS = {
    "acme": ["alice", "bob"],
    "globex": ["carol"],
}

# Sample documents: (document_id, tenant, direct_viewers, viewer_groups)
DOCUMENTS = [
    ("doc-acme-finance-policy", "acme", [], ["acme-finance"]),
    ("doc-acme-eng-handbook", "acme", [], ["acme-engineering"]),
    ("doc-acme-alice-private", "acme", ["alice"], []),
    ("doc-globex-finance-policy", "globex", [], ["globex-finance"]),
]


async def get_or_create_store(client: OpenFgaClient) -> str:
    stores = await client.list_stores()
    for store in stores.stores or []:
        if store.name == STORE_NAME:
            return store.id
    created = await client.create_store(body={"name": STORE_NAME})
    return created.id


async def write_authorization_model(client: OpenFgaClient) -> str:
    model = json.loads(MODEL_PATH.read_text())
    response = await client.write_authorization_model(body=model)
    return response.authorization_model_id


def build_tuples() -> list[ClientTuple]:
    tuples: list[ClientTuple] = []

    for tenant, users in TENANT_MEMBERS.items():
        for user in users:
            tuples.append(
                ClientTuple(user=f"user:{user}", relation="member", object=f"tenant:{tenant}")
            )

    for group, users in GROUP_MEMBERS.items():
        for user in users:
            tuples.append(
                ClientTuple(user=f"user:{user}", relation="member", object=f"group:{group}")
            )

    for document_id, tenant, direct_viewers, viewer_groups in DOCUMENTS:
        tuples.append(
            ClientTuple(
                user=f"tenant:{tenant}", relation="tenant", object=f"document:{document_id}"
            )
        )
        for user in direct_viewers:
            tuples.append(
                ClientTuple(
                    user=f"user:{user}",
                    relation="direct_viewer",
                    object=f"document:{document_id}",
                )
            )
        for group in viewer_groups:
            tuples.append(
                ClientTuple(
                    user=f"group:{group}#member",
                    relation="group_viewer",
                    object=f"document:{document_id}",
                )
            )

    return tuples


async def main() -> None:
    configuration = ClientConfiguration(api_url="http://localhost:8080")
    async with OpenFgaClient(configuration) as client:
        store_id = await get_or_create_store(client)
        client.set_store_id(store_id)

        model_id = await write_authorization_model(client)
        client.set_authorization_model_id(model_id)

        await client.write(ClientWriteRequest(writes=build_tuples()))

        print(f"APERTURE_OPENFGA_STORE_ID={store_id}")
        print(f"APERTURE_OPENFGA_AUTHORIZATION_MODEL_ID={model_id}")


if __name__ == "__main__":
    asyncio.run(main())
