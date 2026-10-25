# Samples

Working reference artifacts for
[`../GUIDE-SDD-CORE.md`](../GUIDE-SDD-CORE.md).
These are shapes to copy, not generated output — but every one of them is what the
generator described in that plan must produce.

## Start here

**[`CHECKLIST-run.md`](CHECKLIST-run.md)** — the overall sample at the highest level. One
page for an entire SDD run: the pipeline shape, phase 0 closed, phase 1 open with
per-module sub-checklists, phases 2–6 deliberately ungenerated, the site section, and a
verdict block that exits 1 because the run is not finished.

## The artifacts

| File | Role |
|---|---|
| [`requirement-assistant-role-prompt.en.md`](requirement-assistant-role-prompt.en.md) | **Phase 0 persona.** The AI Requirements Assistant role prompt in English — four-layer conversation, value-before-question, converge late. Injected as `rolePromptTemplate`. |
| [`CHECKLIST-run.md`](CHECKLIST-run.md) | Run-level checklist. Created **first**, before any work. |
| [`CHECKLIST-phase1-system-architect.md`](CHECKLIST-phase1-system-architect.md) | The orchestrator's checklist — written before the architect writes anything. Opens with the Phase-0 → Phase-1 inheritance gate and its 14-field mapping. |
| [`CHECKLIST-phase1-backend-service-architect.md`](CHECKLIST-phase1-backend-service-architect.md) | Unit-level checklist for one delegated module — 26 rows, real argv, real evidence. |
| `sdd-workspace.yml` | The workspace contract with the legacy taxonomy removed: no static children table, no outer slots, one emergent glob, plus `routing_policy` and `execution_checklist`. |
| [`workspace-template/`](workspace-template) | A per-skill workspace template — the manifest plus its page templates, installed beside the exported skill that owns it. |

The end-to-end flow these fit into is
`../PLAN-REQUIREMENT-TO-SITE-FLOW.md`.

## The three rules these encode

1. **The owner is a router verdict.** Never a name written in a config file. The ten
   `14`–`23` tier children have no package and own nothing; they appear only as
   `routing_hint`.
2. **A slot exists because evidence activated it.** Every slot in the manifest carries a
   `when:`; a skipped slot gets a one-line reason, not an empty folder with a README
   saying it is deferred.
3. **A checklist row closes on argv, not on assertion.** `Verify` is a command;
   `Evidence` is what that command returned. `run_sdd_phase.py --postflight` reads the
   file and refuses to close a phase with an unfinished row.

## Reading order

```
requirement-assistant-role-prompt.en.md    ← Phase 0: how the requirement is drawn out
  └─ CHECKLIST-run.md                      ← the whole run, one page
       ├─ CHECKLIST-phase1-system-architect.md    ← the orchestrator, checklist first
       │    └─ inherits the Phase-0 draft (14-field mapping)
       └─ CHECKLIST-phase1-<skill>.md             ← one delegated module
            └─ workspace-template.yml             ← what that module scaffolds
                 └─ templates/*.md                ← what it writes into each slot
sdd-workspace.yml                     ← the contract all of the above obey
```
