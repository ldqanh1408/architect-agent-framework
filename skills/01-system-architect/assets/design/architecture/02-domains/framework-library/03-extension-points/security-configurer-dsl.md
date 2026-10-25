---
primary_layer: content
---
# Security Configurer — Fluid Builder DSL

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Extension Points*

## Table of Contents

- [Summary](#summary)
- [1. Consumer Ergonomics](#1-consumer-ergonomics)
- [2. Contracts (Configurer + Builder)](#2-contracts-configurer--builder)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Init vs Configure Phases](#5-init-vs-configure-phases)
- [6. Related Docs](#6-related-docs)

## Summary

The framework's Fluid-DSL Builder gives consumers a chained, IDE-completable API to compose filters, providers, and cross-cutting policy — without hand-registering beans. This page specifies the Builder contract, the Configurer callback, and the two-phase `init → configure` lifecycle every DSL module obeys.

## 1. Consumer Ergonomics

The DSL is designed so a typical consumer configuration reads as English:

```java
@Configuration
public class MyAppSecurityConfig {

    @Bean
    public SecurityFilterChain customChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            );
        return http.build();
    }
}
```

Nothing outside the Fluid DSL is required to configure filters. If a mechanism cannot be reached through the DSL, that mechanism is a coverage defect on the DSL, not a consumer skill gap.

## 2. Contracts (Configurer + Builder)

```java
package com.example.starter.security.config;

public interface SecurityBuilder<O> {
    O build() throws Exception;
}

public interface SecurityConfigurer<O, B extends SecurityBuilder<O>> {
    void init(B builder) throws Exception;
    void configure(B builder) throws Exception;
}
```

## 3. Executable Boilerplate

```java
package com.example.starter.security.config;

import jakarta.servlet.Filter;
import java.util.ArrayList;
import java.util.List;

public class HttpSecurity implements SecurityBuilder<DefaultSecurityFilterChain> {

    private final List<Filter> filters = new ArrayList<>();
    private final List<SecurityConfigurer<DefaultSecurityFilterChain, HttpSecurity>> configurers = new ArrayList<>();

    public HttpSecurity apply(SecurityConfigurer<DefaultSecurityFilterChain, HttpSecurity> configurer) {
        this.configurers.add(configurer);
        return this;
    }

    public HttpSecurity addFilterAfter(Filter filter, Class<? extends Filter> afterFilter) {
        // Position resolution elided — see Filter Order Registry
        this.filters.add(filter);
        return this;
    }

    @Override
    public DefaultSecurityFilterChain build() throws Exception {
        for (var c : configurers) c.init(this);
        for (var c : configurers) c.configure(this);
        return new DefaultSecurityFilterChain(this.filters);
    }
}
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Builder is single-use | `build()` marks the instance sealed | Re-building against a mutated state produces incoherent chains |
| Configurers are applied in insertion order | Insertion order | Consumers rely on stable filter ordering |
| `init(...)` runs for **all** configurers before any `configure(...)` runs | Two-pass lifecycle | Configurers depend on siblings' registered state; a one-pass loop would force declaration order to matter |
| `apply(...)` returns `this` | Fluent return | Non-fluent return breaks chain readability |

## 5. Init vs Configure Phases

`init(builder)` runs first for every configurer. It registers shared services, wires cross-configurer dependencies, and reserves filter positions. `configure(builder)` runs second, and at this point every configurer is guaranteed to see the fully-populated shared registry. Mutating the shared registry during `configure(...)` is forbidden — it defeats the invariant that `init(...)` establishes.

## 6. Related Docs

- [Customizer Interfaces](customizer-interfaces.md)
- [Filter Chain (Chain of Responsibility)](../02-core-engine/filter-chain-responsibility.md)
- [Authentication Manager (Strategy)](../02-core-engine/authentication-manager-strategy.md)
- [Core Engine Class Diagram](../04-diagrams-specs/core-engine-class-diagram.md)
