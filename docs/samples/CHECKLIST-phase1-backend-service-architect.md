---
checklist_id: CK-P1-backend-service-architect-001
generated_by: scripts/build_checklist.py
generated_at: 2026-08-07T09:14:22Z
phase: 1
workspace: <workspace>
skill: backend-service-architect
cluster: 03_application_architecture
routing_hint: { tier: "12.2", child: "15-backend-service-architect" }
module: core-messaging-gateway
run_id: r-2026-08-07-001
previous_run_id: none
status: in_progress
---
# Checklist — Phase 1 · `backend-service-architect` · `core-messaging-gateway`

**This file is a gate, not a note.** `run_sdd_phase.py --postflight` reads it and
**exits non-zero** unless every row is `done`, or `blocked`/`n-a` **with a reason and
an owner**. A row cannot be closed by asserting it; `Verify` names the argv that
closes it, and `Evidence` records what that argv actually returned.

**Statuses:** `todo` · `doing` · `done` · `blocked` (needs owner + reason) ·
`n-a` (needs reason). Nothing else parses.

---

## A. Intake — before writing anything

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-A1 | Router returned `selected`; the owner is an **exported skill**, not a tier child | `python exported_skills/orchestration/architect-skill-orchestrator/scripts/route.py route --query "core messaging gateway persistence fan-out"` | done | `status=selected domain_skill_id=backend-service-architect task_skill_id=service-decomposition` exit 0 · 09:02:11Z |
| CK-A2 | The four `load_paths` were read completely | manual + `skill_intake` row in `sdd-context.yml` | done | `skill_intake[2].read_status=read-complete` |
| CK-A3 | Preflight passed | `python vendor/sdd-agent/scripts/run_sdd_phase.py --workspace <ws> --phase 1 --skill backend-service-architect --slug core-messaging-gateway` | done | exit 0 · 09:03:40Z |
| CK-A4 | Previous ledger row is `complete` + `postflight_status: pass` + `next_allowed: true` | `python vendor/sdd-agent/run_hooks.py --check-submodule-sequence <ws>` | done | exit 0 |
| CK-A5 | Write root resolves to `02-domains/<cluster>/<skill>/`, **not** `<NN>-<slug>` | `python scripts/check_catalog_isomorphism.py --strict` | done | **M0 closed 2026-08-08 (user sign-off OQ-5).** `check_catalog_isomorphism.py --strict` → `clusters=10 skills=110 participants=110 findings=0` / `PASSED`, exit 0. All 110 contracts carry the emergent `<cluster>/<skill>` shape; R3 = 0. |

## B. Scaffold — from this skill's own workspace template

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-B1 | Every `when: always` slot exists | `python vendor/sdd-agent/scripts/check_workspace_template.py <ws> --skill backend-service-architect` | done | exit 0 · 5/5 slots |
| CK-B2 | Every conditional slot that was **skipped** has a one-line reason in the overview | `… --explain-skips` | done | skipped `02-core-engine/` — "no algorithm routed here"; skipped `self-audit.md` — "level=standard" |
| CK-B3 | No empty optional folder was created | `… --no-empty-optional` | done | exit 0 |
| CK-B4 | One `01-<module>/` folder per module in the charter; folder name, overview title and `source-map.subject` agree | `python scripts/check_module_identity.py <ws> --skill backend-service-architect` | done | 1 module · 3/3 names agree |
| CK-B5 | No forbidden slot was written | `python vendor/sdd-agent/run_hooks.py --check-child-ownership <ws>` | done | exit 0 |

