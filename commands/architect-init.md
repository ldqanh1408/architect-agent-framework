---
description: Initialize a new SDD architecture workspace with solo-author or governed-team preset
argument-hint: "[thư mục đích (tùy chọn)]"
---

# `/architect-init` — Zero-Friction SDD Workspace Initialization

Initialize **$ARGUMENTS** as an ISO/IEC/IEEE 42010 architecture workspace governed by the **Architect Agent Framework (AAF v2.0)**.

## 1. Governance Presets & Orthogonal Profile Selection

1. **Governance Presets (`--preset`):**
   - **`solo-author` (Default for Individual Architects & Fast Onboarding):** Sets `policy.mode: advisory` and `first_run_gate: auto`. Allows autonomous Phase 0 → Phase 4 execution (source intake, tree materialization, multi-wave authoring, and deterministic gate checks) without blocking at step 0 on a hardware WebAuthn passkey. Formal passkey sign-off remains available when publishing a baseline.
   - **`governed-team` (Enterprise & Multi-Reviewer Governance):** Sets `policy.mode: enforce` and `first_run_gate: approve`. Every task dispatch wave and candidate acceptance requires cryptographic WebAuthn passkey approval in the Review Console.
2. **Architecture Profiles (`--profile`):**
   - `seed` (3–6 files: brief, clarified requirements, index)
   - `minimal` (10–18 files: single service / small application)
   - `standard` (20–60 files: MVP / multi-module system)
   - `maximal` (100–350+ files: full enterprise system with 100% concern ledger accounting and full archetype slot expansion)
   - `portfolio` (250–600+ files: multi-system enterprise portfolio with C0 System Landscape & Domain Segments)

## 2. Dual-Mode Execution (MCP + Cross-Platform CLI)

- **MCP Mode:** Call `architect_sdd_init` with `workspace`, `workspace_id`, `reviewer`, `profile` (`seed`, `minimal`, `standard`, `maximal`, or `portfolio`), `preset` (`solo-author` or `governed-team`), and `allow_existing_sources: true`.
- **CLI Mode (Windows PowerShell, macOS, Linux):**
  ```bash
  python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd host-init "${ARGUMENTS:-.}" --workspace-id my-spec --reviewer lead-architect --profile standard --preset solo-author --allow-existing-sources
  ```

## 3. Non-Destructive Brownfield & Existing-Source Handling

- When `--allow-existing-sources` is enabled (default in `architect_sdd_init`), existing requirement documents (`SYSTEM_REQUIREMENTS.md`, `Atlas_Tech_Stack_and_ADR_SaaS.md`, `brief.md`, `README.md`) and code directories in the target folder are preserved intact and automatically registered under `attachments` in `sdd-workspace.yml` instead of failing with `WORKSPACE_NOT_EMPTY`.
- Control directories (`.sdd/`, `.architect/`, `.architect-build/`) and `sdd-workspace.yml` are created with deterministic schema validation.

## Next

Read the current result, then use `/architect-clarify` or `/architect-quickstart` for the next scoped action.

## If it fails

- If `sdd-workspace.yml` already exists, inspect it with `/architect-status` rather than overwriting it.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
