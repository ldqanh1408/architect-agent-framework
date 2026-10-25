---
description: Fast-track MVP architecture specification (minimal/standard profile, 12-25 pages in 5-10 minutes, UC-02)
argument-hint: "[mô tả ngắn hoặc thư mục đích (tùy chọn — tự động quét tài liệu)]"
---

# `/architect-quickstart` — Fast-Track MVP Architecture Playbook (`UC-02`)

Build and verify a complete, implementation-ready MVP architecture specification (`minimal` or `standard` profile, 12–25 pages) for **$ARGUMENTS** in a single cohesive workflow without manual setup.

## 1. Mandatory Skill & Reference Loading

Before planning or materializing the MVP workspace, read these files from `${CLAUDE_PLUGIN_ROOT}`:
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/design/target-document-tree-planning.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/design/document-tree-primer.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/output-contract.md`

## 2. End-to-End Fast-Track Execution Protocol

1. **Phase 0 & Phase 1 — Auto-Initialize & Extract Source Ledger:**
   Initialize the target workspace (`default: ./spec`) with `preset: solo-author` and `profile: standard` (or `minimal` for small single-service apps), then extract all input sources (`brief.md`, `clarified-requirements.md`, `README.md`, or SRS files):
   - **MCP Mode:** Call `architect_sdd_init`, `architect_sdd_extract`, and `architect_sdd_materialize`.
   - **CLI Mode:**
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd host-init ./spec --workspace-id mvp-spec --reviewer lead-architect --profile standard --preset solo-author --allow-existing-sources
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd extract-sources --workspace ./spec --sources <source-files>
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd materialize --workspace ./spec --profile standard --preset solo-author
     ```
2. **Phase 2 — Author Core MVP Deliverables (10-Section Contract, Zero Stubs):**
   Author every materialized specification page with concrete domain schemas, Mermaid C4/sequence/state diagrams, `## 3. Executable Boilerplate`, and `## 4. Guardrails & Defaults`:
   - **System Views & Strategy:** `architecture/index.md`, C1 System Context, C2 Container View, Deployment Topology, Requirements Baseline, Solution Strategy, Risk Register, and core ADRs (`01-global-strategy/05-governance/decisions/NNNN-<slug>.md`).
   - **Bounded Contexts & Shared Contracts:** Core domain overviews, API contracts, data entity schemas, and critical runtime scenarios.
3. **Phase 3 — Post-Processing & Deterministic Gate Verification:**
   Run the built-in post-processor and deterministic gate checker until `status == "PASS"` and `findings == []`:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd prepare-check ./spec --tighten --style-fix --stamp
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd check ./spec --full --out ./spec/.architect-build/check.json
   ```
4. **Phase 4 — Workbench Handoff:**
   Provide the 4-layer scorecard and launch or share the interactive C4 workbench URL (`http://localhost:8767/`).

## Next

Read the current result, then use `/architect-console` or `/architect-check` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
