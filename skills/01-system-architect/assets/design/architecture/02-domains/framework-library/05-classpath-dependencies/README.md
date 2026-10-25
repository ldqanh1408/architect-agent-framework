---
primary_layer: workflow
---
# 05 — Classpath & Dependencies

Everything the artifact drags onto the consumer's classpath. Third parties consuming the framework must be able to read this slot alone to understand what they inherit.

- [dependency-management.md](dependency-management.md) — BOM, `dependencyManagement`, pinned versions
- [transitive-exclusions.md](transitive-exclusions.md) — forbidden transitives with rationale
- [packaging-distribution.md](packaging-distribution.md) — publish target, signing, artifact naming (moved from the flat layout)
- [versioning-compatibility.md](versioning-compatibility.md) — semver policy, deprecation window (moved from the flat layout)

Every version bump to a pinned dependency requires an ADR under `architecture/01-global-strategy/05-governance/decisions/`. Transitive drift is the single most common source of "it worked in dev, exploded in prod" incidents — this slot exists to make drift auditable.
