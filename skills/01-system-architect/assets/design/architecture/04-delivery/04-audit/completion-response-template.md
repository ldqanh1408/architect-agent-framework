---
primary_layer: infrastructure
---
Generated technical system docs at `{{OUTPUT_DIR}}`.

- Project type: `{{PROJECT_TYPE}}`
- Optional modules activated: {{ACTIVATED_MODULES}}
- UML pages generated: {{UML_PAGE_LIST}}
- Pages generated: {{PAGE_COUNT}} (core + uml + module + detail)

Validation: `{{VALIDATION_STATUS}}` (`scripts/check_output_docs.py {{OUTPUT_DIR}}`)

Open questions: {{OPEN_QUESTION_COUNT}}
{{OPEN_QUESTION_LIST}}

Key remaining assumptions:
{{ASSUMPTION_LIST}}

Note: Mermaid diagrams render natively on GitHub/GitLab and in editors such as
VS Code. Open `index.md` in any Markdown viewer to confirm diagram syntax and
navigation; no internet connection or extra tooling is required.
