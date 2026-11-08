## What And Why

<!-- What does this change, and why is it needed? -->

## How To Verify

<!-- Commands or steps a reviewer can run to check this works. -->

## Checklist

- [ ] `make lint` passes
- [ ] `make test` passes
- [ ] If a dependency changed: `uv.lock` is updated and
      `uv run python scripts/check_licenses.py` passes
- [ ] If this touches `tests/security/`: the PR description explains which leak scenario is
      covered
- [ ] Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
