# Workspace Skeleton — Maximal Depth (Actionable Workspace)

The **maximal skeleton** is the deep-nested, numbered-folder layout that turns an SDD output tree from a *read-only reference* into an **Actionable Workspace**: a place where each `.md` sits next to the code contract it drives, and where a developer building a complex multi-module system (custom Spring Boot Starter, browser extension, dynamic-plugin host, third-party integration adapter set) can drill down progressively from **Bounded Context → Module → Concern → Topic → Executable Boilerplate**.

This reference is the canonical target shape for `system-architect` outputs whenever:

- The system spans **two or more bounded contexts** (backend + extension, host + plugins, core + adapters).
- Any single bounded context contains **five or more distinct concerns** (configuration, core engine, extension points, diagrams, dependencies, security, observability, …).
- The user asks for an **executable / boilerplate-rich / DSL-style** design (e.g. "design my own security filter chain", "author a plugin registry", "wrap a payment SDK with an adapter layer").

If none of those hold, a smaller profile (`minimal` or `standard`) applies — still the nested `<cluster>/<submodule>/<skill>/` layout, with fewer contexts and fewer populated slots. If any of them hold, a flat `02-domains` is a coverage defect — you must generate the maximal skeleton below.

## Table of Contents

- [1. Design Principles](#1-design-principles)
- [2. Global Numbering Scheme](#2-global-numbering-scheme)
- [3. Root Layout — Multi-Bounded-Context Workspace](#3-root-layout--multi-bounded-context-workspace)
- [4. Per-Bounded-Context Layout — Deep Nesting](#4-per-bounded-context-layout--deep-nesting)
- [5. Reserved Concern Slots (00–99)](#5-reserved-concern-slots-0099)
- [6. Page Anatomy — Executable Specification](#6-page-anatomy--executable-specification)
- [7. ADR Slot — Architectural Decision Records](#7-adr-slot--architectural-decision-records)
- [8. Fitness Functions Slot](#8-fitness-functions-slot)
- [9. Cross-Context Contracts](#9-cross-context-contracts)
- [10. Anti-Patterns (Coverage Defects)](#10-anti-patterns-coverage-defects)
- [11. Validation Rules](#11-validation-rules)
- [12. Bounded-Context Catalogue](#12-bounded-context-catalogue)
  - [12.1 Frontend / User Surface](#121-frontend--user-surface-00-09-)
  - [12.2 Backend / API Tier](#122-backend--api-tier-10-19-)
  - [12.3 Framework / Library / SDK](#123-framework--library--sdk-20-29-)
  - [12.4 Data / Analytics](#124-data--analytics-30-39-)
    - [12.4b AI / ML Runtime Overlay](#124b-ai--ml-runtime-overlay)
  - [12.5 Infra / Platform](#125-infra--platform-40-49-)
  - [12.6 Extension / Plugin](#126-extension--plugin-50-59-)
  - [12.7 Integration / Adapter](#127-integration--adapter-60-69-)
  - [12.8 Domain / Business Capability](#128-domain--business-capability-70-79-)
  - [12.9 Operations / Observability](#129-operations--observability-80-89-)
  - [12.10 Cross-Cutting Appendices](#1210-cross-cutting-appendices-90-99-)
  - [12.11 Selection Heuristic](#1211-selection-heuristic)
- [13. Catalogue Versioning](#13-catalogue-versioning)
- [14. Growth Ladder and Sub-Module Folderization](#14-growth-ladder-and-sub-module-folderization)
  - [14.1 The growth ladder — what each level generates](#141-the-growth-ladder--what-each-level-generates)
  - [14.2 Sub-module folderization ladder](#142-sub-module-folderization-ladder)

## 1. Design Principles

| # | Principle | What it enforces |
|---|---|---|
| P1 | **One topic per file** | A `.md` describes exactly one mechanism, contract, or artifact. If a page passes the 220-line review threshold or introduces a second independently versioned topic or contract, split it into its own file inside a sibling folder (hard cap 400 lines, V-MAX-6). |
| P2 | **Numbered folders reflect reading order** | `00-…` is always the entry / overview slot; higher numbers add depth. Numbers are stable — new concerns are appended, never renumbered. |
| P3 | **Folder = namespace, file = topic** | Any `.md` that would sit alone without siblings *and* whose subject can conceivably grow (protocol version 2, new adapter target, additional filter) must live inside a dedicated folder that acts as its namespace. |
| P4 | **Executable boilerplate belongs next to its spec** | The Markdown that describes a mechanism must also carry the source-code skeleton a developer copies to start implementing it. If snippets encode behaviour, they *are* the specification (see R2 in `SKILL.md`). |
| P5 | **ADRs and fitness functions are first-class slots** | The workspace reserves `01-global-strategy/05-governance/decisions/` (system ADR log) and `03-cross-cutting/04-fitness-functions/` (guardrail rules, one file per rule). Removing either is a coverage defect. |
| P6 | **Depth over dilution** | Prefer three levels of folders over one flat directory with mixed concerns. Flat directories are how detail gets lost. |
| P7 | **Diagrams live under the concern they describe** | UML/Mermaid class, sequence, and state diagrams live inside the concern's own folder (or under `03-diagrams-specs/` inside the module), not in the shared root `uml/` bucket — the shared bucket keeps *system-wide* diagrams only. |
| **P8** | **One definition, three consumers** | The skeleton exists once, machine-readably, in `architect_framework/data/workspace_skeleton.yaml` (`contracts.workspace_skeleton()`). This document, the scaffolder and `architect-runtime sdd check <workspace> --full` read it; none of them restates it. A slot absent from the manifest cannot be generated, and a manifest slot that is never generated is a validator failure rather than a footnote. |
| **P9** | **Every view names its audience; every concern gets a view** | Coverage is measured over stakeholder concerns, not artifact types. `00-viewpoints/` makes the join possible, and the C4-level checklist becomes a consequence of concern coverage rather than the goal itself (ISO/IEC/IEEE 42010 Section 5). |
| **P10** | **Structure scales by adding levels, never by moving files** | Growth from one service to a portfolio adds slots, indexes and a segment manifest under paths that already existed. A promotion that requires a `git mv` of a spec page is a design bug in the skeleton, not a migration task for the user. |
| **P11** | **A slot is created by evidence, not by template** | The manifest declares which slots *exist*; evidence decides which are *populated*. The case that produces empty trees is the fifth one: a slot that applies but that you have nothing to say about yet is not created at all. |

## 2. Global Numbering Scheme

Numbers are two-digit and sorted lexicographically. Reserved ranges:

| Range | Meaning |
|---|---|
| `00-` | Overview / entry / index for the enclosing scope |
| `01-`–`09-` | Structural concerns (configuration, core engine, extension points, dependencies) |
| `10-`–`19-` | Runtime concerns (lifecycle, communication, state, scheduling) |
| `20-`–`29-` | Cross-cutting concerns (security, observability, resilience, i18n) |
| `30-`–`39-` | Delivery concerns (packaging, versioning, rollout, compatibility) |
| `90-`–`99-` | Reserved: `90-appendices/`, `99-scratch/` (never shipped, gitignored) |

Bounded-context folders at the workspace root use the same scheme (`00-web-app/`, `01-spring-boot-starter/`, `02-browser-extension/`, …) so the reading order of contexts is stable across projects.

## 3. Root Layout — Multi-Bounded-Context Workspace

This tree is rendered from `architect_framework/data/workspace_skeleton.yaml`, which is the single definition. When the two disagree, the manifest wins and this section is stale — do not patch one without the other.

```text
documents/
├── sdd-workspace.yml
├── index.md                              # master TOC — must reach every leaf
├── architecture/00-system-views/                       # arc42 §3, arc42 §6, arc42 §7 · C4 · ISO 42010
│   ├── 00-viewpoints/                    # [42010] the register that makes concern coverage checkable
│   │   ├── viewpoint-catalog.md          #   VP-xxx: concerns framed, model kinds, notation
│   │   ├── stakeholder-concern-matrix.md #   STK-xxx x concern x the view that answers it
│   │   └── correspondence-rules.md       #   COR-xxx: which views must agree, and on what
│   ├── c0-landscape.md                   # C4 System Landscape — portfolio level only
│   ├── c1-context.md                     # C4 L1 system context (business language, no tech)
│   ├── c2-container.md                   # C4 L2 canonical deployable/runnable units
│   ├── logical-l2-submodules.md          # house Logical L2 — bounded-context map
│   ├── c4-deployment.md                  # C4 deployment view (infra prose lives in 03-cross-cutting)
│   ├── container-module-mapping.md       # generated many-to-many C2 <-> Logical L2 join
│   ├── 06-runtime/                       # [arc42 §6] 1–5 scenarios, no more
│   │   ├── 00-scenario-index.md          #   SCN-xxx -> QS-xxx -> building blocks traversed
│   │   └── SCN-NNN-<slug>.md             #   narrative + dynamic diagram + failure branch
│   ├── visual-source-map.md              # source map consumed by context-diagram … class-diagram
│   └── generated/                        # derived renders — disposable, never a second SSoT
├── architecture/01-global-strategy/                    # arc42 §1, arc42 §2, arc42 §4, arc42 §9, arc42 §10, arc42 §11, arc42 §12 · TOGAF Repository
│   ├── 00-context/
│   │   ├── problem-brief.md
│   │   ├── goals-non-goals.md
│   │   ├── assumptions.md                # ASM-xxx — the Assumed route of the evidence boundary
│   │   └── glossary.md                   # arc42 §12 — system-wide ubiquitous language
│   ├── 01-requirements/                  # [TOGAF] Architecture Requirements Repository
│   │   ├── requirements.md
│   │   ├── constraints.md                # arc42 §2 — a requirements-side input, not a strategy output
│   │   └── quality-attributes.md         # arc42 §10 — QS-xxx; what fitness functions join on
│   ├── 02-strategy/
│   │   ├── architecture-principles.md
│   │   ├── solution-strategy.md
│   │   └── technology-selection.md       # [TOGAF] Solutions Landscape entry
│   ├── 03-standards/                     # [TOGAF] Standards Library
│   │   ├── standards-register.md         #   STD-xxx | domain | status | scope | owner | source
│   │   └── <topic>-standards.md          #   only when a register row is insufficient
│   ├── 04-risks/
│   │   ├── risk-register.md              # arc42 §11 first half
│   │   └── technical-debt.md             # arc42 §11 second half — usually dropped
│   ├── 05-governance/                    # [TOGAF] Governance Repository
│   │   ├── decisions/                    #   system ADR log — 0000-…, 0001-…, 0002-…
│   │   └── compliance-log.md             #   assessments, findings, standards deviations
│   ├── architecture.md                   # topology view (all zones, all contexts) + Submodule Suffix Registry
│   ├── docs-as-code-rationale.md         # three-layer model + Docs-as-Code choice & transition triggers
│   └── composition-root.md               # entry point, DI/wiring graph, root routing (required when any module is app-lifecycle)
├── architecture/02-domains/                            # arc42 §5 — EVERY hexagon lives here
│   ├── 00-overview/
│   │   └── domains-index.md              # mandatory at >=5 domains; grouped by module_role into <=9 groups
│   ├── _shared-kernel/                   # system hexagon core + ports (Knob K-F local-first: promote at >=2 consumers + ADR)
│   ├── _shared-adapters/                 # system hexagon outer ring — inbound/ and outbound/
│   ├── _shared-contracts/                # canonical cross-domain contracts, single writer
│   │   ├── 00-core/                      # contract overview + cross-context flows
│   │   │   └── flows/
│   │   ├── 01-data/
│   │   ├── 02-apis/
│   │   ├── 03-messages/
│   │   ├── 04-external/
│   │   └── 05-state-machines/
│   └── 03_application_architecture/      # <cluster> — one folder per cluster that has a selected skill
│       ├── 00-web-app/<skill>/           # <NN-submodule>/<skill>: bounded context 1
│       ├── 01-spring-boot-starter/<skill>/   # bounded context 2
│       ├── 02-browser-extension/<skill>/ # bounded context 3
│       ├── 03-dynamic-plugins/<skill>/   # bounded context 4
│       └── 04-integration-adapters/<skill>/  # bounded context 5
├── architecture/03-cross-cutting/                      # arc42 §8 / arc42 §10 — spans >=2 domains
│   ├── 00-overview.md                    # concept index by category — arc42 FAQ C-8-2
│   ├── 01-mechanisms/
│   ├── 02-security/
│   ├── 03-infrastructure/                # deployment prose: nodes, sizing, IaC, runbooks
│   ├── 04-fitness-functions/             # a DIRECTORY, not one file
│   │   ├── 00-overview.md                # quality tree: goal -> scenario -> rule
│   │   └── FIT-NNN-<slug>.md             # one file per enforceable rule; cites QS-xxx and STD-xxx
│   └── 05-reference-library/             # [TOGAF] Reference Library — patterns/ reference-models/ templates/
└── architecture/04-delivery/                           # planning, quality, release, ops, audit
```

Two entries in `02-domains/00-overview/` carry more weight than their size suggests:

- **`context-map.md`** — every edge must carry a DDD relationship pattern and a direction. The pattern is what generates work downstream: a `conformist` edge means no adapter and accepted coupling, an `anticorruption-layer` edge means an integration-adapter module is required rather than optional. Untyped edges are why the same system decomposes differently on two runs.
- **`segments.md`** — TOGAF's Segment level, present only at the `portfolio` level, and deliberately a *manifest* rather than a folder tier. Making segments folders would push every context down one level, breaking P2, invalidating every `source-map.yml`, and breaking the tier-range logic in the deterministic skeleton validator (`architect-runtime sdd check <workspace> --full`). The tier ranges already partition the landscape; what was missing was that the partition had no artifact.

**The three kinds of `02-domains/` child.** Validators branch on `module_role`, never on the presence of a
number:

| Kind | Naming | Reserved concern slots apply? | `module_charter` row | Hexagon? | Owner |
|---|---|---|---|---|---|
| Shared slot | `_shared-kernel/`, `_shared-adapters/`, `_shared-contracts/` — the registered `_`-prefixed set declared in `registered planning artifact` | No | No | Part of the **system** hexagon | orchestrator |
| Bounded context | `<cluster>/<submodule>/<skill>/` | Yes — Section 5 slots, P1–P7, V-MAX | Yes, with `module_role` + `@<CODE>` | Yes | router-selected exported skill (Section 12.1–12.9) |
| Appendix module | `<cluster>/<submodule>/<skill>/` | Partially — `00-overview/` required, hexagon slots not | Yes, `module_role: appendix` | No | `23-appendix-architect` (hint, Section 12.10) |

Adding a fourth `_`-slot requires an ADR; an unregistered `02-domains/_<slug>/` is a finding.

Each bounded context under `architecture/02-domains/` is itself a full workspace-in-miniature and follows Section 4.

## 4. Per-Bounded-Context Layout — Deep Nesting

Applied to a custom Spring-Boot-Starter security framework (the canonical example the maximal skeleton was designed against):

```text
architecture/02-domains/03_application_architecture/01-spring-boot-starter/library-sdk-architect/
├── 00-overview/
│   └── starter-overview.md               # what the artifact is, who consumes it
├── 01-configuration/
│   ├── auto-configuration.md             # @AutoConfiguration + spring.factories
│   └── conditional-matrix.md             # @ConditionalOn… truth table
├── 02-core-engine/
│   ├── filter-chain-responsibility.md    # Chain-of-Responsibility spec + boilerplate
│   ├── authentication-manager-strategy.md# Strategy pattern spec + boilerplate
│   └── context-threadlocal-holder.md     # SecurityContextHolder analogue
├── 03-extension-points/
│   ├── security-configurer-dsl.md        # Fluid Builder DSL spec + boilerplate
│   ├── customizer-interfaces.md          # Customizer<T> callback contracts
│   └── custom-provider-integration.md    # 3rd-party provider hookup
├── 04-diagrams-specs/
│   ├── core-engine-class-diagram.md      # Mermaid classDiagram — patterns overlay
│   └── authentication-sequence.md        # Mermaid sequenceDiagram — request flow
└── 05-dependencies/                  # JVM presentation alias: 05-classpath-dependencies
    ├── dependency-management.md          # BOM, dependencyManagement block
    └── transitive-exclusions.md          # forbidden transitives + why
```

Applied to a Chrome extension:

```text
architecture/02-domains/03_application_architecture/02-browser-extension/plugin-extension-architect/
├── 00-overview/
│   └── extension-overview.md
├── 01-manifest-security/
│   ├── manifest-v3-spec.md               # manifest.json boilerplate + permission rationale
│   └── permission-matrix.md
├── 02-runtime-execution/
│   ├── service-worker-bg.md
│   └── content-script-dom.md
└── 03-communication/
    ├── message-passing-protocol.md
    └── storage-sync-state.md
```

Applied to a dynamic-plugin host:

```text
architecture/02-domains/03_application_architecture/03-dynamic-plugins/plugin-extension-architect/
├── 00-overview/
│   └── plugin-overview.md
├── 01-host-contracts/
│   ├── host-api-interfaces.md            # IHostAPI Java interface + JavaDoc
│   └── dynamic-classloaders.md
├── 02-lifecycle/
│   ├── lifecycle-state-machine.md        # Mermaid stateDiagram
│   └── registry-discovery.md
└── 03-sandbox-security/
    ├── resource-quotas.md
    └── permission-scopes.md
```

Applied to third-party integration adapters:

```text
architecture/02-domains/03_application_architecture/04-integration-adapters/integration-adapter-architect/
├── 00-overview/
│   └── integration-overview.md
├── 01-adapters/
│   ├── target-interfaces.md              # IPaymentGatewayAdapter contract
│   └── composition-wrappers.md           # StripeSdkWrapper boilerplate
├── 02-data-mappings/
│   ├── conversion-rules.md
│   ├── exception-translations.md
│   └── validation-rules.md
└── 03-resilience/
    ├── retry-backoff-config.md
    └── circuit-breaker-specs.md
```

## 5. Reserved Concern Slots (00–99)

Inside a bounded context the following slot names are canonical. Mandatory slots exist with content. Conditional slots are populated only with source evidence; a required seam without enough evidence gets a blocked `README.md` naming the exact question, while a non-applicable slot is omitted and its rationale is recorded in the context overview. Slot numbers remain reserved in the catalogue without requiring empty physical folders.

| Slot | Purpose | Typical file(s) |
|---|---|---|
| `00-overview/` | Entry page for the context — profile table, module landscape diagram | `<context>-overview.md`, `ubiquitous-language.md` |
| `01-configuration/` | Static configuration surface | `auto-configuration.md`, `conditional-matrix.md`, `defaults.md` |
| `02-core-engine/` | The heart of the artifact — mechanisms, patterns, algorithms. Presents as `02-domain-model/` when `module_charter.module_role` is `domain` | one file per pattern / responsibility; for a domain context, per aggregate / invariant / policy |
| `03-extension-points/` | Public SPI + Builder DSL surface | `spi-contracts.md`, `dsl-builder.md`, `customizer-interfaces.md` |
| `04-diagrams-specs/` | Context-scoped UML + sequence + state diagrams | `class-diagram.md`, `sequence-<flow>.md` |
| `05-dependencies/` | Stack-neutral dependency policy; JVM may present `05-classpath-dependencies`, Node `05-node-modules-dependencies`, Rust `05-crate-dependencies` | `dependency-management.md`, `transitive-exclusions.md` |
| `10-lifecycle/` | State machines, start-up / shut-down, hot-reload | `lifecycle-state-machine.md`, `startup-order.md` |
| `11-communication/` | Message passing, RPC, event contracts | `message-passing-protocol.md`, `event-catalog.md` |
| `20-security/` | Auth, encryption, secrets, sandbox | `permission-scopes.md`, `secret-storage.md` |
| `21-observability/` | Logs, metrics, traces, MDC keys | `mdc-keys.md`, `metric-catalog.md`, `trace-attributes.md` |
| `22-resilience/` | Retry, backoff, circuit breaker, bulkhead | `retry-backoff-config.md`, `circuit-breaker-specs.md` |
| `30-packaging/` | JAR/NPM/DEB/… layout, entry points, manifest | `packaging-distribution.md` |
| `31-versioning/` | SemVer, deprecation, migration guides | `versioning-compatibility.md`, `migration-<N>-to-<N+1>.md` |
| `90-appendices/` | Glossary, alternatives-considered, external references | `glossary.md`, `alternatives.md` |

Unused numbers are fine — you can jump from `03-` to `10-`. Never renumber to close a gap.

## 6. Page Anatomy — Executable Specification

Every leaf `.md` inside a bounded context follows the base contract in `template-standard.md` **plus** two extra sections when the page describes a mechanism:

```markdown
# <Mechanism title>


## Table of Contents
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contracts (Interfaces / Abstract Classes)](#2-contracts-interfaces--abstract-classes)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Related Diagrams](#5-related-diagrams)
- [6. Related Docs](#6-related-docs)

## Summary
One paragraph — what mechanism this page decides.

## 1. Runtime Principle
Prose + optional Mermaid — how the mechanism behaves at runtime.

## 2. Contracts (Interfaces / Abstract Classes)
Language-appropriate declarations (Java interface, TypeScript type, Rust trait…) — the *identity* of the mechanism.

## 3. Executable Boilerplate
A copy-pasteable skeleton the developer starts from. Not illustrative — this **is** the spec (see SKILL.md R2).

## 4. Guardrails and Defaults
Normative defaults (timeouts, thread limits, clock skew, retry counts) as a table. Every default has a rationale column.

## 5. Related Diagrams
Cross-links to the diagrams under `04-diagrams-specs/` that visualise this mechanism.

## 6. Related Docs
Cross-links to the ADR that decided this mechanism and the fitness test that enforces it.
```

Mechanism pages that omit either **Section 3 Executable Boilerplate** or **Section 4 Guardrails and Defaults** are treated as *stub* pages and fail the self-audit.

## 7. ADR Slot — Architectural Decision Records

Every bounded context reserves `architecture/01-global-strategy/05-governance/decisions/` at the workspace root for its decisions; a context-only decision is an ADR there that names the context in its title. No ADR folder is created under `02-domains/`.

- Filename: `NNNN-<slug>.md` where NNNN is a monotonic four-digit sequence starting at `0001`.
- Status lifecycle: `PROPOSED → ACCEPTED → SUPERSEDED-BY-NNNN | DEPRECATED`.
- Every mechanism page in Section 6 links to its enabling ADR in the **Related Docs** section.

Template lives at `architecture/01-global-strategy/05-governance/decisions/ADR-TEMPLATE.md`. Copy, rename to the next number, fill the sections. Never mutate an ACCEPTED ADR — supersede it with a new one.

## 8. Fitness Functions Slot

`architecture/03-cross-cutting/04-fitness-functions/00-overview.md` collects the *guardrail* tests that the CI pipeline runs on every commit to protect the boundaries this SSoT declared. Typical targets:

- Layer isolation (`core` must not import `infrastructure`).
- Extension-point purity (`Filter`-suffixed classes must extend the base class chosen in Section 4 of the filter-chain spec).
- Circular-dependency ban (no cycles between packages that map to bounded contexts).
- Third-party SDK containment (business-tier packages must not import vendor SDK types directly — go through Adapter wrappers, see integration-adapters context).

The page ships ready-to-drop code in the project's fitness-test framework (ArchUnit for JVM, `dependency-cruiser` for TypeScript, `import-linter` for Python). Extending the guardrail set is a two-line change per rule.

## 9. Cross-Context Contracts

When two bounded contexts talk to each other, the *contract* between them lives in `architecture/02-domains/_shared-contracts/` at the workspace root, **not** inside either context. Each side then keeps a stub page under its own `03-extension-points/` (or `11-communication/`) that reads:

```markdown
## Summary
This context consumes / exposes API-017, defined in [../../../architecture/02-domains/_shared-contracts/02-apis/api-017-user-sync.md].
Local adapter code lives in `02-core-engine/user-sync-adapter.md`.
```

This prevents duplication and gives `spec-critic` a single place to check version compatibility.

## 10. Anti-Patterns (Coverage Defects)

The following shapes are treated as coverage defects by `self-audit.md` and by `spec-critic`:

| Anti-pattern | Why it fails | Remedy |
|---|---|---|
| Flat `<context>/*.md` with 6+ files | Loses drill-down; contracts and mechanisms sit at the same level | Split into `00-…/`, `01-…/`, `02-…/` per Section 4 |
| One monolithic `architecture.md` for a multi-context system | Erases per-context topology and cross-zone boundaries | Keep the shared `architecture/01-global-strategy/architecture.md` for topology only; move context detail into each `architecture/02-domains/<cluster>/<NN-submodule>/<skill>/00-overview/` |
| Mechanism page without Section 3 boilerplate | Behaviour dropped as "implementation trivia" | Add the copy-pasteable skeleton (Java/TS/Rust) |
| Mechanism page without Section 4 defaults table | Guard values become tribal knowledge | Add every default (timeout, size, skew) with rationale |
| ADRs stored inline inside overview pages | Cannot be superseded independently | Move each decision into its own `NNNN-<slug>.md` under `05-governance/decisions/` |
| Diagrams stored only in the root `uml/` folder | Context reader has to jump to a different subtree to see the picture | Duplicate context-scoped diagrams under `04-diagrams-specs/` (link, don't fork) |
| Renumbered folders after the fact | Breaks stable cross-links from downstream skills | Append new numbers; never renumber to fill gaps |

## 11. Validation Rules

Run `architect-runtime sdd check <workspace> --full` after generation. In addition to the base rules, the following are added when the maximal skeleton is active:

- **V-MAX-1** — Every folder whose name matches `^\d{2}-` contains at least one `.md` or a `README.md` describing the slot. This includes the bounded-context module root itself (`architecture/02-domains/<cluster>/<skill>/README.md`), not only its concern-slot subfolders — a child skill's own `## Skeleton` example must show this file explicitly, or agents following the example literally will fail this check on first attempt (confirmed via a live eval pilot, see `completion-plan.md` Phase 1.2).
- **V-MAX-2** — Every bounded context under `architecture/02-domains/` contains a `00-overview/` folder and an overview page named `<context-slug>-overview.md`.
- **V-MAX-3** — Every mechanism page (any file whose filename ends in `-strategy.md`, `-responsibility.md`, `-dsl.md`, `-state-machine.md`, `-protocol.md`) has both an `## Executable Boilerplate` and a `## Guardrails and Defaults` heading.
- **V-MAX-4** — Every ADR file matches `^\d{4}-[a-z0-9-]+\.md$` and starts with a `Status:` line.
- **V-MAX-5** — `architecture/03-cross-cutting/04-fitness-functions/00-overview.md` exists whenever `architecture/02-domains/` contains two or more contexts.
- **V-MAX-6** — generated content has a soft review threshold of 220 lines and a hard cap of 400 lines. Split earlier whenever a second independently versioned topic or contract appears.
- **V-MAX-7** — `registered planning artifact` contains `planning metadata: catalogue_version` matching this document's current catalogue version.

Downstream skills (`context-diagram`, `class-diagram` and the other diagram task skills) read the numbered folders directly; keeping the numbers stable is what lets them find their input without a manifest lookup.

## 12. Bounded-Context Catalogue

A large system usually contains **more than a handful** of bounded contexts. The four examples in Section 4 are illustrative, not exhaustive. Pick from the catalogue below when scaffolding `architecture/02-domains/`; each row lists the canonical folder slug, the module's role, and the inner concern slots the module almost always needs. Slot numbers between contexts are independent — two contexts can both use `01-configuration/` without conflict.

Assign each context an outer two-digit prefix (`00-`, `01-`, `02-`, …) reflecting the reading order you want. Reserved outer-prefix ranges:

| Outer range | Tier | Reading intent |
|---|---|---|
| `00-`–`09-` | Frontend / user surface | The thing users see first |
| `10-`–`19-` | Backend / API tier | Server-side business logic |
| `20-`–`29-` | Framework / library / SDK | Reusable code shipped elsewhere |
| `30-`–`39-` | Data / analytics | Warehouse, pipelines, ML |
| `40-`–`49-` | Infra / platform | Kubernetes, mesh, deployment code |
| `50-`–`59-` | Extension / plugin | Extensibility surfaces |
| `60-`–`69-` | Integration / adapter | Third-party SDK wrappers |
| `70-`–`79-` | Domain / business capability | Cart, ledger, fraud, KYC |
| `80-`–`89-` | Operations / observability | Log/metric/trace/alert plumbing |
| `90-`–`99-` | Cross-cutting appendices | Glossary, alternatives, decisions log |

### 12.1 Frontend / User Surface (`00-`–`09-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `00-` | `web-app` | SPA / SSR web application (Next.js, Nuxt, SvelteKit, Remix) | `01-ui-components/`, `02-routing-navigation/`, `03-data-api/`, `04-state-management/`, `20-security/` |
| `01-` | `admin-dashboard` | Internal ops console with elevated privileges | `01-ui-components/`, `02-role-permission/`, `03-audit-log-ui/`, `20-security/` |
| `02-` | `marketing-site` | Public brochureware, SEO/SSG-heavy | `01-pages-cms/`, `02-seo-schema/`, `03-analytics-tags/`, `21-observability/` (Core Web Vitals) |
| `03-` | `mobile-app` | iOS/Android/React Native/Flutter/KMP client | `01-navigation-graph/`, `02-offline-sync/`, `03-push-registration/`, `10-lifecycle/`, `20-security/` (keychain, biometric) |
| `04-` | `desktop-app` | Electron/Tauri/JavaFX/WPF desktop client | `01-window-shell/`, `02-ipc-main-renderer/`, `03-auto-update/`, `30-packaging/` (installers, notarisation) |
| `05-` | `browser-extension` | Chrome MV3 / Firefox WebExtension | `01-manifest-security/`, `02-runtime-execution/` (SW + content scripts), `03-communication/` (messaging + storage) |
| `06-` | `ide-plugin` | VS Code / JetBrains / Neovim extension | `01-command-palette/`, `02-language-services/` (LSP client), `03-editor-integration/`, `30-packaging/` |
| `07-` | `tv-kiosk-ui` | Set-top-box, kiosk, POS terminal, in-car unit | `01-focus-navigation/` (D-pad / remote), `02-hardware-integration/`, `03-lockdown-shell/`, `20-security/` |
| `08-` | `design-system` | Shared UI tokens + component library published as a package | `01-tokens/`, `02-primitives/`, `03-patterns/`, `04-a11y-contracts/`, `31-versioning/` |
| `09-` | `chatbot-widget` | Embedded chat / voice-assistant surface | `01-widget-loader/`, `02-conversation-protocol/`, `03-transport-layer/` (WebSocket/SSE) |

### 12.2 Backend / API Tier (`10-`–`19-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `10-` | `api-gateway` | Single ingress: routing, quota, JWT introspection | `01-route-matrix/`, `02-auth-quota/`, `21-observability/`, `22-resilience/` |
| `11-` | `bff-service` | Backend-for-frontend, one per client surface | `01-response-shaping/`, `02-downstream-aggregation/`, `03-caching-policy/` |
| `12-` | `public-api-service` | External REST/GraphQL surface with a stability contract | `01-versioning-lifecycle/`, `02-rate-limit-policy/`, `03-partner-tenancy/`, `31-versioning/` |
| `13-` | `graphql-federation` | Apollo Router / Mesh federation with subgraphs | `01-subgraph-registry/`, `02-composition-rules/`, `03-schema-checks/`, `04-persisted-queries/` |
| `14-` | `grpc-internal-service` | Protobuf-first service in the mesh | `01-proto-contracts/`, `02-code-generation/`, `03-deadline-cancel/`, `22-resilience/` (retry budget) |
| `15-` | `webhook-dispatcher` | Outbound webhook fan-out with signing + replay | `01-subscription-registry/`, `02-signing-verification/`, `03-delivery-retry/`, `21-observability/` |
| `16-` | `background-jobs` | Async worker / cron / Sidekiq / Temporal | `01-job-registry/`, `02-idempotency/`, `03-scheduling/`, `22-resilience/` (retry, dead-letter) |
| `17-` | `realtime-service` | WebSocket / SSE / MQTT hub | `01-connection-model/`, `02-presence-broadcast/`, `03-backpressure/`, `22-resilience/` |
| `18-` | `search-service` | Elastic/OpenSearch/Meilisearch/Typesense front | `01-index-mapping/`, `02-query-dsl/`, `03-relevance-tuning/`, `04-reindex-strategy/` |
| `19-` | `recommendation-service` | Feature-store-driven ranking / retrieval | `01-feature-store/`, `02-candidate-generation/`, `03-ranker-model/`, `21-observability/` |

### 12.3 Framework / Library / SDK (`20-`–`29-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `20-` | `spring-boot-starter` | Custom auto-configured JVM library (see Section 4 worked example) | `01-configuration/`, `02-core-engine/`, `03-extension-points/`, `04-diagrams-specs/`, `05-dependencies/` (JVM alias: `05-classpath-dependencies/`) |
| `21-` | `node-middleware-framework` | Express/Fastify/Koa middleware pipeline shipped as a package | `01-registration-api/`, `02-middleware-order/`, `03-request-context/`, `04-typescript-types/` |
| `22-` | `dotnet-source-generator` | Roslyn analyser / source generator NuGet | `01-analyzer-rules/`, `02-generation-templates/`, `03-diagnostic-ids/`, `04-msbuild-integration/` |
| `23-` | `python-sdk` | pip-installable client library / typed data classes | `01-client-facade/`, `02-transport-layer/`, `03-pagination-retry/`, `04-typing-contracts/` |
| `24-` | `go-module` | Idiomatic Go library with functional-options constructors | `01-public-surface/`, `02-error-taxonomy/`, `03-context-propagation/`, `31-versioning/` |
| `25-` | `rust-crate` | `#[proc_macro]` or runtime crate published on crates.io | `01-public-surface/`, `02-macro-derivations/`, `03-msrv-matrix/`, `31-versioning/` |
| `26-` | `cli-tool` | Standalone command-line binary with subcommands | `01-command-tree/`, `02-flag-parsing/`, `03-config-precedence/`, `30-packaging/` (homebrew, scoop, apt) |
| `27-` | `codegen-library` | OpenAPI/GraphQL/Protobuf → source code generator | `01-input-schemas/`, `02-template-engine/`, `03-output-conventions/`, `04-plugin-system/` |
| `28-` | `test-fixtures-lib` | Shared factories, matchers, container harness | `01-factory-builders/`, `02-matchers-dsl/`, `03-container-lifecycle/` |
| `29-` | `common-domain-lib` | Shared domain primitives (Money, Currency, PhoneNumber, TenantId) | `01-value-objects/`, `02-serialisation/`, `03-invariants/`, `31-versioning/` |

### 12.4 Data / Analytics (`30-`–`39-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `30-` | `data-warehouse` | Snowflake/BigQuery/Redshift schema + governance | `01-schema-modelling/`, `02-security-classification/`, `03-cost-controls/`, `04-lineage/` |
| `31-` | `batch-etl-pipeline` | Airflow/dbt/Dagster DAGs | `01-source-manifests/`, `02-transformations/`, `03-tests-freshness/`, `21-observability/` (SLA metrics) |
| `32-` | `streaming-pipeline` | Kafka/Flink/Kinesis/Beam topology | `01-topic-catalogue/`, `02-schema-registry/`, `03-stream-processors/`, `22-resilience/` (exactly-once, DLQ) |
| `33-` | `cdc-pipeline` | Debezium/Datastream change capture | `01-source-connectors/`, `02-topology-projection/`, `03-schema-evolution/` |
| `34-` | `reverse-etl` | Warehouse → Salesforce/HubSpot/… sync (Hightouch/Census) | `01-model-selectors/`, `02-destination-mappings/`, `03-sync-strategies/` |
| `35-` | `ml-training-pipeline` | Kubeflow/Vertex/SageMaker training + registry | `01-feature-pipeline/`, `02-training-loop/`, `03-experiment-tracking/`, `04-model-registry/` |
| `36-` | `ml-inference-service` | Online prediction service | `01-model-loading/`, `02-request-batching/`, `03-shadow-canary/`, `21-observability/` (drift) |
| `37-` | `rag-pipeline` | Embedding + vector-store + retrieval + guardrails | `01-ingestion-chunking/`, `02-embedding-model/`, `03-retriever-rerank/`, `04-guardrails/` |
| `38-` | `experimentation-platform` | A/B testing, feature-flag-driven experiments | `01-assignment-service/`, `02-metric-catalogue/`, `03-power-analysis/`, `04-guardrail-metrics/` |
| `39-` | `analytics-collection` | Event-tracking SDK + ingestion sink | `01-event-taxonomy/`, `02-client-sdks/`, `03-ingestion-endpoint/`, `04-schema-registry/` |

#### 12.4b AI / ML Runtime Overlay

AI and RAG runtime systems are composite by default; do not force the whole system into the data tier because it uses a model. Each owner below runs when its skill slot is filled; an empty slot leaves a `SKILL-SLOT-EMPTY` seam instead of that subtree.

| Runtime concern | Owning skill (selected exported package) | Canonical location |
|---|---|---|
| Online HTTP/gRPC inference endpoint, tenant isolation, request auth, retry budget, PII redaction before serving | `backend-service-architect` (routing hint `15-backend-service-architect`) | `architecture/02-domains/03_application_architecture/<NN-submodule>/backend-service-architect/` or the service-specific module slug |
| Training, feature generation, model registry, promotion criteria, drift measurement, offline evals | `data-platform-architect` (routing hint `17-data-platform-architect`) | `architecture/02-domains/05_data_architecture/<NN-submodule>/data-platform-architect/` |
| RAG ingestion, chunking, embeddings, vector index, recall evaluation | `data-platform-architect` (routing hint `17-data-platform-architect`) | `architecture/02-domains/05_data_architecture/<NN-submodule>/data-platform-architect/rag/` |
| LLM/provider wrapper, streaming protocol, tool-use adapter, vendor cost controls | `integration-adapter-architect` (routing hint `20-integration-adapter-architect`) | `architecture/02-domains/03_application_architecture/<NN-submodule>/integration-adapter-architect/` |
| Chat/completion business endpoint that composes retrieval + LLM adapter + policy checks | `backend-service-architect` (routing hint `15-backend-service-architect`) | backend service module with `11-api/` and `20-security/` |

The orchestrator records this split in `architecture/01-global-strategy/05-governance/decisions/NNNN-ai-runtime-ownership.md` whenever more than one of the rows above is present. Cross-tier seams live under `architecture/02-domains/_shared-contracts/`: endpoint API in `architecture/02-domains/_shared-contracts/02-apis/`, model-registry data contract in `architecture/02-domains/_shared-contracts/01-data/`, vector-index freshness contract in `architecture/02-domains/_shared-contracts/01-data/`, and provider adapter port in `architecture/02-domains/_shared-contracts/02-apis/`.

### 12.5 Infra / Platform (`40-`–`49-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `40-` | `terraform-module` | Reusable HCL module | `01-input-outputs/`, `02-resource-graph/`, `03-provider-versions/`, `31-versioning/` |
| `41-` | `helm-chart` | Kubernetes deployment package | `01-values-schema/`, `02-templates/`, `03-hooks/`, `31-versioning/` |
| `42-` | `k8s-operator` | Custom controller + CRD | `01-crd-schema/`, `02-reconcile-loop/`, `03-status-conditions/`, `22-resilience/` (backoff, leader election) |
| `43-` | `service-mesh-config` | Istio/Linkerd routing + mTLS | `01-virtual-services/`, `02-authorization-policy/`, `03-mtls-scope/` |
| `44-` | `ci-cd-pipeline` | GitHub Actions / Buildkite reusable workflows | `01-build-jobs/`, `02-test-strategy/`, `03-release-gate/`, `04-artifact-signing/` |
| `45-` | `sidecar-proxy` | Envoy/nginx/custom sidecar for legacy services | `01-config-generation/`, `02-listener-chain/`, `03-metrics-export/` |
| `46-` | `secrets-management` | Vault / SOPS / KMS envelope-encryption layout | `01-secret-taxonomy/`, `02-rotation-policy/`, `03-access-audit/`, `20-security/` |
| `47-` | `feature-flag-service` | LaunchDarkly / GrowthBook / Unleash self-host or wrapper | `01-flag-model/`, `02-targeting-rules/`, `03-sdk-embeds/`, `04-audit-events/` |
| `48-` | `local-dev-stack` | docker-compose / devcontainer / mise setup | `01-service-topology/`, `02-seed-data/`, `03-hot-reload/`, `04-tooling-versions/` |
| `49-` | `disaster-recovery` | Backup, restore drills, multi-region failover | `01-rto-rpo-targets/`, `02-backup-schedule/`, `03-restore-runbook/`, `04-failover-playbook/` |

### 12.6 Extension / Plugin (`50-`–`59-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `50-` | `dynamic-plugins-host` | Runtime plugin loader (JVM/OSGi/Node/.NET AssemblyLoadContext) | `01-host-contracts/`, `02-lifecycle/`, `03-sandbox-security/`, `04-registry-discovery/` |
| `51-` | `wordpress-plugin` | PHP plugin shipped to the WP directory | `01-hooks-actions/`, `02-shortcodes-blocks/`, `03-i18n-l10n/`, `30-packaging/` |
| `52-` | `slack-bot` | Slack bot / Bolt app | `01-event-subscriptions/`, `02-slash-commands/`, `03-interactive-blocks/`, `20-security/` (signing) |
| `53-` | `discord-bot` | Discord.js bot with slash commands | `01-command-registry/`, `02-intents-scopes/`, `03-voice-integration/` |
| `54-` | `github-app` | GitHub App with webhook + installation model | `01-permission-scopes/`, `02-webhook-events/`, `03-check-runs/`, `20-security/` (JWT) |
| `55-` | `figma-plugin` | Figma REST + plugin API extension | `01-manifest/`, `02-canvas-api/`, `03-ui-panel/` |
| `56-` | `shopify-app` | Shopify embedded app + Admin API | `01-scopes-billing/`, `02-webhook-topics/`, `03-app-bridge/` |
| `57-` | `salesforce-package` | Salesforce managed package | `01-metadata-types/`, `02-apex-triggers/`, `03-lightning-components/` |
| `58-` | `zapier-integration` | Zapier CLI integration | `01-triggers-searches/`, `02-actions/`, `03-auth-scheme/` |
| `59-` | `oauth-app` | Third-party OAuth 2.1 / OIDC client-app registration | `01-scopes-consent/`, `02-token-exchange/`, `03-refresh-strategy/` |

### 12.7 Integration / Adapter (`60-`–`69-`)

Each context here wraps exactly one third-party SDK behind the Adapter pattern (see [ADR 0002](../../assets/design/architecture/01-global-strategy/05-governance/decisions/0002-adapter-pattern-for-payment.md)). Inner concerns are near-identical across the tier: `01-adapters/`, `02-data-mappings/`, `03-resilience/`, `04-webhook-inbox/` when the vendor pushes events back.

| Slot | Slug | Wraps | Notes |
|---|---|---|---|
| `60-` | `payment-gateway-adapter` | Stripe / PayPal / Adyen / Braintree | Signed webhooks, idempotency-key contract |
| `61-` | `email-provider-adapter` | SendGrid / Postmark / Mailgun / SES | Suppression list sync, bounce webhooks |
| `62-` | `sms-provider-adapter` | Twilio / MessageBird / Vonage | Segment count + rate limits |
| `63-` | `push-notification-adapter` | FCM / APNs / Web Push | Token lifecycle + collapse keys |
| `64-` | `identity-provider-adapter` | Auth0 / Okta / Cognito / Google / Apple | SSO/SAML/OIDC federation |
| `65-` | `analytics-adapter` | Segment / Amplitude / Mixpanel / PostHog | Track/identify contract, PII stripping |
| `66-` | `search-provider-adapter` | Algolia / Elastic Cloud / Meilisearch | Index sync + reindex strategy |
| `67-` | `crm-adapter` | Salesforce / HubSpot / Pipedrive | Object sync + rate-limit budget |
| `68-` | `object-storage-adapter` | S3 / GCS / Azure Blob / R2 | Signed URLs + lifecycle policies |
| `69-` | `llm-adapter` | OpenAI / Anthropic / Bedrock / Vertex | Tool-use contract, streaming, cost budget |

### 12.8 Domain / Business Capability (`70-`–`79-`)

Pick from the ones your product actually needs — this tier is the least generic. Every context here is a bounded context in the DDD sense; the internal concern layout follows the same `00-overview/`, `01-configuration/`, `02-core-engine/` (domain services), `03-extension-points/` (SPI for policy overrides), `04-diagrams-specs/`, `05-dependencies/` stack-neutral shape. A stack-specific alias is permitted only when `module_charter.stack` matches it.

| Slot | Slug | Role |
|---|---|---|
| `70-` | `catalog-service` | Product/SKU catalog, pricing, availability |
| `71-` | `cart-checkout-service` | Cart state, coupon engine, checkout orchestration |
| `72-` | `order-management-service` | Order lifecycle, cancellation, returns |
| `73-` | `inventory-service` | Stock levels, reservations, replenishment |
| `74-` | `fulfillment-service` | Warehouse selection, carrier booking, tracking |
| `75-` | `ledger-service` | Double-entry ledger, reconciliation, close-of-period |
| `76-` | `subscription-billing-service` | Plans, trials, dunning, proration |
| `77-` | `fraud-detection-service` | Rules + ML scoring, chargeback workflow |
| `78-` | `kyc-compliance-service` | Identity verification, sanctions screening, audit trail |
| `79-` | `loyalty-rewards-service` | Points ledger, tier engine, reward catalog |

### 12.9 Operations / Observability (`80-`–`89-`)

| Slot | Slug | Role | Inner concerns |
|---|---|---|---|
| `80-` | `log-aggregation` | Loki / ELK / Datadog Logs pipeline | `01-log-schema/`, `02-shipper-config/`, `03-retention-policy/`, `20-security/` (PII scrubbing) |
| `81-` | `metrics-platform` | Prometheus / VictoriaMetrics / Mimir | `01-metric-catalogue/`, `02-recording-rules/`, `03-cardinality-budget/` |
| `82-` | `tracing-platform` | Tempo / Jaeger / Datadog APM | `01-instrumentation-standard/`, `02-sampling-strategy/`, `03-trace-attributes/` |
| `83-` | `alerting-oncall` | PagerDuty / OpsGenie / Grafana OnCall | `01-alert-catalogue/`, `02-routing-policy/`, `03-runbook-links/`, `04-postmortem-template/` |
| `84-` | `slo-error-budgets` | Sloth/OpenSLO SLO definitions | `01-sli-catalogue/`, `02-slo-thresholds/`, `03-burn-rate-alerts/`, `04-error-budget-policy/` |
| `85-` | `synthetic-monitoring` | Playwright/Datadog synthetics | `01-journey-catalogue/`, `02-geo-schedule/`, `03-alert-mapping/` |
| `86-` | `chaos-engineering` | Chaos Mesh / Litmus / Gremlin experiments | `01-hypothesis-catalogue/`, `02-blast-radius/`, `03-abort-conditions/` |
| `87-` | `audit-log-service` | Tamper-evident business-event log | `01-event-schema/`, `02-signing-chain/`, `03-retention-legal-hold/` |
| `88-` | `incident-management` | Post-incident review process + tooling | `01-timeline-template/`, `02-action-item-tracking/`, `03-blameless-review/` |
| `89-` | `cost-observability` | FinOps dashboards, tagging strategy, budget alerts | `01-tag-taxonomy/`, `02-budget-alerts/`, `03-anomaly-detection/` |

### 12.10 Cross-Cutting Appendices (`90-`–`99-`)

| Slot | Slug | Role |
|---|---|---|
| `90-` | `glossary-appendix` | Every acronym, domain term, and non-obvious noun with a definition and an owning context |
| `91-` | `alternatives-considered` | Options-not-chosen archive so future maintainers see the state of the world at decision time |
| `92-` | `deprecation-log` | Every deprecated API surface + its removal date + migration guide link |
| `93-` | `compliance-mapping` | Requirements → controls → evidence mapping (SOC 2, HIPAA, PCI, GDPR) |
| `94-` | `licence-inventory` | Every third-party licence in the classpath with SPDX identifier |
| `95-` | `open-source-releases` | Public-facing packages you publish, their maintainers, and their SLA |
| `96-` | `threat-model` | STRIDE / attack-tree per surface, refreshed per release train |
| `97-` | `capacity-model` | Traffic → resource sizing math, one page per capability |
| `98-` | `benchmarks-baselines` | Performance baselines and their runbooks |
| `99-` | `scratch` | Local-only, gitignored, never shipped |

### 12.11 Selection Heuristic

You almost never generate all 100 contexts. The heuristic is:

1. **Frontend** — one context per distinct user surface (SPA + admin + mobile + extension is four, not one).
2. **Backend** — one context per deployable service; a monolith is *one* context but split by inner concern slots (Section 5).
3. **Framework/library** — one context per publishable artifact (starter, SDK, CLI, design system all separate).
4. **Data** — pipeline + warehouse count separately; ML training and ML inference are different life-cycles.
5. **Integration adapters** — one context per third-party vendor; the tier can grow to 10+ rows without becoming noise.
6. **Domain** — pick from Section 12.8 only what the product asks for; unused slots stay empty.
7. **Ops / observability** — the pillars (log/metric/trace/alert) are almost always warranted; SLO + incident management follow at seed-round-plus scale.
8. **Appendices** — glossary is mandatory; compliance mapping is mandatory whenever the product touches PCI/HIPAA/SOC2; the rest are opt-in.

If your first-cut skeleton has fewer than five contexts and the system is genuinely complex, you have under-decomposed. If it has more than twenty-five contexts and no strong justification, you have over-decomposed — likely by promoting concerns (auth, config) into contexts they don't warrant.

## 13. Catalogue Versioning

Current catalogue version: `2026.07`.

Record this document metadata inside a registered planning artifact, not as extra fields in `sdd-workspace.yml`:

```yaml
planning_metadata:
  catalogue_version: "2026.07"
  layout: "maximal"
  maximal_skeleton_version: "2026.07"
```

Downstream skills preserve the version marker in place. When the catalogue grows (for example a new tier, a moved slug, or an AI runtime split), migration is explicit:

1. Read `registered planning artifact` and compare `planning metadata: catalogue_version` with this document.
2. If the workspace is older, do not renumber existing folders. Add new bounded contexts with unused outer slots and record the migration as an ADR.
3. Add compatibility notes to the affected overview pages, naming the old slug, the new owner, and the cross-contract IDs that connect them.
4. Update `planning metadata: catalogue_version` only after current deterministic and regression checks, independent review and signed human acceptance pass on the migrated tree.

## 14. Growth Ladder and Sub-Module Folderization

The skeleton in Sections 3–5 is the **maximal** rendering. The `minimal` and `standard` profiles (`architect_framework/data/skeleton_profiles.yaml`, ADR-0004) use the same nested layout and the same principles P1–P7 — they scale by selecting fewer contexts and fewer populated slots, never by flattening paths. The flat root layout is migration-only compatibility and is never selected for a new workspace.

### 14.1 The growth ladder — what each level generates

Five levels, not three. The old ladder scaled *breadth* — how many contexts — but a one-service project still paid the full page anatomy, and a workspace past a dozen contexts had a flat sibling list and one index as its only navigation. `seed` and `portfolio` fix the two ends.

Authoritative source: `from_level` on each slot in `architect_framework/data/workspace_skeleton.yaml`. This table is the readable summary.

| Subtree | `seed` | `minimal` | `standard` | `maximal` | `portfolio` |
|---|---|---|---|---|---|
| the nine baseline pages (see SKILL.md) | always | always | always | always | always |
| `01-global-strategy/02-strategy/solution-strategy.md` | always | always | always | always | always |
| `01-global-strategy/architecture.md` + `05-governance/decisions/` | always | always | always | always | always |
| `00-system-views/c1-context.md` | always | always | always | always | always |
| `00-system-views/c2-container.md` + `visual-source-map.md` | — | always | always | always | always |
| `02-domains/00-overview/domains-index.md` | — | always | always | always | always |
| `02-domains/<cluster>/<submodule>/<skill>/` | **none** | exactly one; orchestrator may author it inline | selected contexts; delegate where tier depth warrants it | every context through its tier child skill, one submodule per run | same, plus segment assignment |
| `03-cross-cutting/04-fitness-functions/00-overview.md` | — | when an enforceable rule exists | always | always (V-MAX-5) | always |
| `00-system-views/06-runtime/` (arc42 §6) | — | — | 1–3 scenarios | up to 5 | up to 5 |
| `00-system-views/00-viewpoints/` (ISO 42010) | — | — | always | always | always |
| `01-global-strategy/03-standards/` (TOGAF SIB) | — | — | always | always | always |
| `02-domains/00-overview/context-map.md` (typed edges) | — | — | always | always | always |
| `02-domains/_shared-contracts/` | — | — | catalogs populated per seam evidence | full catalog set | full catalog set |
| `03-cross-cutting/{00-overview.md,01-mechanisms,02-security,03-infrastructure}/` | — | only slots with material content | populated per concern evidence | per tier taxonomy | per tier taxonomy |
| `02-domains/{_shared-kernel,_shared-adapters}/` | — | — | — | per promotion evidence + ADR | same |
| `03-cross-cutting/05-reference-library/` (TOGAF) | — | — | — | when a pattern or model was adopted | same |
| per-module `self-audit.md`, `tests/submodule.feature` | — | — | — | always | always |
| `00-system-views/c0-landscape.md` (C4 landscape) | — | — | — | — | always |
| `02-domains/00-overview/segments.md` (TOGAF segment) | — | — | — | — | always |
| `01-global-strategy/05-governance/compliance-log.md` | — | — | — | — | when an assessment has occurred |
| `04-delivery/` | — | planning shell | planning + quality shells | planning + quality + audit | full delivery tree |

Level upgrades are append-only: a workspace moves `seed → minimal → standard → maximal → portfolio` by adding contexts and slots under the same stable paths — no renumbering, no moved files (P2, P10). Record the upgrade as an ADR and update `planning metadata: selected_profile` with fresh `selection_evidence`.

The `seed` row that matters most is the one that is empty: a seed workspace has **no `02-domains/`**. A single-deployable project does not have bounded contexts to map; giving it a `02-domains/00-web-app/` with six numbered slots produces a tree whose shape claims a decomposition nobody made.

Optional-slot policy (all levels, from `architect_framework/data/skeleton_profiles.yaml`): mandatory slots are populated; conditional slots with evidence are populated and cite the evidence; a required seam without evidence yet receives a blocked README naming the missing input; a non-applicable slot is omitted entirely, with the omission rationale recorded in the context's `00-overview/` page; and a slot that applies but has nothing to say yet is not created at all — that last case is the one that produces empty trees.

### 14.2 Sub-module folderization ladder

Inside any concern slot, depth grows with the topic one rung at a time, and each rung becomes mandatory the moment its trigger appears:

1. **File** — one topic, one `.md`: `02-core-engine/filter-chain.md`.
2. **Namespace folder** — the topic gains a sibling-to-be or a second independently versioned aspect: move it into its own folder per P3, `02-core-engine/filter-chain/{filter-chain.md, ordering-rules.md}`.
3. **Numbered sub-slots** — the folder accumulates five or more files with distinct sub-concerns: introduce two-digit numbered subfolders reusing the Section 2 ranges, `02-core-engine/filter-chain/{00-overview.md, 01-registration/, 02-ordering/, 03-error-dispatch/}`.
4. **Sub-module** — a sub-concern develops its own contracts, lifecycle, or versioning: promote it to a module-in-miniature with a `00-overview/` entry page, its own diagrams under the module's `04-diagrams-specs/` (P7), and stable-ID-linked contracts. When it crosses the Section 12.11 decomposition line (own deployable, own publishable artifact, own vendor), escalate to the orchestrator with a `request-payload` (`kind: taxonomy`). Promotion is a **MOVE**, never a copy: the canonical subtree moves to `modules/<cluster>/<skill>/`; the old nested path may retain only a tombstone README linking to the new stable location. Two live copies are a failed ownership gate.

Concern slot numbers identify semantic responsibilities rather than one technology. For example, slot `05` is `05-dependencies`; a JVM module may present `05-classpath-dependencies`, a Node module `05-node-modules-dependencies`, and a Rust module `05-crate-dependencies`. `module_charter.stack` controls which alias is valid. Stack-specific names such as `msrv` or `classpath` in a mismatched module are validator findings, not harmless labels.

Every rung obeys the same page anatomy (Section 6), splitting thresholds (V-MAX-6: review at 220 lines, hard cap 400), and the orphan-isolation rule — a page whose subject can grow never sits alone between unrelated siblings.


## 15. Core Registry Authority & Frontend Bounded Context Decomposition (2026.10 Alignment)

1. **Single Core Authority (`sdd-workspace.yml`):** In core mode, `sdd-workspace.yml` (with `document_coverage.mode: maximal`) is the sole machine-readable authority for registered artifacts, obligations, and coverage basis digests. This document serves as the canonical catalog of architectural families and concern slots used during applicability evaluation and target-tree derivation (`DT-06`).
2. **Independent Denominator & Depth Priority:** Maximal coverage means accounting for 100% of extracted source items (`covered`, `gap`, `deferred`, `not_applicable`) and designing every applicable mechanism, contract, and state machine to full implementation depth (9 dimensions). KISS is applied strictly within a single page after coverage and depth are preserved.
3. **Frontend Bounded Context Decomposition (`01_frontend_architecture`):** Whenever the source includes frontend applications, UI design specifications, or frontend acceptance evidence (e.g., SPA workspaces, telemetry consoles, route maps, component catalogs, state stores, definition forms, user journeys, and stream/service bindings), each distinct frontend application MUST be modeled as its own bounded context with dedicated concern pages covering:
   - `00-overview/`: application boundary, actors, runtime modes, and module topology;
   - `11-ui-surface/`: route/view map, component catalog, form/action contracts, and end-to-end user journeys;
   - `12-state/`: client state store, persistence, optimistic UI, and CRDT/realtime reconciliation;
   - `13-api-consumption/`: REST/RPC service contracts, realtime stream protocols, error/timeout/unknown outcome handling, and backend dependency seams (`BE-*`);
   - `20-accessibility/`: WCAG compliance, keyboard navigation, focus management, and responsive layout;
   - `21-performance/`: frame/render budgets, bundle splitting, and telemetry boundaries.
