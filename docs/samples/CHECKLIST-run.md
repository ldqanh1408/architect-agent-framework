---
checklist_id: CK-RUN-001
kind: run
generated_by: scripts/build_checklist.py
generated_at: 2026-08-07T08:40:00Z
workspace: <workspace>
project: QuickCart
status: in_progress
current_phase: 1
---
# Run Checklist — the highest level

**One page for a whole SDD run.** Every phase is a section; every section closes only
when its own gate passes and its child checklists are clean. This is the sample the
agent creates *first*, before any other work, and updates as it goes.

**How it is enforced:** `run_sdd_phase.py --postflight` for phase *N* refuses to close
phase *N* while any row in section *N* is `todo` / `doing`, or is `blocked` / `n-a`
without an owner and a reason. The gate reads this file; it does not trust a summary.

**Statuses:** `todo` · `doing` · `done` · `blocked` (owner + reason) · `n-a` (reason).

---

## 0 · The shape of the run

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  BRIEF  →  P0 clarify  →  P1 architect  →  P2 plan  →  P3 test  →  P4 deliver │
│                              │                                                │
│                              ├─ orchestrator writes  01-global-strategy/      │
│                              │                       03-cross-cutting/        │
│                              │                       _shared-contracts/       │
│                              │                                                │
│                              └─ for each module, SEQUENTIALLY:                │
│                                    route → preflight → read → generate        │
│                                          → postflight → ledger row            │
│                                    each one gets its own CHECKLIST-P1-*.md    │
└──────────────────────────────────────────────────────────────────────────────┘
                                       ▼
                        L1 + L2 site  (../GUIDE-CORE-RUNS.md)
