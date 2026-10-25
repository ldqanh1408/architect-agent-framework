# Contribute to the current candidate

Candidate: 2.0.0. Release status: NOT_QUALIFIED.

Declare each special fixture with an explicit pytest marker and a record in
`tests/fixture-exclusions.json`. Each record needs an owner, a reason, and
`qualification_when_excluded: INCOMPLETE`. A comment or a filename does not select
an exclusion. Preserve critical invariants in public synthetic fixtures.

To refresh the declared register, run the writer below and review its diff. This
command collects tests only. It does not run or qualify them.

```bash
PYTHONPATH=tests .venv/bin/python -m pytest --collect-only -q -p _fixture_register_collector --fixture-register-maintenance
```

Use a synthetic workspace for a bug report. Include the command, version, profile, expected result, and actual result. Remove secrets and private source text.

## Set up and check

```bash
uv sync --locked --all-extras
npm ci --ignore-scripts
npm run build:console
.venv/bin/ruff check architect_framework scripts tests vendor/sdd-agent/sdd_core
```

Public fixtures live in `tests/_sdd_fixture.py` and `tests/core_engine/`. The shared fixture module supports child processes. `ContractFixtureJudge` checks contracts and transport; it does not measure semantic model quality.

Run the current core cohort:

```bash
.venv/bin/python -m pytest tests/core_engine tests/test_core_runs.py tests/test_core_dispatch.py tests/test_run_gate_signatures.py tests/test_sdd_integration.py tests/test_workspace_migration.py tests/test_workflow_contracts.py tests/test_judge_facade.py tests/test_label_review.py tests/test_document_style.py
```

Run current browser QA after you install the declared browser:

```bash
.venv/bin/python -m playwright install chromium --only-shell
ARCHITECT_REQUIRE_UX=1 .venv/bin/python -m pytest tests/test_workbench_browser.py
```

Synthetic workers and virtual keys do not qualify live hosts or physical devices. The full repository suite and its slow generation checks remain required integration checks.

## Edit canonical sources

| Change | Source | Check |
|---|---|---|
| Foundation contracts | `contracts/foundation-workflows/` | `scripts/compile_foundation_contracts.py --check` |
| Foundation instructions | Vendor skill and required references | `scripts/build_plugin_skills.py --check` |
| Workbench | `console/ts/workbench.ts` | TypeScript build and browser QA |
| Signed review UI | `console/static/sdd-console.js` and `manual-evidence.js` | Browser review and acceptance journey |
| Scheduling | `runtime/core_runs.py` | Dependency, lease, corruption, and signature cases |
| Provider facade | `sdd_core/adapters/` | Evidence, budget, cancellation, and fallback cases |

The contract compiler preserves authored instructions. Rebuild projections after changing a canonical source. Keep generated files current in the same change.

## Preserve authority

Keep grants, dispatch, semantic review, acceptance, and publication separate. A candidate cannot grant itself broader authority. Only configured people sign human decisions.

Test stale source, revoked trust, duplicate operations, expired leases, cancellation, and failed dependencies when the change affects them. Check that a refused operation preserves user bytes.

Use explicit bounded model configuration for live evaluation. Two names in a label file do not establish independent human evidence. Normal tests must not call a live provider.

## Remove legacy code

Run `python scripts/audit_legacy.py --report docs/legacy-inventory.json`. The declared inventory covers LEG-01 through LEG-12. Its failure blocks release.

Port useful invariants before deleting code, prompts, contracts, assets, or old test APIs. Record each replacement in `docs/public-core-oracle-port.json` or the applicable parity map. A skipped predicate is not PASS.

After deletion, rebuild and inspect the public source, wheel, sdist, and host bundles. Keep old readers in the separate migration path. Do not remove correctness assertions to make the suite green.

## Write a reviewable change

Explain the concrete trigger and resulting behavior. Record actual checks, incomplete evidence, and support limits. Link the affected case and work order.

Write short technical sentences. Keep one instruction per sentence where practical. Preserve IDs, values, units, links, code, normative words, negation, and UNKNOWN. Bounded language repair still needs human review.
