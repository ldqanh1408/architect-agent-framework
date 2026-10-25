# Reproduce and extend the current core

Use Python 3.12 and the checked-in lock for the verified local profile:

```bash
uv sync --frozen --all-extras
npm ci
uv run --frozen playwright install chromium
uv run --frozen pytest -q --runslow
npm run check:console
uv run --frozen ruff check architect_framework scripts tests vendor/sdd-agent/sdd_core
```

The public fixture kit in `tests/_sdd_fixture.py` and `examples/core-payments` contains synthetic source facts and authorities. No real key, provider credential or paid body is needed for core correctness tests. Read each explicit exclusion in `tests/fixture-exclusions.json`; an exclusion is incomplete qualification. Original paid bodies and independent human studies have separate ownership.

For a new predicate, add a registered typed check to a public fixture, show its clean control, mutate the intended business fact and assert the targeted diagnostic. Also assert that checking does not write a baseline or alter source. Start with `tests/core_engine/test_final_boundaries.py`.

For a runtime change, start with `tests/test_cutover_parity.py` and `tests/test_runtime_harness.py`. Exercise the actual launcher or MCP transport, exact revisions and forbidden side effects. Preserve stale and failed outcomes; do not turn retries or timeouts into approval.

For a UI change, read `design-system/aaf-workbench/MASTER.md`, build the committed JavaScript with `npm run build:console`, then run the browser tests with `ARCHITECT_REQUIRE_UX=1`. Check keyboard access, focus during polling, mobile width, both themes and exact-revision document reads. Independent participant studies remain separately recorded.

For package changes, build a new public directory with `scripts/build_public_tree.py`, build wheel and sdist there with `scripts/build_dist.py`, scan the actual archives with `scripts/check_release_artifacts.py`, and install outside the checkout with `scripts/smoke_wheel_install.py`. Rebuild a wheel from the sdist too. Artifact edits invalidate earlier artifact evidence.

The source plan and assurance index retain requirement ownership. Use one canonical contract source and regenerate mirrors. Avoid bringing retired writers or phase ledgers back as compatibility aliases. Human signature, acceptance and publication authority remain outside agent tooling.
