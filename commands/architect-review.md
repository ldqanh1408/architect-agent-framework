---
description: Run independent 02-spec-critic pre-mortem and sharded JEV semantic/language review (UC-06)
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect-review` — Independent Spec Critique (`02-spec-critic`) & Sharded JEV Judge (`UC-06`)

Execute independent architectural critique and sharded semantic/language evaluation for **$ARGUMENTS**.

## 1. Mandatory Skill & Reference Loading

Before running the critique, read these files from `${CLAUDE_PLUGIN_ROOT}`:
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/workflow-contract.yml`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/references/review-method.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/references/shape-review.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/references/critic-rules.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/assets/premortem-checklist.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/assets/design-review-template.md`

## 2. Three-Stage Independent Review Protocol

1. **Stage 1 — Deterministic Gate Prerequisite (`DTG-01`..`DTG-10`):**
   Verify `architect_sdd_check` (`sdd check <workspace> --full`) passes with `status == "PASS"`, `findings == []`, and all 5 coverage metrics `== 1.0`. Do not waste live Judge budget on a workspace with unresolved deterministic defects or placeholder stubs.
2. **Stage 2 — Independent Pre-Mortem & Seam Critique (`02-spec-critic`):**
   - Perform structural shape review and failure-mode pre-mortem across cross-boundary seams (`OBL-SEAM-*`), distributed state machines (`SC-SM-*`), concurrency/fencing guards, and SLO failure recovery paths.
   - Classify findings using `references/critic-rules.md` (`blocker`, `major`, `minor`) with exact artifact/line citations.
3. **Stage 3 — Sharded JEV Semantic & Language Review (`aaf-ste80-v1`):**
   - Call `architect_candidate_review` and `architect_language_review` via MCP, or run via CLI (which automatically loads `JEV_API_KEY` / `JEV_KEY` / `SDD_JUDGE_API_KEY` from `.env` or environment):
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd review-candidate "${ARGUMENTS:-.}" --change <change-id> --live --out .architect-build/review.json
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd language-review "${ARGUMENTS:-.}" --change <change-id> --live --out .architect-build/lang-review.json
     ```
   - The engine automatically shards `@system` obligations into packets of `<= 8` prose documents and `<= 70 KB` (`70,000 bytes`), excludes machine/ledger files (`SRC-MANIFEST`, `CONCERN-INV`, `TARGET-PLAN`, `.json`), enables 64-sentence windowing, and caches per-document language evaluations by `(artifact_id, revision)` for incremental resume.
   - If any prose sentences fail STE-80 plain-language checks, propose bounded repairs via `architect_language_repair` (`sdd language-repair`). Model review results inform the human reviewer and grant no document acceptance.

## Next

Read the current result, then use `/architect-console` or `/architect-approve` for the next scoped action.

## If it fails

- A missing `JEV_API_KEY` stops live calls safely; set `JEV_API_KEY` in `.env` or run without `--live` for local heuristic review.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
