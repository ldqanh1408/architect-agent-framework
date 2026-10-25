---
primary_layer: content
submodules: []
---
# FIT-001 — Core must not import infrastructure

[← Table of Contents]({{INDEX_PATH}}) · *Cross-Cutting › Fitness Functions › FIT-001*

## Table of Contents

- [Summary](#summary)
- [Rule](#rule)
- [Why This Rule Exists](#why-this-rule-exists)
- [What Violating It Looks Like](#what-violating-it-looks-like)
- [Self-Check](#self-check)
- [See Also](#see-also)
- [Related Docs](#related-docs)

## Summary

The domain core stays independent of how it is stored, transported, and
deployed. This rule is the executable form of that claim: the target project
materializes it into its own stack, so the boundary is checked by
CI rather than by review discipline.

## Rule

```yaml
id: FIT-001
quality_attribute: modifiability
scope: layer-isolation
rule: forbid-dependency
from: "**/_shared-kernel/**"
to: ["**/02-domains/_shared-adapters/**", "**/infrastructure/**"]
severity: blocking
source_adr: ADR-0001
submodules: []
```

## Why This Rule Exists

A core that imports infrastructure cannot be tested without it, cannot be reused
behind a different adapter, and drags the whole stack into every unit test. The
dependency direction is the entire value of the hexagon; nothing else in the
design survives losing it.

## What Violating It Looks Like

An import of a persistence, HTTP, or vendor SDK type from inside a core package.
The fix is an outbound port plus an adapter that implements it, never a
suppression.

## Self-Check

| Check | Status |
|---|---|
| `quality_attribute` resolves into quality-attributes.md | {{CHECK_1}} |
| `source_adr` resolves to an accepted ADR | {{CHECK_2}} |
| The rule is materialized in the target project's own stack | {{CHECK_3}} |

## See Also

- ADR-0001
- QA-1

## Related Docs

- [Fitness Functions Overview](00-overview.md)
- [Quality Attributes](../../01-global-strategy/01-requirements/quality-attributes.md)
