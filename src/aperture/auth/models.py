"""Identity types shared across the auth and retrieval packages."""

from pydantic import BaseModel


class CurrentUser(BaseModel):
    """The authenticated caller, resolved from a validated OIDC token.

    tenant_id and groups are read from the token's "groups" claim, using the
    convention documented in deploy/dex/config.yaml: a single "tenant:<id>"
    entry and zero or more "group:<name>" entries.
    """

    subject: str
    email: str | None = None
    tenant_id: str
    groups: list[str] = []

    def openfga_group_ids(self) -> list[str]:
        """Group identifiers as used in OpenFGA tuples, for example
        "acme-finance" for a user in tenant "acme" and group "finance".
        """

        return [f"{self.tenant_id}-{group}" for group in self.groups]
