---
name: architect-runtime
description: Schedule and observe bounded architecture tasks and dispatch all 16 Architect commands across Claude Code, Codex, and DeepSeek Harness (dsh). Respect accepted grants, source obligations, task leases, and signed human gates. Document acceptance remains a separate human decision.
---

# Run current architecture tasks (`architect-runtime`)

Use the host-discovered `architect-runtime` MCP tools or the self-contained cross-platform CLI launcher (`python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap ...`). A host can add a namespace to tool names. The plugin embeds both `architect_framework/` and `vendor/sdd-agent/` inside `${CLAUDE_PLUGIN_ROOT}` and automatically loads `.env` (`JEV_API_KEY` / `JEV_KEY` / `SDD_JUDGE_API_KEY`).

## Dual-Surface 16-Command Dispatcher (Claude Code, Codex & DeepSeek Harness)

| Command / Skill Alias | Primary Use Case | Dual-Mode Execution (MCP Tool / CLI Subcommand) |
|---|---|---|
| `/architect` | Context-aware wizard | `architect_sdd_check` / `sdd status-probe .` |
| `/architect-init` | Zero-friction init | `architect_sdd_init` / `sdd host-init <ws> --preset solo-author --allow-existing-sources` |
| `/architect-clarify` | `UC-01` Socratic SRS | `00-requirement-clarifier` + `architect_sdd_propose` |
| `/architect-route` | `UC-05` Skill router | `cli route-skills --query "<request>"` |
| `/architect-quickstart` | `UC-02` Fast MVP spec | `architect_sdd_materialize` (`--profile standard`) + `architect_sdd_prepare_check` |
| `/architect-design` | `UC-03` Full 6-phase spec | `01-system-architect` (`sdd extract-sources` -> `sdd materialize` -> waves -> `sdd prepare-check` -> `sdd check`) |
| `/architect-execute` | `UC-05` Single skill pair | `architect_execute_standalone` (`sdd execute-standalone --domain <d> --task <t>`) |
| `/architect-audit` | `UC-04` Brownfield audit | `architect_sdd_extract` (`sdd extract-sources --audit`) + `architect_sdd_check` |
| `/architect-change` | `UC-07` Living spec CR | `architect_sdd_propose` + `sdd regression <ws> --full` |
| `/architect-check` | `UC-06` Gate & anti-stub | `architect_sdd_check` / `sdd check <ws> --full --out .architect-build/check.json` |
| `/architect-review` | `UC-06` Critic & JEV | `02-spec-critic` + `architect_candidate_review` (`sdd review-candidate <ws> --change <id> [--live]`) |
| `/architect-run` | Multi-agent wave run | `architect_runs_start`, `architect_task_claim`, `architect_task_complete` (`max_concurrency <= 4`) |
| `/architect-status` | 4-layer scorecard | `architect_runtime_status` + `architect_sdd_check` |
| `/architect-skills` | `UC-08` 297 skill slots | `architect_runtime_skills` / `skills status <ws> --json` |
| `/architect-console` | `UC-08` C4 web console | `architect_console_url` / `console serve <ws> --port 8767` |
| `/architect-approve` | `UC-08` Passkey sign-off | Human-only terminal: `console serve <ws> --enroll` |

## Mandatory Reference Loading for Full-Lifecycle Architecture (`01-system-architect`)

Before creating any workspace file or planning any document tree under `/architect-design` or `/architect-run`, load:
- `${CLAUDE_PLUGIN_ROOT}/skills/architect-runtime/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/workflow-contract.yml`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/design/workspace-skeleton-maximal.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/design/target-document-tree-planning.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/design/document-tree-primer.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/output-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/assets/design/architecture/document-tree-plan-template.md`

## Prepare

Call `architect_sdd_check`. Read the current source, accepted grants, and applicable skill contracts.
Load the selected skill and all of its required references. Use `architect_runtime_skills` to check installed content.
A missing marker requires explicit initialization or migration. A malformed marker requires repair.
Do not infer approval from an old ledger or copied reviewer key.

## Execute

1. Prepare bounded tasks with IDs, skills, objectives, writes, required outputs, dependencies, and human questions (`max_concurrency <= 4`, `1–2` pages per micro-batch across Waves 1–6). Run `sdd probe-models` before multi-agent dispatch.
2. Call `architect_runs_start`. Keep its run ID. Serialize overlapping writers.
3. Read `architect_runtime_status` or `architect_runtime_next`.
   A task awaiting a human cannot dispatch. Give the person `architect_console_url`.
   They open **Runs and task gates**, inspect the exact scope, answer the questions, and sign their action.
   Independent ready tasks can continue within the concurrency limit (`max_concurrency <= 4`).
4. Call `architect_task_claim` for a ready task. Keep its lease token private.
   Read the objective, required outputs, human answers, base candidate, and artifact revisions.
   If a base candidate exists, read that candidate before extending it.
5. Prepare proposal operations inside the declared paths and accepted grant (180–350 body lines, 10 canonical sections, all 9 depth dimensions, `## 3. Executable Boilerplate`, and `## 4. Guardrails & Defaults`).
   Preserve unknown facts. Do not guess human answers. Renew the active lease with `architect_task_heartbeat`.
6. Call `architect_task_complete` with the exact lease and proposal operations.
   The scheduler checks the isolated candidate and registered outputs. It does not accept documents.
7. Run `architect_sdd_prepare_check` (`sdd prepare-check <ws> --tighten --style-fix --stamp`) and `architect_sdd_check` (`sdd check <ws> --full`) until all 5 coverage ratios equal `1.0` and `findings == []`. Report checked candidates, failed tasks, missing evidence, and the next action.
   `execution-complete` means task checks passed. Independent review and signed document acceptance remain separate.

Call `architect_candidate_review` on a checked change ID. Use `live: true` only within the configured provider and shared candidate budget. Jev performs typed semantic and language assessment with verified source witnesses. Route targeted author corrections through `architect_language_repair`, then review the returned child candidate. Two repair attempts per document lineage share the original budget. Missing evidence remains INCOMPLETE; no model verdict grants acceptance.
Write short, clear technical English. Preserve IDs, values, units, links, code, normative words, negation, and UNKNOWN during repair.
The partial writing checker does not certify ASD-STE100 or 80% full-profile compliance.

## Observe and control

Read `architect_runs_observe` after the previous event cursor. Reading starts no work.
The workbench shows task state, dependencies, write scope, gate bindings, and events.
A view pause stops rendering updates. A scheduling pause stops new dispatch.
Running host workers can continue. Late results from cancelled or expired attempts are fenced.
Use `architect_runs_control` to pause, resume, cancel, or retry. These actions grant no approval.
A retry needs a new attempt and a new gate. A changed source or baseline needs a new plan.
A notification deadline never creates a human approval record.

Host observation is partial. Report unavailable usage and cost as unknown.
Do not claim a live model, live host, or physical-key qualification from synthetic tests.

## Human actions

Only the person enrolls or trusts reviewer keys, signs gates, accepts documents, and recovers publication.
Enrollment requires their own terminal and fingerprint confirmation. Do not execute these actions for them.
If no trusted key is available, keep the gate pending and show the enrollment instructions.
MCP has no human approval or document acceptance tool.

## How every reply ends

Report the observed task, validation, review and acceptance states separately. Give exactly one next step through a current command, with its scope. Never paste a traceback, expose a lease or credential, or call execution completion document acceptance. Preserve unknown observations.
