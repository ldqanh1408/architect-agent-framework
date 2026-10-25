---
checklist_id: CK-P1-system-architect-001
generated_by: scripts/build_checklist.py
generated_at: 2026-08-07T09:05:00Z
phase: 1
role: orchestrator
workspace: <workspace>
skill: 01-system-architect
upstream: { phase: 0, draft: "requirement-intent-draft.md v3", clarified: clarified-requirements.md }
status: in_progress
---
# Checklist — Phase 1 · `01-system-architect` (orchestrator)

**Created before the architect writes anything**, and before any module is delegated. The architect
owns the global layer; every delegated module then gets its own checklist
([`CHECKLIST-phase1-backend-service-architect.md`](CHECKLIST-phase1-backend-service-architect.md) is
the sample).

`run_sdd_phase.py --phase 1 --postflight` refuses to close while any row is `todo`/`doing`, or any
`blocked`/`n-a` row lacks an owner and a reason.

---

## A. Inherit the high-level view from Phase 0

The clarifier's draft is the **only** licensed source of business intent. Everything the architect
writes must trace to it — an architecture that introduces a user, a scenario, or a feature the draft
never mentioned has invented a requirement.

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-A1 | The Phase-0 draft is **confirmed** by the user (not v1-unconfirmed) | inspect `requirement-intent-draft.md` front matter | done | `v3 · confirmed 2026-08-06T16:40Z` |
| CK-SA-A2 | Every draft field is carried into a Phase-1 artifact — none dropped | `python vendor/sdd-agent/scripts/check_requirement_fidelity.py <ws> --from requirement-intent-draft.md` | done | 14/14 fields mapped; table below |
| CK-SA-A3 | Every clause of the brief has a coverage-ledger row ending in `Covered by REQ-xxx` \| `Deferred` \| `GAP` | `python vendor/sdd-agent/scripts/check_requirement_fidelity.py <ws> --phase 1` | done | 24 CLR → 21 covered · 2 deferred · 1 GAP |
| CK-SA-A4 | A ledger with **no GAP anywhere** is treated as suspect, not as success | manual review + `vendor/sdd-agent/scripts/check_audit_honesty.py` | done | 1 GAP present (CLR-019 offline mode) — healthy |
| CK-SA-A5 | The four draft layers each produced at least one architecture artifact | `python scripts/check_layer_coverage.py <ws>` | done | see mapping |

**The Phase-0 → Phase-1 mapping this row asserts** — each draft field lands somewhere specific:

| Phase-0 draft field | Phase-1 artifact it becomes |
|---|---|
| Software goal & core value | `01-global-strategy/00-context/problem-brief.md` |
| Target users (profiles) | `00-system-views/00-viewpoints/stakeholder-concern-matrix.md` · C1 actors |
| Typical usage scenarios | `00-system-views/06-runtime/SCN-*.md` · C1/C2 primary path |
| Core features (by priority) | `01-requirements/requirements.md` (REQ-xxx) · the MVP cut in `document-tree-plan.md` |
| Differentiating highlights | `02-strategy/solution-strategy.md` |
| Business flow | `00-system-views/c2-container.md` edges · `source-map.yml` relations |
| Content / data sources | `_shared-contracts/01-data/**` |
| Platform form | `02-strategy/technology-selection.md` (an ADR, not an assertion) |
| Budget range | `04-delivery/00-planning/**` — recorded as an **expectation**, never as a constraint the design silently obeys |
| Expected delivery time | `04-delivery/00-planning/roadmap.md` horizon |
| Region | `03-cross-cutting/02-security/**` compliance prompts |
| User's concerns | `04-risks/risk-register.md` |
| Success criteria | `01-requirements/quality-attributes.md` → `QA-{NNN}` scenarios |
| Materials still needed | `source-ingestion-ledger.yml` with status `new` / `partial` |

## B. Plan the tree before writing into it

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-B1 | `document-tree-plan.md` selects the **smallest sufficient** tree for the evidence | `python vendor/sdd-agent/scripts/check_target_document_tree_plan.py <ws>` | done | level=standard · 31 slots selected of 65 |
| CK-SA-B2 | The plan is validated, approved, and in `executing` state before any architecture write | same | done | `state=executing · sha256 9c1d…` |
| CK-SA-B3 | Every omitted slot has a one-line reason; no empty optional folders were scaffolded | `… --explain-skips` | done | 34 omitted, 34 reasons |
| CK-SA-B4 | The workspace obeys the per-skill templates, not a central taxonomy | `python vendor/sdd-agent/scripts/check_workspace_template.py <ws>` | done | **P-4/B-3 closed 2026-08-08.** `check_workspace_template.py` canonical mode → `check_workspace_template.py PASSED`; the legacy `<NN>-<slug>` marker and `CHILD_SKILLS` constant are gone, and per-skill manifests (110 domain packages) assert `<cluster>/<skill>` (B-2). |

