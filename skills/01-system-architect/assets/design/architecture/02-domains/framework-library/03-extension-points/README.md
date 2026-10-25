---
primary_layer: workflow
---
# 03 — Extension Points

Public seams for consumer teams and third-party plugins. Every seam is a stable contract; every contract has a customizer or SPI here.

- [security-configurer-dsl.md](security-configurer-dsl.md) — Fluid Builder DSL (`http.csrf(...).authorizeHttpRequests(...)…`)
- [customizer-interfaces.md](customizer-interfaces.md) — `Customizer<T>` callback pattern
- [custom-provider-integration.md](custom-provider-integration.md) — hooking third-party `AuthenticationProvider`s
- [extension-points-spi.md](extension-points-spi.md) — canonical extension-point table (moved from the flat layout)
- [public-api-surface.md](public-api-surface.md) — versioned surface list (moved from the flat layout)

Extension points are the *only* seams the consumer is guaranteed to see across framework versions. Adding, renaming, or removing one is a semver-major change — record every mutation as an ADR under `architecture/01-global-strategy/05-governance/decisions/`.
