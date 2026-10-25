---
primary_layer: content
---
# Customizer Interfaces

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Extension Points*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contract](#2-contract)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Related Docs](#5-related-docs)

## Summary

Customizers are single-method callbacks the consumer passes into DSL methods to tweak a nested builder without leaving the fluent chain. The pattern reduces API surface (one `.csrf(csrf -> csrf.disable())` covers every knob on `CsrfConfigurer`) while preserving IDE completion inside the lambda.

## 1. Runtime Principle

`Customizer<T>` is a `@FunctionalInterface` with one `void customize(T t)` method. The DSL calls each customizer once, immediately, during the `configure(...)` phase of its owning configurer. Customizers are not stored — they run and are discarded. Side effects that outlive the callback (e.g. registering a bean) belong on the builder, not the customizer.

## 2. Contract

```java
package com.example.starter.security.config;

@FunctionalInterface
public interface Customizer<T> {
    void customize(T t);

    static <T> Customizer<T> withDefaults() {
        return t -> {};
    }
}
```

## 3. Executable Boilerplate

Wiring a customizer into a DSL method:

```java
public HttpSecurity csrf(Customizer<CsrfConfigurer<HttpSecurity>> csrfCustomizer) {
    CsrfConfigurer<HttpSecurity> configurer = getOrApply(new CsrfConfigurer<>());
    csrfCustomizer.customize(configurer);
    return this;
}
```

Consumer usage — customize + default form:

```java
http
    .csrf(csrf -> csrf.disable())
    .authorizeHttpRequests(Customizer.withDefaults());
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Customizer runs **exactly once** | Enforced by DSL method | Repeat runs would double-register filters |
| Customizer must not throw checked exceptions | `void` return, unchecked only | Checked exceptions in a lambda force the consumer to wrap every chain |
| `withDefaults()` is the "no-op" | Available on the interface | Consumers should never have to write `t -> {}` themselves |
| Customizer target is a **nested** builder, never the parent | Enforced by generics | Escaping the nested builder makes the DSL non-local |

## 5. Related Docs

- [Fluid-DSL Configurer](security-configurer-dsl.md)
- [Extension Points / SPI](extension-points-spi.md)