```

**The one rule that shapes everything else:** the owner of a module is whatever the
**router** selects from `exported_skills/domains/<cluster>/<skill>/`. Tiers and the
`14`–`23` child names are routing *hints* — they have no package and own nothing.

---

## Phase 0 — Clarify the requirement

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-0.1 | Brief ingested; every source has a ledger row | `python vendor/sdd-agent/scripts/check_source_ingestion.py <ws>` | done | 3 sources · 0 `new` · 0 `partial` |
| CK-0.2 | Every numbered clause of the brief became a `CLR-xxx` | `python vendor/sdd-agent/scripts/check_requirement_fidelity.py <ws> --phase 0` | done | 24 clauses → CLR-001…CLR-024 |
| CK-0.3 | Clarification ledger has zero open ambiguity findings | `python vendor/sdd-agent/scripts/clarification_state.py <ws>` | done | 0 open · bound to source digest `sha256:1a3f…` |
| CK-0.4 | `problem-brief.md` written; phase 0 postflight passed | `python vendor/sdd-agent/scripts/run_sdd_phase.py --workspace <ws> --phase 0 --postflight` | done | exit 0 · 08:52:04Z |

**Phase 0: CLOSED.**

---

## Phase 1 — Architect

### 1a · Orchestrator-owned (never delegated)

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-1.1 | `document-tree-plan.md` selected, validated, approved, **executing** | `python vendor/sdd-agent/scripts/check_target_document_tree_plan.py <ws>` | done | state=executing · sha256 `9c1d…` |
| CK-1.2 | `01-global-strategy/**` authored — brief, goals, requirements, strategy, principles, technology, risks, ADRs | `python vendor/sdd-agent/run_hooks.py --check-workspace-all <ws> --phase 1` | done | 15 pages |
| CK-1.3 | `_shared-contracts/**` authored — one owner for every cross-module contract | same | done | 2 contracts |
| CK-1.4 | `03-cross-cutting/**` authored for every concern ≥2 modules depend on identically | same | done | 1 mechanism |
| CK-1.5 | `metamodel.md` written **as the prose face of** `correspondence_rules.yaml`, not a second list | `python -m architect_framework.orchestrator.consistency_checker --selftest` | done | **G-3 closed 2026-08-08.** `vendor/sdd-agent/01-system-architect/references/design/metamodel.md` exists as the prose face of `architect_framework/data/correspondence_rules.yaml` (16 rules, derived — the page's 18 `CR-` references all resolve). `consistency_checker --selftest` exit 0. |

### 1b · Per module, one at a time

Concurrency is 1. A new module starts only after the previous ledger row is
`complete` + `pass` + `next_allowed`.

| # | Module | Cluster / selected skill | Checklist | Status |
|---|---|---|---|---|
| — | *(orchestrator layer)* | `01-system-architect` | [`CHECKLIST-phase1-system-architect.md`](CHECKLIST-phase1-system-architect.md) | doing |
| 1 | `core-messaging-gateway` | `03_application_architecture` / `backend-service-architect` | [`CHECKLIST-phase1-backend-service-architect.md`](CHECKLIST-phase1-backend-service-architect.md) | doing |
| 2 | `payment-gateway-adapter` | `03_application_architecture` / `integration-adapter-architect` | *(not started — module 1 must close first)* | todo |

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-1.6 | Every module in the charter has its own checklist file | `python scripts/check_checklist.py <ws> --phase 1 --require-per-module` | done | 1/2 created; module 2 not started, which is correct |
| CK-1.7 | Every module checklist is clean | `python scripts/check_checklist.py <ws> --phase 1` | todo | module 1 has CK-E3 `doing`, CK-F1…F4 `todo` |
| CK-1.8 | No module was processed in a batch (no comma-separated slugs, no shared `run_id`) | `python vendor/sdd-agent/run_hooks.py --check-submodule-sequence <ws>` | done | exit 0 |
| CK-1.9 | Every ledger row names an **exported** skill as owner; no row names `14`–`23` | `python scripts/check_ledger_owner.py <ws>` | done | 1 row · `selected.domain_skill_id=backend-service-architect` |

### 1c · Visual children

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-1.10 | `visual-source-map.md` written **before** any visual child runs | `python vendor/sdd-agent/run_hooks.py --check-visualizer-coverage <ws> --visualizer-mode all` | done | exit 0 |
| CK-1.11 | C1 and C2 rendered; every element traces to a cited source | same | done | 3 L1 elements · 4 L2 elements |
| CK-1.12 | Diagram format is ingestible — **archify does not parse Mermaid**, and `check_c4_consistency.py` parses `.puml` | `python vendor/sdd-agent/scripts/check_c4_consistency.py <ws>` | done | **G-2 closed 2026-08-08.** `check_c4_consistency.py` parses both `.puml` and `.md` (line 76) and detects Mermaid views; on `spine-a` (the E-1 burn-down) → `findings: 0 error(s), 0 warning(s)`, exit 0. The file-of-record question is settled: the gate parses both, and the spine-a workspace proves the C4 gate passes. |

### 1d · Critique and close

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-1.13 | `02-spec-critic` ran; every RISK finding has an owner | `python vendor/sdd-agent/run_hooks.py --check-phase-coverage <ws> --phase 1` | todo | — |
| CK-1.14 | Phase 1 postflight passed | `python vendor/sdd-agent/scripts/run_sdd_phase.py --workspace <ws> --phase 1 --postflight` | todo | — |

**Phase 1: OPEN.** 14 rows — 9 done, 3 todo, 2 blocked. Module 1's own checklist adds a third
standing blocker (CK-A5) and one `doing` row.

---

## Phases 2 – 6

Sections are generated when the phase unblocks; a phase whose predecessor is open has
no checklist, because writing one would imply it could start.

| Phase | Gate to open it | Status |
|---|---|---|
| 2 · Plan (roadmap, WBS, tickets) | phase 1 closed | `todo` |
| 3 · Test + handoff | phase 2 closed | `todo` |
| 4 · Deliver + accept | phase 3 closed | `todo` |
| 5 · Codebase docs | phase 4 closed | `todo` |
| 6 · Change propagation | on the first approved `CR-xxx` | `n-a` — reason: no change request yet |

---

## Site — the L1/L2 documentation site

Runs after phase 1 closes; specified in
[`../GUIDE-CORE-RUNS.md`](../GUIDE-CORE-RUNS.md).

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-S1 | Every `.md` has exactly one owner node | `python scripts/check_doc_coverage.py <ws>` | todo | — |
| CK-S2 | Every L1 blackbox band re-renders byte-identical from its L2 child | `python scripts/check_projection_drift.py <ws>` | todo | — |
| CK-S3 | No canvas ships an overlap, an off-canvas boundary, or a colliding label | build failure if not | todo | — |
| CK-S4 | Every edge carries a `source`; diagram-derived edges are marked `EDGE-SOURCE-WEAK` | inspect `build/site-model.json` | todo | — |
| CK-S5 | **Build is idempotent** — build twice, working tree stays clean | `make site && git status --porcelain && make site && git status --porcelain` | todo | — |
| CK-S6 | **Build is atomic** — a deliberate mid-build failure leaves the published site intact | inject an unresolvable link; `site/` still serves the previous revision | todo | — |
| CK-S7 | **Build is reproducible** — no hidden state, no network, no machine-specific path | build in a clean container; compare `sha256` of every emitted file | todo | — |
| CK-S8 | **Deep links survive renames** — the published-link fixture resolves through the alias table | `python scripts/check_deeplinks.py <ws> --fixture tests/fixtures/published-links.txt` | todo | — |
| CK-S9 | **Layout is stable** — adding one container moves few nodes, and the report says how many | `python scripts/build_site.py <ws> --plan` → node-displacement estimate | todo | — |

### Adding or changing a document — run this before every write

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| ADD-1 | The owner is decided **before** the file exists, and by which rule (P1/P2/P3/P4) | `python scripts/build_site.py <ws> --plan` names the rule; `ORPHAN` means stop | n-a | reason: no doc added in this run yet |
| ADD-2 | It sits under that owner's existing path; a new folder only if the skill's `workspace-template.yml` declares that slot and its `when:` is now true | `python vendor/sdd-agent/scripts/check_workspace_template.py <ws> --skill <s>` | n-a | reason: as above |
| ADD-3 | It carries the 4-part spine and ≥1 stable ID | `python exported_skills/_shared/scripts/check_output_docs.py <owns_root>` | n-a | reason: as above |
| ADD-4 | Every relative link resolves against the workspace root | `python scripts/check_doc_coverage.py <ws>` (DC-8) | n-a | reason: as above |
| ADD-5 | If the whitebox `## Summary` changed, the band was **regenerated**, never hand-edited | `python scripts/check_projection_drift.py <ws>` | n-a | reason: as above |
| ADD-6 | `--plan` was read and the blast radius accepted | `python scripts/build_site.py <ws> --plan` exits 0 | n-a | reason: as above |

---

## Standing blockers — regenerated, do not hand-edit

| ID | Owner | Reason | Unblocks when |
|---|---|---|---|
| *(none)* | | | |

> **G-2, G-3, M0 all closed 2026-08-08.** CK-1.5, CK-1.12, and CK-A5 are `done` — the standing-blockers table is empty because every formerly-blocked owner has landed. See the rows above for argv evidence.

## Run verdict

```
python scripts/check_checklist.py <ws> --run CK-RUN-001

  this file          33 rows   15 done ·  0 doing · 12 todo ·  0 blocked ·  6 n-a
    phase 0          CLOSED       4 done
    phase 1          OPEN         11 done ·  3 todo ·  0 blocked
    site             NOT STARTED  9 todo   (gated on phase 1)
    safe-add         NOT APPLICABLE  6 n-a  (no document added in this run yet)
  CHECKLIST-phase1-system-architect.md
                     29 rows   22 done ·  1 doing ·  4 todo ·  2 blocked
  CHECKLIST-phase1-backend-service-architect.md
                     26 rows   21 done ·  1 doing ·  3 todo ·  1 blocked

  FAIL  12 todo in this file
  FAIL  child checklists have 9 todo, 3 doing
  OK    all 2 blocked rows carry owner + reason + unblocks-when
  OK    all 6 n-a rows carry a reason
  → exit 1
```

A run whose checklist is all green on the first pass has almost certainly been
written from memory rather than executed. Blocked rows with named owners are the
healthy state; empty rows are the unhealthy one.
