---
primary_layer: workflow
---
# 02 — Core Engine

The mechanisms that make the framework *do* something at runtime. Each `.md` here specifies exactly one pattern, with executable boilerplate and normative defaults.

- [filter-chain-responsibility.md](filter-chain-responsibility.md) — Chain of Responsibility (Servlet Filter / middleware pipeline)
- [authentication-manager-strategy.md](authentication-manager-strategy.md) — Strategy pattern for pluggable providers
- [context-threadlocal-holder.md](context-threadlocal-holder.md) — Ambient thread-local context propagation

When adding a new mechanism, follow the six-section anatomy defined in [`workspace-skeleton-maximal.md Section 6`](../../../../../../references/design/workspace-skeleton-maximal.md#6-page-anatomy--executable-specification). Any mechanism page missing `## 3. Executable Boilerplate` or `## 4. Guardrails and Defaults` is a coverage defect.
