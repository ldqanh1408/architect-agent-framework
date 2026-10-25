---
primary_layer: content
---
# Public API Surface

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Extension Points*

## Table of Contents

- [Summary](#summary)
- [1. API Boundary Map](#1-api-boundary-map)
- [2. Public Types](#2-public-types)
- [3. Deprecation Policy](#3-deprecation-policy)
- [4. Stability Guarantees](#4-stability-guarantees)
- [5. Related Docs](#5-related-docs)

{{PUBLIC_API_SUMMARY}}

## 1. API Boundary Map

The public surface is the set of packages a consumer can `import`. Everything else is `internal` and can change without notice.

| Package | Kind | Semver commitment |
|---|---|---|
{{API_PACKAGE_ROWS}}

## 2. Public Types

| Type | Kind | Introduced in | Notes |
|---|---|---|---|
{{PUBLIC_TYPE_ROWS}}

## 3. Deprecation Policy

- A public type marked `@Deprecated(since=X)` remains present for at least one minor version after `X`.
- Removal is a semver-major change and requires an ADR under `architecture/01-global-strategy/05-governance/decisions/`.
- Migration guide lives under `05-classpath-dependencies/migration-<X>-to-<Y>.md`.

## 4. Stability Guarantees

- Fluid-DSL entry points (`HttpSecurity`, `Customizer<T>`) are `@API(status = STABLE)`.
- SPI contracts (`AuthenticationProvider`, `SecurityFilterChain`) are `@API(status = STABLE)`.
- Internal helpers (`internal.*`) are `@API(status = INTERNAL)` — importing from `internal.*` triggers an architecture-fitness test failure.

## 5. Related Docs

- [Extension Points / SPI](extension-points-spi.md)
- [Versioning & Compatibility](../05-classpath-dependencies/versioning-compatibility.md)
- [Custom Provider Integration](custom-provider-integration.md)
