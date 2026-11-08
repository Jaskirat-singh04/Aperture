# 0001: Dependabot Over Renovate

## Status

Accepted.

## Context

The project needs automated dependency update pull requests, for Python (uv), GitHub
Actions and Docker base images. Both Renovate and Dependabot can do this.

## Decision

Use Dependabot (`.github/dependabot.yml`), not Renovate.

Dependabot is built into GitHub, needs no third-party app installation or separate
configuration host, and natively supports the `uv` ecosystem. Renovate is more
configurable (grouping, scheduling, changelog formatting), but that configurability is
more than a solo-maintained, early-stage project needs right now, and it is one more
moving part to maintain.

## Consequences

Less configuration surface, at the cost of Renovate's richer grouping and scheduling
options. If PR volume or grouping needs become a problem later, revisit this.