## C. Author — content, not shape

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-C1 | Every page carries the 4-part spine | `python exported_skills/_shared/scripts/check_output_docs.py <owns_root> --contract <pkg>/skill-contract.yml` | done | `PASSED: 4 pages` |
| CK-C2 | Every page has ≥3 implementable identifiers | `python vendor/sdd-agent/scripts/check_evidence_discipline.py <owns_root>` | done | overview 11 · design 8 · fitness 6 |
| CK-C3 | `source-map.yml` declares ≥1 **typed** relation | `python scripts/check_source_map_typed.py <owns_root>/source-map.yml` | done | 4 relations: 1 providesApi · 2 consumesApi · 1 publishesEvent |
| CK-C4 | Every relation kind is declared in the metamodel | `python -m architect_framework.orchestrator.consistency_checker --source-map <owns_root>/source-map.yml` | done | 4/4 kinds resolve · 16 correspondence rules loaded |
| CK-C5 | Every `FIT-*` uses **this skill's** `fitness_prefix` (`BSA-FIT`) | `python vendor/sdd-agent/scripts/check_fitness_catalog.py <owns_root> --expect-prefix BSA-FIT` | done | 6/6 rows · 0 `BE-FIT` occurrences |
| CK-C6 | No verdict outside the legal five; positive share ≤ ~⅓ | `python vendor/sdd-agent/scripts/check_audit_honesty.py <owns_root>` | done | 6 rows: 4 UNVERIFIABLE-AT-PHASE-1 · 1 VERIFIED-BY-QUOTE · 1 GAP → positive share 17 % |

## D. Requirement coverage (A4)

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-D1 | Every clause routed to this module has a ledger row ending in `Covered` / `Deferred` / `GAP` | `python vendor/sdd-agent/scripts/check_requirement_fidelity.py <ws> --scope <owns_root>` | done | 9 clauses · 8 covered · 1 GAP (CLR-021 push retry budget) |
| CK-D2 | No clause is silently absent | same command, mechanical presence half | done | 0 unaccounted |

## E. Self-ask clarification (A5)

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-E1 | Every `ASM-xxx` has a reversal trigger | `python vendor/sdd-agent/scripts/clarification_state.py <owns_root>` | done | 3 ASM · 3 triggers |
| CK-E2 | Every `OQ-xxx` has an owner and a concrete question | same | done | 2 OQ · both owned |
| CK-E3 | Every VAGUE / PLACEHOLDER / measure-less term is resolved or promoted | same | doing | 1 remaining: "low latency" in `01-core-messaging-gateway/…-design.md:88` |
| CK-E4 | The design has **at least one** marker | same | done | 5 markers — a zero-marker design over a real requirement is itself a signal (V-11) |

## F. Close

| ID | Step | Verify | Status | Evidence |
|---|---|---|---|---|
| CK-F1 | Postflight passed | `python vendor/sdd-agent/scripts/run_sdd_phase.py --workspace <ws> --phase 1 --skill backend-service-architect --slug core-messaging-gateway --postflight` | todo | — |
| CK-F2 | Exactly one ledger row written **by the workflow manager**, chained by `previous_run_id` | `python vendor/sdd-agent/run_hooks.py --check-submodule-sequence <ws>` | todo | — |
| CK-F3 | The ledger row records `selected.{domain_skill_id, task_skill_id, cluster_id}` and demotes tier/child to `routing_hint` | inspect `sdd-context.yml` | todo | — |
| CK-F4 | This checklist has no `todo` / `doing` row left | `python scripts/check_checklist.py <ws> --run r-2026-08-07-001` | todo | — |

---

## Blocked and skipped — the standing summary

`check_checklist.py` regenerates this section; do not hand-edit it.

| ID | Status | Owner | Reason | Unblocks when |
|---|---|---|---|---|
| CK-E3 | doing | this run | one measure-less term remains | the term gains a unit + source, or is promoted to `OQ-xxx` |

> **M0 closed 2026-08-08 (user sign-off OQ-5).** CK-A5 is `done` — the `{slot}-` shape is gone, `check_catalog_isomorphism.py --strict` reports `findings=0`. Only CK-E3 remains `doing`.

**Current verdict: `run_sdd_phase.py --postflight` will FAIL.** CK-E3 is `doing` and
CK-F1…F4 are `todo`. That is the correct outcome — the run is not finished, and the
checklist is what says so out loud.
