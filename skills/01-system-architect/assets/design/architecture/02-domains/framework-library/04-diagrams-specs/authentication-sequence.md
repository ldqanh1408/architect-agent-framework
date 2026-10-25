---
primary_layer: content
---
# Authentication — Sequence Diagram

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Diagrams & Specs*

## Table of Contents

- [Summary](#summary)
- [1. Scenario](#1-scenario)
- [2. Diagram](#2-diagram)
- [3. Notable Boundary Behaviours](#3-notable-boundary-behaviours)
- [4. Related Docs](#4-related-docs)

## Summary

Full request flow of an authenticated HTTP request: entry into the Servlet container, dispatch through the framework's filter chain, credential extraction, provider-strategy resolution, and downstream business-handler invocation. This sequence is the *canonical* success path — deviations (401, 403, provider-not-found) are documented in adjacent flow files.

## 1. Scenario

Consumer calls `GET /api/orders/42` with `Authorization: Bearer eyJhbGciOi...` on an application that has enabled the framework's JWT provider through the DSL.

## 2. Diagram

```mermaid
sequenceDiagram
    autonumber
    participant Client as HTTP Client
    participant Servlet as Servlet Container
    participant Proxy as DelegatingFilterProxy
    participant Chain as FilterChainProxy
    participant AuthF as AuthenticationFilter
    participant Manager as ProviderManager
    participant JwtP as JwtAuthenticationProvider
    participant AuthzF as AuthorizationFilter
    participant Handler as OrderController

    Client->>Servlet: GET /api/orders/42 (Bearer …)
    Servlet->>Proxy: doFilter
    Proxy->>Chain: doFilter
    Chain->>Chain: match(request) → chain[0]
    Chain->>AuthF: doFilter
    AuthF->>AuthF: parse Authorization header
    AuthF->>Manager: authenticate(BearerToken)
    Manager->>JwtP: supports(BearerToken.class) → true
    Manager->>JwtP: authenticate(BearerToken)
    JwtP-->>Manager: Authentication (principal, authorities)
    Manager-->>AuthF: Authentication
    AuthF->>AuthF: SecurityContextHolder.setContext(...)
    AuthF->>AuthzF: chain.doFilter()
    AuthzF->>AuthzF: check /api/orders/** requires ROLE_USER
    AuthzF->>Handler: chain.doFilter()
    Handler-->>AuthzF: 200 OrderDto
    AuthzF-->>AuthF: response
    AuthF->>AuthF: SecurityContextHolder.clearContext()
    AuthF-->>Chain: response
    Chain-->>Proxy: response
    Proxy-->>Servlet: response
    Servlet-->>Client: 200 OK
```

## 3. Notable Boundary Behaviours

| Step | Behaviour | Rationale |
|---|---|---|
| Header parse | Missing `Authorization` → `AuthF` continues without setting context; downstream `AuthzF` decides `401` | Anonymous endpoints must still be reachable |
| Provider resolution | No matching `supports()` → `ProviderNotFoundException`, `AuthF` maps to `401` | Silent skip would leak unsigned tokens |
| Context clear | Executed in `finally` block | Prevents leak between requests on reused worker threads |
| Authorization | Uses `Authentication.getAuthorities()` — no re-authentication | Provider state is trusted for the duration of the request |

## 4. Related Docs

- [Filter Chain (Chain of Responsibility)](../02-core-engine/filter-chain-responsibility.md)
- [Authentication Manager (Strategy)](../02-core-engine/authentication-manager-strategy.md)
- [Context ThreadLocal Holder](../02-core-engine/context-threadlocal-holder.md)
- [Core Engine Class Diagram](core-engine-class-diagram.md)
