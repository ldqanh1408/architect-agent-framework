---
primary_layer: workflow
---
# 04 — Diagrams & Specs

Context-scoped UML and sequence diagrams that visualise the mechanisms in `02-core-engine/` and the DSL in `03-extension-points/`. Diagrams that span the *entire system* still live in the workspace-root `uml/` folder — this slot is for the framework-library bounded context only.

- [core-engine-class-diagram.md](core-engine-class-diagram.md) — Mermaid `classDiagram` overlay of the Proxy + Chain-of-Responsibility + Strategy + Builder patterns
- [authentication-sequence.md](authentication-sequence.md) — Mermaid `sequenceDiagram` of a single request end-to-end through the chain

Every diagram in this slot pairs with either a mechanism page (`02-core-engine/`) or a DSL page (`03-extension-points/`); orphan diagrams are a coverage defect.
