---
primary_layer: content
---
# Filter Chain — Chain of Responsibility

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Core Engine*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contracts (Interfaces)](#2-contracts-interfaces)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Filter Catalogue](#5-filter-catalogue)
- [6. Related Diagrams](#6-related-diagrams)
- [7. Related Docs](#7-related-docs)

## Summary

Every request the consumer's application receives is dispatched through the framework's custom filter chain before the business handler runs. This page specifies the chain's *identity*, its executor, and the guardrails every filter obeys — so a developer can drop in a new filter without reading the executor's source.

## 1. Runtime Principle

The chain is a Chain-of-Responsibility. A dispatcher (`DelegatingFilterProxy` analogue) hands the request to a `FilterChainProxy`, which selects a `SecurityFilterChain` whose `RequestMatcher` accepts the URL, then walks the chain's ordered filter list via a `VirtualFilterChain`. Each filter has exactly three choices: (a) short-circuit the response, (b) mutate the request/response and continue, or (c) do nothing and continue. There is no fourth option — filters do not "vote", they act.

## 2. Contracts (Interfaces)

```java
package com.example.starter.security.core;

import jakarta.servlet.Filter;

public interface SecurityFilterChain {
    boolean matches(HttpServletRequest request);
    List<Filter> getFilters();
}
```

## 3. Executable Boilerplate

The chain executor. Drop into `com.example.starter.security.core`:

```java
package com.example.starter.security.core;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.util.List;

public class CustomSecurityFilterChainExecutor implements Filter {

    private final List<Filter> securityFilters;

    public CustomSecurityFilterChainExecutor(List<Filter> securityFilters) {
        this.securityFilters = List.copyOf(securityFilters);
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        new VirtualFilterChain(chain, securityFilters).doFilter(request, response);
    }

    private static final class VirtualFilterChain implements FilterChain {
        private final FilterChain originalChain;
        private final List<Filter> additionalFilters;
        private int currentPosition = 0;

        VirtualFilterChain(FilterChain originalChain, List<Filter> additionalFilters) {
            this.originalChain = originalChain;
            this.additionalFilters = additionalFilters;
        }

        @Override
        public void doFilter(ServletRequest request, ServletResponse response)
                throws IOException, ServletException {
            if (currentPosition == additionalFilters.size()) {
                originalChain.doFilter(request, response);
                return;
            }
            Filter nextFilter = additionalFilters.get(currentPosition++);
            nextFilter.doFilter(request, response, this);
        }
    }
}
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Filter order is **positional** | Insertion order == execution order | Filters carry side effects; reordering silently is a source of security incidents |
| A filter must call `chain.doFilter(...)` **at most once** | Enforced by convention | Double-call re-runs downstream filters and business logic |
| Filter list is **immutable** after chain build | `List.copyOf` on construction | Prevents late mutation during a live request |
| Every filter extends `GenericFilterBean` | Enforced by architecture-fitness test | Uniform init/destroy lifecycle |
| Executor's max chain length | 32 filters | Guardrail against accidental fan-out; raise deliberately |

## 5. Filter Catalogue

| Filter | Responsibility | Extends |
|---|---|---|
| `CorsFilter` | Enforces cross-origin policy | `GenericFilterBean` |
| `CsrfFilter` | Verifies CSRF token on state-changing methods | `GenericFilterBean` |
| `AuthenticationFilter` | Extracts credentials from headers; sets `SecurityContextHolder` | `GenericFilterBean` |
| `AuthorizationFilter` | Enforces the ACL derived from the current `Authentication` | `GenericFilterBean` |

## 6. Related Diagrams

- [Core Engine Class Diagram](../04-diagrams-specs/core-engine-class-diagram.md)
- [Authentication Sequence](../04-diagrams-specs/authentication-sequence.md)

## 7. Related Docs

- [Authentication Manager (Strategy)](authentication-manager-strategy.md)
- [Fluid-DSL Configurer](../03-extension-points/security-configurer-dsl.md)
- [Architecture Fitness Tests](../../../../architecture/03-cross-cutting/04-fitness-functions/00-overview.md)
