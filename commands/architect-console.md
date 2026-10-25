---
description: Open the interactive C4 Document Graph & Review Console workbench (UC-08)
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect-console` — Interactive C4 Architecture Graph & Review Workbench (`UC-08`)

Start the interactive Web Console for **$ARGUMENTS** (default: current directory) using MCP `architect_console_url` or the cross-platform CLI launcher:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap console serve "${ARGUMENTS:-.}"
```

## 1. Workbench Capabilities (`http://localhost:8767/`)

Give the person the localhost link (`http://localhost:8767/`) and summarize the two primary views:
1. **Document Review & Interactive C4 Explorer (`/`):**
   - **Data-Backed C4 Hierarchy:** Drill down from **C1 System Context** → **C2 Domain Clusters & Bounded Contexts** (`01_frontend_architecture`, `03_application_architecture`, `04_ai_architecture`, `07_security_architecture`, `08_quality_attribute_architecture`) → **C3 Concern Slots & Specification Pages**, alongside architectural pillars (`00-plan`, `00-system-views`, `01-global-strategy`, `03-cross-cutting`, `04-delivery`).
   - **Sub-Second `SnapshotCache` Reader (`< 20ms` per artifact):** Renders full Markdown tables, Mermaid diagrams, and separated YAML frontmatter even for large ledger files (`source-manifest.md`, `concern-inventory.md`, `document-tree-plan.md` up to `250 KB`).
   - **Traceability & Acceptance Drawer:** Inspect upstream requirement authorities, downstream consumers, deterministic gate findings, sharded JEV review verdicts, and cryptographic document acceptance.
2. **Runs and Task Gates (`/runs`):**
   - Inspect live multi-agent task state, DAG dependencies, write scopes, durable event stream, and pending human dispatch gates.

## 2. Human Authority Boundary

Human actions require the person passkey. Enrollment requires `--enroll` in their own terminal and fingerprint confirmation. Do not enable enrollment or sign decisions for them.

## Next

Read the current result, then use `/architect-status` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
