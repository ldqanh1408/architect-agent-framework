---
description: Show which skill slots a workspace needs, which have content, and what fills the empty ones (UC-08)
argument-hint: "[install <zip> | doctor (tùy chọn)]"
---

# `/architect-skills` — 297-Slot Skill Catalog & Transactional Pack Manager (`UC-08`)

Inspect, diagnose, or install domain and task skill packs across the 297-slot AAF taxonomy for **$ARGUMENTS** (default: the current directory as the workspace):

## 1. Subcommands & Dual-Mode Execution

1. **`status` (Default — Inspect Workspace Skill Slots):**
   Call `architect_runtime_skills` with the workspace, or run via CLI:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills status <workspace> --json
   ```
   Show every slot required by the workspace with its state (`licensed`, `third-party`, `core`, `empty`, `base`), followed by `filled` of `required` across the 10 architecture domain clusters and 21 task families (297 total slots).
2. **Empty Slot Resolution & `cheapest_cover`:**
   For each `empty` slot, show its `advice` line verbatim: the individual skill price, the domain/cluster bundle pack that carries it, and the store link. Then display `cheapest_cover`. Explain clearly that an `empty` slot writes nothing until it is filled by an installed pack or a user-owned skill (`~/.architect-framework/skill-bindings.yml`, `ARCHITECT_SKILLS_PATH`, or `~/.claude/skills/`).
3. **`install <zip>` (Transactional Pack Installation):**
   Install a skill pack archive or directory with atomic rollback protection (`pack_transaction.py`):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills install <zip>
   ```
   Then re-run `skills status` to confirm the newly populated slots.
4. **`offer <skill-id>` (Inspect Single Slot Coverage & Bundles):**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills offer <skill-id>
   ```
5. **`doctor` (Diagnose Misplaced Skills & Binding Conflicts):**
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills doctor
   ```
   Explain each finding and the exact remediation step.

Never write a skill content yourself to fill a slot, and never set `ARCHITECT_ALLOW_BASE` for the user: running empty slots on their contract alone is their decision.

## Next

When every slot the user needs is filled, run `/architect-run`.

## If it fails

- `install` refuses a zip: show its one-line reason (wrong pack, damaged zip) and the store link from `offer`.
- Say in one sentence what failed and what fixes it; do not paste a traceback or a raw JSON error to the user.