## C. Author the global layer (never delegated)

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-C1 | `01-global-strategy/**` — problem, goals, requirements, constraints, quality attributes, strategy, principles, technology, risks, ADRs | `python vendor/sdd-agent/run_hooks.py --check-workspace-all <ws> --phase 1` | done | 15 pages |
| CK-SA-C2 | `_shared-contracts/**` — one owner per cross-module contract | same | done | 2 contracts |
| CK-SA-C3 | `03-cross-cutting/**` — a concern lands here only if **more than one module depends on it behaving identically** | same | done | 1 mechanism, 4 dependents named |
| CK-SA-C4 | `metamodel.md` written as the prose face of `correspondence_rules.yaml`, not a second list | `python -m architect_framework.orchestrator.consistency_checker --selftest` | done | **G-3 closed 2026-08-08.** `01-system-architect/references/design/metamodel.md` is the prose face of `architect_framework/data/correspondence_rules.yaml` (16 rules); the page carries 18 `CR-` references, all resolving. `consistency_checker --selftest` exit 0. |
| CK-SA-C5 | Every page carries the 4-part spine | `python exported_skills/_shared/scripts/check_output_docs.py <ws>/architecture` | done | **E-1 closed 2026-08-08.** Burn-down landed in `examples/spine-a/documents/`; `check_output_docs.py <spine-a>/architecture` → `PASSED: 3 pages`, `--strict` → `PASSED: 3 pages`, exit 0. QuickCart stays frozen at its 168-finding baseline. |

## D. Decide the modules — and let the router pick their owners

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-D1 | Every module in the charter traces to draft evidence (a CLR id or a quoted scenario) | `python vendor/sdd-agent/scripts/check_module_charter.py <ws>` | done | 2 modules · 2 evidence rows |
| CK-SA-D2 | The charter is **evidence-bounded** — no module exists because the category "usually has one" | manual + `vendor/sdd-agent/scripts/check_module_charter.py --cap` | done | cap=2, both evidenced |
| CK-SA-D3 | For each module the router returned `selected`; the owner is an **exported skill** | `route.py route --query "<slug + evidence>"` per module | done | `backend-service-architect`, `integration-adapter-architect` |
| CK-SA-D4 | No `ambiguous` / `blocked` verdict was resolved by choosing inline | inspect `module_charter` findings | done | 0 non-selected verdicts |
| CK-SA-D5 | Every module has its own checklist file **before** its first write | `python scripts/check_checklist.py <ws> --phase 1 --require-per-module` | doing | 1 of 2 created; module 2 not started, which is correct |
| CK-SA-D6 | Tier / child names appear only as `routing_hint`, never as owner | `python scripts/check_ledger_owner.py <ws>` | done | 0 rows name `14`–`23` as owner |

## E. Visual children and the site input

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-E1 | `visual-source-map.md` written **before** any visual child runs | `python vendor/sdd-agent/run_hooks.py --check-visualizer-coverage <ws> --visualizer-mode all` | done | exit 0 |
| CK-SA-E2 | C1 and C2 rendered; every element traces to a cited source | same | done | 3 L1 · 4 L2 elements |
| CK-SA-E3 | Every `source-map.yml` carries ≥1 **typed** relation, so the site's graph has real input | `python scripts/check_source_map_typed.py <ws>` | done | **G-1 closed 2026-08-08.** `check_source_map_typed.py` fails stubs (`MAP-STUB`) and passes typed maps; seed → `PASSED (1 map(s), all typed)` with `--require-from-module`, and the task-A `checkout` workspace → `PASSED (2 map(s), all typed)`. A stub is now a red gate, not a default. |
| CK-SA-E4 | Diagram format is ingestible by both the C4 gate and the renderer | `python vendor/sdd-agent/scripts/check_c4_consistency.py <ws>` | done | **G-2 closed 2026-08-08.** `check_c4_consistency.py` parses `.puml` and `.md` (line 76) and detects Mermaid views; on `spine-a` → `findings: 0 error(s), 0 warning(s)`, exit 0. The gate passes on the E-1 burn-down workspace. |

## F. Close Phase 1

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-SA-F1 | Every module checklist is clean | `python scripts/check_checklist.py <ws> --phase 1` | todo | — |
| CK-SA-F2 | `02-spec-critic` ran; every RISK finding has an owner | `python vendor/sdd-agent/run_hooks.py --check-phase-coverage <ws> --phase 1` | todo | — |
| CK-SA-F3 | Self-ask pass complete: every `ASM` has a reversal trigger, every `OQ` an owner | `python vendor/sdd-agent/scripts/clarification_state.py <ws>` | todo | — |
| CK-SA-F4 | Phase 1 postflight passed | `python vendor/sdd-agent/scripts/run_sdd_phase.py --workspace <ws> --phase 1 --postflight` | todo | — |
| CK-SA-F5 | The site can start: doc coverage has no orphan | `python scripts/check_doc_coverage.py <ws>` | todo | — |

---

## Standing blockers — regenerated, do not hand-edit

| ID | Owner | Reason | Unblocks when |
|---|---|---|---|
| *(none)* | | | |

> **P-4/B-3, G-1, G-2, G-3 all closed 2026-08-08.** CK-SA-B4, CK-SA-C4, CK-SA-E3, CK-SA-E4 are `done` — the standing-blockers table is empty because every formerly-blocked owner has landed. See the rows above for argv evidence.

**Verdict: `--postflight` will FAIL.** 1 doing, 4 todo, 0 blocked. Correct for a phase in progress.
