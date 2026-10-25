---
description: Run one known Domain x Task skill pair directly in workspace or standalone mode (UC-05)
argument-hint: "<yêu cầu viết ADR, API contract, hoặc thiết kế cơ chế>"
---

# `/architect-execute` — Direct Domain × Task Skill Executor (`UC-05`)

Execute a targeted **Domain Skill × Task Skill** pair for **$ARGUMENTS** in either **Standalone Point-Solution Mode** (no workspace required) or **Core SDD Workspace Mode**.

## 1. Mode A — Standalone Point-Solution Mode (`--standalone` or when `sdd-workspace.yml` is absent)

Use Standalone Mode when the user wants a single implementation-grade artifact immediately (e.g., an ADR, REST/gRPC API contract, Outbox/Saga mechanism specification, Data Entity DDL spec, or Threat Model) inside an existing code repository without creating a multi-hundred-file SDD workspace:

1. **Execute via MCP or CLI:**
   - **MCP Mode:** Call `architect_execute_standalone` with `domain_skill` (or `domain`), `task_skill` (or `task`), `query`, `workspace`, and `out_path` (or `out`).
   - **CLI Mode:**
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd execute-standalone "$ARGUMENTS" --out <file.md>
     ```
2. **Enforce the 10-Section Specification Contract & STE-80 Prose Quality:**
   - Include YAML frontmatter (`artifact_id`, `kind`, `title`, `status`, `owner`, `depth_dimensions`, `depth_witnesses`, `canonical_facts`, `guards`), all 10 canonical sections, Mermaid diagrams, `## 3. Executable Boilerplate`, and `## 4. Guardrails & Defaults`.
   - Validate prose clarity locally with `architect_style_check` (`aaf-ste80-v1`, sentences `<= 25` words, active voice, zero `TODO`/`TBD` placeholders).

## 2. Mode B — Core SDD Workspace Mode (when `sdd-workspace.yml` is present)

1. Verify skill slot availability with `architect_runtime_skills` (or `skills status <ws>`).
2. Use `architect_runs_start`, `architect_task_claim`, `architect_task_heartbeat`, and `architect_task_complete` (or `architect_sdd_propose` for a direct isolated proposal) with the configured skill grant and exact `origin_snapshot`.
3. Read any base candidate with `architect_sdd_read` before extending it.
4. Run `architect_sdd_prepare_check` and `architect_sdd_check` (`sdd check <ws> --full`) to verify zero regressions and full depth witness grounding, then provide `architect_console_url` for human review and signed acceptance.

## Next

Read the current result, then use `/architect-check` for the next scoped action.

## If it fails

- A missing or malformed workspace marker in workspace mode requires explicit setup, migration, repair, or `--standalone`; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
