# Architecture Decision Records

Short records of significant tool choices and places where custom code was chosen over a
library, with the reasoning at the time. Numbered in the order they were written, not
necessarily the order the decisions matter.

- [0001: Dependabot Over Renovate](0001-dependabot-over-renovate.md)
- [0002: Docling For Document Parsing](0002-docling-for-parsing.md)
- [0003: Dex Groups Claim Carries Tenant And Group](0003-dex-groups-claim-for-tenant-and-group.md)
- [0004: Psycopg Is An Accepted LGPL Exception](0004-psycopg-lgpl-dependency.md)
- [0005: Separate Database Role For The Running App](0005-separate-app-db-role-for-append-only-audit-log.md)
- [0006: One Postgres Instance, Two Databases](0006-shared-postgres-instance-for-openfga.md)
- [0007: Tenant Isolation Is Structural In The OpenFGA Model](0007-structural-tenant-isolation-in-openfga-model.md)
- [0008: Custom Code For The Audit Writer, No Library](0008-custom-audit-writer-instead-of-a-library.md)
- [0009: Pin Torch And Torchvision To CPU-Only Wheels](0009-cpu-only-torch-wheels.md)
- [0010: Ollama For The Local LLM And Embedding Provider](0010-ollama-for-local-llm.md)
