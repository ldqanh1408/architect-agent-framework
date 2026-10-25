---
description: Interactive context-aware onboarding wizard, workspace status probe, and 16-command catalog
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect` — Context-Aware Onboarding Wizard & 16-Command Control Plane

Act as a Principal Systems Architect operating with the **Architect Agent Framework (AAF v2.0)** installed at `${CLAUDE_PLUGIN_ROOT}`. Inspect the user workspace **$ARGUMENTS** (default: current directory `.`) and guide the user or execute the appropriate workflow without requiring any custom System Prompt.

## 1. Environment & Dual-Mode Probe (Mandatory First Action)

Run the context-aware workspace probe via MCP `architect_sdd_check` or the self-contained CLI launcher (which automatically bootstraps `PYTHONPATH` to embedded `architect_framework` and `vendor/sdd-agent`, sets `PYTHONUTF8=1`, and loads `.env`):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd status-probe "${ARGUMENTS:-.}"
```

### Decision Tree Based on Workspace State

- **Case A — Uninitialized Directory (`sdd-workspace.yml` is absent):**
  1. Inspect discovered source documents (`*.md`, `SYSTEM_REQUIREMENTS.md`, `SRS`, `PRD`, `ADR`, `brief.md`) and code/evidence directories (`frontend/`, `backend/`, `src/`, `*-acceptance/`).
  2. Recommend the exact command matching the user intent:
     - **UC-01 (Raw Idea / Incomplete Brief):** Run `/architect-clarify <idea-or-brief>` to conduct a bounded Socratic interview and author `clarified-requirements.md`.
     - **UC-02 (Fast-Track MVP Specification, 12–25 pages in 5–10 min):** Run `/architect-quickstart`.
     - **UC-03 (Full Enterprise ISO/IEC/IEEE 42010 Specification, 100–350+ pages):** Run `/architect-design`.
     - **UC-04 (Brownfield Codebase & Acceptance Audit):** Run `/architect-audit`.
     - **UC-05 (Single Point Decision / Standalone ADR or API Contract):** Run `/architect-route <request>` or `/architect-execute <yêu cầu>`.
- **Case B — Initialized SDD Workspace (`sdd-workspace.yml` is present):**
  Display the **4-Layer Governance Scorecard**:
  1. **Task Execution State:** Completed, running, or `waiting-for-human` tasks.
  2. **Deterministic & Coverage Gate Scorecard (`DTG-01`..`DTG-10`):** Overall status (`PASS` / `INCOMPLETE` / `FAIL`), authored pages vs placeholder stubs (`TODO: authored content pending.`), and all 5 coverage ratios (`source_intake_completeness`, `accounting_completeness`, `design_coverage`, `critical_coverage`, `depth_completeness`).
  3. **Semantic & Language Review State:** Sharded `@system` / `OBL-SEAM-*` review status and `aaf-ste80-v1` technical prose compliance.
  4. **Human Acceptance State:** Signed acceptance status and the interactive C4 workbench link (`http://localhost:8767/`).

## 2. Complete 16-Command Operational Catalog

| Command | Action |
|---|---|
| `/architect` | Interactive context-aware onboarding wizard, workspace status probe, and 16-command catalog |
| `/architect-init` | Initialize a new SDD workspace (`solo-author` or `governed-team`, supports existing source files) |
| `/architect-clarify` | Run Socratic requirement clarification from raw ideas or briefs (`UC-01`) |
| `/architect-route` | Select an applicable Domain × Task skill pair and explain ambiguity (`UC-05`) |
| `/architect-quickstart` | Build a fast-track MVP architecture (`minimal`/`standard`) in 5–10 minutes (`UC-02`) |
| `/architect-design` | Execute the autonomous 6-phase full-lifecycle architecture playbook (`UC-03`) |
| `/architect-execute` | Run a known Domain × Task skill pair in workspace or `--standalone` mode (`UC-05`) |
| `/architect-audit` | Audit brownfield codebases and acceptance test evidence against specs (`UC-04`) |
| `/architect-change` | Manage living specification change requests and dependency impact (`UC-07`) |
| `/architect-check` | Inspect deterministic coverage, depth, and anti-stub gates (`UC-06`) |
| `/architect-review` | Run independent `02-spec-critic` and sharded JEV semantic/language review (`UC-06`) |
| `/architect-run` | Start or continue bounded multi-agent task waves |
| `/architect-status` | Inspect task dependencies, coverage scorecard, and pending human gates |
| `/architect-skills` | Inspect 297 skill slots, offer packs, or install skill zips (`UC-08`) |
| `/architect-console` | Launch the interactive C4 Document Graph and Review Workbench (`UC-08`) |
| `/architect-approve` | Show the human passkey enrollment and cryptographic sign-off procedure (`UC-08`) |

Load the selected skill and all required references before authoring. Installed content does not grant write authority. Only the person enrolls keys and signs decisions. Review and acceptance remain separate.

## Next

Read the current result, then use `/architect-quickstart` or `/architect-design` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup via `/architect-init`, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
