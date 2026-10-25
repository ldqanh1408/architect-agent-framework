---
primary_layer: workflow
---
# Framework Library Module

SDK packaging, extension points (SPI), configurations, and semver.

## Layouts

This module ships **two layouts**. Pick one:

### Flat layout (simple libraries, single-artifact SDK)

Use when the artifact has fewer than five concerns. Files sit directly under this folder.

- [framework-library-overview.md](framework-library-overview.md)
- [public-api-surface.md](public-api-surface.md)
- [extension-points-spi.md](extension-points-spi.md)
- [configuration-contract.md](configuration-contract.md)
- [plugin-module-architecture.md](plugin-module-architecture.md)
- [packaging-distribution.md](packaging-distribution.md)
- [versioning-compatibility.md](versioning-compatibility.md)

### Deep-nested layout (custom starter, Fluid-DSL framework, multi-module SDK)

Use when the artifact ships a Fluid-DSL Builder, filter/interceptor chains, a plugin registry, an auto-configuration layer, or any of the other Actionable-Workspace triggers listed in [`references/design/workspace-skeleton-maximal.md`](../../../../../references/design/workspace-skeleton-maximal.md). This is the canonical shape for a Spring-Boot-Starter, an ASP.NET Core middleware pipeline, an Express plugin, or a Rust `#[proc_macro]` crate that layers on top of a runtime.

- [00-overview/](00-overview/) — Artifact profile and module landscape
- [01-configuration/](01-configuration/) — Auto-configuration and conditional matrix
- [02-core-engine/](02-core-engine/) — Runtime mechanisms (chain of responsibility, strategy, thread-local context)
- [03-extension-points/](03-extension-points/) — Fluid-DSL Builder, SPI contracts, customizer interfaces
- [04-diagrams-specs/](04-diagrams-specs/) — Class + sequence diagrams anchored to the mechanisms above
- [05-classpath-dependencies/](05-classpath-dependencies/) — BOM, transitive exclusions, packaging, semver

The deep-nested layout is the target whenever `system-architect` triggers the maximal-skeleton path — see rule R10 in [`SKILL.md`](../../../../../SKILL.md#known-weaknesses--refactor-mode-rules).
