# Architecture document navigation

The current artifact registry in `sdd-workspace.yml` defines paths, kinds, owners, and
coverage basis references. This guide helps readers organize and navigate a maximal or
selective architecture tree. It does not grant write access outside accepted grants.

## Navigation groups

| Group | Question | Ownership basis |
|---|---|---|
| Workspace marker & coverage basis | Which artifacts, obligations, coverage policy, source manifest, concern inventory, and target plan are configured? | `sdd-workspace.yml`; accepted authority controls changes |
| Plan & accounting (`00-plan/`) | Which sources were read, which concerns apply, how is the target tree derived, and what is covered, gap, deferred, or excluded? | Registered planning and inventory artifacts owned by the architect |
| Navigation (`index.md`) | Where are the planned, authored, blocked, and deferred documents? | A registered navigation artifact and its accepted owner |
| System views (`00-system-views/`) | What context, functional use cases, structure, deployment zones, information model, and runtime scenarios explain the system? | Derived artifacts linked to source IDs, viewpoints, and exact revisions |
| Strategy and decisions (`01-global-strategy/`) | What problem, requirements, constraints, principles, standards, risks, and individual ADRs govern the system? | Registered architect and ADR artifacts with source clauses |
| Domains & bounded contexts (`02-domains/`) | What does each backend, AI, security, observability, control-plane, or frontend bounded context own across its concern slots? | The selected skill's accepted artifact grant |
| Shared contracts (`02-domains/_shared-contracts/`) | Which core types, data entities, APIs, realtime messages, external system integrations, and state machines connect contexts? | One registered canonical owner per shared contract |
| Cross-cutting concerns (`03-cross-cutting/`) | Which cross-module mechanisms, security/tenancy models, runtime/infrastructure topologies, fitness functions, and exception catalogs apply? | Registered owner and explicit affected consumers |
| Delivery & verification (`04-delivery/`) | What roadmap, WBS, SaaS readiness, testing strategy, RTM, GAP closure, acceptance findings, and CI/CD runbooks govern delivery? | Registered handoff owner; assumptions, findings, and gaps stay visible |

Use module and concern folders so readers can drill down from system topology to bounded context to specific contract or mechanism without scanning monolithic files.

## Planned vs. authored tree views

Keep four states visible in navigation and planning reports:

- **Planned & covered:** registered, authored, and backed by body witnesses and depth coverage.
- **Planned & gap / blocked:** required by source concern inventory, waiting on evidence, design completion, or write grant.
- **Deferred with authority:** explicitly postponed by an approved decision record with a review trigger.
- **Not applicable:** evaluated against the catalog and excluded with source-grounded rationale.

Do not optimize for a small page count or default to a `seed` profile when the source requires `maximal` coverage. Conversely, do not create empty placeholder files to inflate file counts.

## Read and author

Read and reconcile all sources first, then establish the source manifest, concern inventory, and target document tree plan. Author global strategy and individual ADRs, shared contracts, bounded context concern pages (including frontend and backend modules), cross-cutting mechanisms/exceptions/fitness functions, delivery/acceptance registers, and derived system views. Compile `index.md` after the candidate's page set is known.

A checked candidate still needs independent semantic review and separate signed human acceptance. Observe task state in the core run store. Do not treat a plan, an agent summary, or a task dispatch signature as accepted document content.
