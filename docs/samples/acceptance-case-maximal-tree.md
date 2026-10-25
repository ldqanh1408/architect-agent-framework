# COMPREHENSIVE 100% TARGET DOCUMENT TREE PLAN (ASCII DIAGRAM)
## System: Multi-User Collaborative AI Engineering & Specification Workspace
**Standard:** SDD Agent Framework — Profile: `maximal` (8 Bounded Contexts, 100% Full Coverage Across All 9 Deep-Dive Project Analysis Documents)

> **This is the target document tree AFTER completing [`../GUIDE-SDD-CORE.md`](../GUIDE-SDD-CORE.md).**
> This document is a concrete **acceptance case** for V3 (Maximal Profile), not an end in itself: it demonstrates what an
> 8-context `maximal` system looks like once every V3 architectural decision is applied. Four key shifts distinguish V3 from the legacy ULTIMATE layout, and
> all four are materialized below:
>
> 1. **Grouped by architectural concern, not by diagram notation** (Section 4.1): `00-system-views/` is organized into **six views** (`01-context`,
>    `02-functional`, `03-structure`, `04-deployment`, `05-information`, `06-runtime`) replacing `01-c4-models/` +
>    `02-uml-diagrams/` + `03-frontend-views/`. `05-information/` is the fifth view that the legacy layout lacked.
> 2. **P8 Cardinality / Multiplicity** (Section 19): multi-instance diagrams are no longer collapsed into singletons. The legacy layout had **one** `uml-use-case-matrix.md`, **one**
>    `uml-domain-class-diagram.md`, and **one** `uml-component-overview.md`. This tree has **12 use case pages**, **12 activity
>    diagrams** (`activities/{use-case}/`), **10 sequence diagrams** (`sequences/{scenario}/`), **4 state machine
>    diagrams** (`state-machines/{aggregate}/`), a component diagram **per container**, and a class diagram **per bounded context**.
> 3. **Each subject is a directory, not a single flat page** (Section 4.3): every API, entity, message, and aggregate is an **owned
>    directory**; `02-apis/{api}/` carries an 11-file contract suite replacing a single monolithic `*-service-api.md` file.
> 4. **Every slot declares its page class + provenance** (Section 7, P7): annotated as `[page_class | producer | scope]`, and every
>    file carries `produced_by/run/source_digest` frontmatter.
>
> Concrete cardinality matrix for this system (measured directly from the tree below): **12 use cases · 12 activities · 10 sequences · 4
> state machines · 8 class diagrams · 7 API folders · 5 BPMN processes · 2 deployment environments** — no slot remains a "single file for the whole system" when the actual architecture has multiple instances.

---

## 1. 100% MAPPING MATRIX FROM THE 9 DEEP-DIVE SOURCE DOCUMENTS TO THE SDD DOCUMENT TREE

| # | Source Document in `docs/` | Core Analyzed Content | SDD Document Tree Branch Providing 100% Coverage |
|:---:|---|---|---|
| 1 | `SYSTEM_REQUIREMENTS.md` | Complete SRS v1.1: 16 chapters, M1–M7, NFRs, Scope | Full system backbone: `00-system-views/`, `01-global-strategy/`, `02-domains/` |
| 2 | `Requirements_Gap_Analysis_Report.md` | Master Gap Register: 36 GAPs (GAP-AUTH-01..GAP-OBS-02), E2E Addendum v1.1 | `01-global-strategy/05-governance/gap-register/` + `04-delivery/02-audit/e2e-gap-closure-verification.md` |
| 3 | `RBAC_Permission_Matrix.md` | 4-tier Dynamic RBAC, Master Catalog of 35+ permissions, 6 Default Roles, Custom Roles | `02-domains/03_application_architecture/10-auth-workspace/.../20-security/` + `_shared-contracts/00-core/` |
| 4 | `Business_Rules_Analysis.md` | 4 State Machines, Dynamic Weighted Blast Radius Risk Model (6 axes), 10 validation rules | Contracts: `_shared-contracts/05-state-machines/{aggregate}/` · Diagrams: `00-system-views/06-runtime/state-machines/{aggregate}/` + `07_security_architecture/71-governance-safety/.../15-risk-engine/` |
| 5 | `Data_Integration_Analysis.md` | Detailed entity models M1–M7, External integrations catalog, Real-time sync protocol (WebSocket/Redis) | Subject directories: `_shared-contracts/01-data/{entity}/`, `02-apis/{api}/` (11 files), `03-messages/{message}/`, `04-external/{system}/`; ERD in `00-system-views/05-information/` |
| 6 | `Dynamic_Configuration_And_Docker_Compose_Strategy.md` | 19 dynamic parameters, 4-tier inheritance (System->Org->WS->Proj), Docker Dual-Mode (Test Seed vs Prod) | `03-cross-cutting/01-mechanisms/dynamic-config...` + `03-infrastructure/docker-dual-mode...` |
| 7 | `Alternate_Flows_Analysis.md` | Exception flow analysis across 6 subsystems, Exception code catalog EX-ONB, EX-SPC, EX-AST, EX-AGT, EX-LCK, EX-GOV | `03-cross-cutting/05-exceptions/` (Dedicated specification file per subsystem exception group) |
| 8 | `MVP_Requirements.md` | MVP Scope M1–M6 + M7 Full Collab + Observer, 7 E2E Happy Path User Journeys (Flow 0 through Flow 6) | `01-global-strategy/00-context/goals-non-goals.md` + `00-system-views/02-functional/use-cases/UC-001..012` + `06-runtime/SCN-000..009` |
| 9 | `extracted_text.txt` / Appendix v1.1 | Business context, 13 Core Technical Decisions, Closed-loop Doc-Code Drift mechanism | `01-global-strategy/05-governance/decisions/0001..0013` (13 dedicated ADRs) |

---

## 2. THE COMPLETE TARGET DOCUMENT TREE (100% COMPLETE ASCII DIAGRAM)

```text
documents/
├── sdd-context.yml                                           [orchestrator | Phase state ledger, maximal profile, gates & router verdicts]
├── index.md                                                  [orchestrator | Master Navigation TOC — System-wide architecture navigation]
└── architecture/
    ├── 00-system-views/                                      [arc42 §3 §5 §6 §7 · ISO 42010 | SIX VIEWS grouped by CONCERN, not by diagram notation]
    │   ├── 00-viewpoints/                                    [viewpoint | registry mapping view ↔ concern ↔ notation]
    │   │   ├── viewpoint-catalog.md                          [01-system-architect | Which concern each view serves, notation used, target audience]
    │   │   ├── stakeholder-concern-matrix.md                 [01-system-architect | Tech Lead · Admin · Security Officer · SRE Observer · Developer × concern]
    │   │   └── correspondence-rules.md                       [01-system-architect | Where C4 ↔ UML ↔ Code align: container IDs, module names, event names]
    │   ├── 01-context/                                       [diagram | Who surrounds the system and where the boundary lies — SINGLE, one system context]
    │   │   ├── c4-context-diagram-mermaid-plantuml.md        [context-diagram (07) | C4 L1: Users, GitHub, LLMs, Profiler]
    │   │   ├── system-boundary-specification.md              [context-diagram (07) | What sits inside vs. outside the system boundary]
    │   │   ├── operational-context-profile.md                [context-discovery (01) | Operational environment and external constraints]
    │   │   ├── dependency-map.md                             [dependency-discovery (01) | 6 external dependencies & relationship types]
    │   │   └── 00-index.md [derived]
    │   ├── 02-functional/                                    [use_case · diagram | WHAT USERS CAN DO, and HOW EACH CAPABILITY EXECUTES]
    │   │   ├── use-cases/                                    [use_case · 12 pages | ONE PAGE PER USE CASE (Section 8) — replaces singleton uml-use-case-matrix.md]
    │   │   │   ├── UC-001-invite-member-assign-dynamic-role.md  [requirement-analysis | Admin invites member & assigns 4-tier RBAC ← SCN-000]
    │   │   │   ├── UC-002-define-project-dynamic-workflow.md    [requirement-analysis | Tech Lead creates Workflow / Org Default ← SCN-000]
    │   │   │   ├── UC-003-ingest-spec-from-github-push.md       [requirement-analysis | Webhook push → Spec Ingestion ← SCN-001]
    │   │   │   ├── UC-004-edit-spec-collaboratively-crdt.md     [requirement-analysis | Developer edits Spec via CRDT / Live Cursor ← SCN-002]
    │   │   │   ├── UC-005-resolve-3way-merge-conflict.md        [requirement-analysis | Tech Lead resolves FCFS 3-Way conflict ← SCN-002]
    │   │   │   ├── UC-006-scan-code-build-symbol-graph.md       [requirement-analysis | Scan 100K LOC AST, Symbol Graph ← SCN-003]
    │   │   │   ├── UC-007-lock-spec-prepare-memory.md           [requirement-analysis | Lock Spec → Memory Prep → DAG ← SCN-004]
    │   │   │   ├── UC-008-approve-dag-run-sandbox.md            [requirement-analysis | Approve Plan, Human Gate, gVisor Sandbox ← SCN-005]
    │   │   │   ├── UC-009-evaluate-risk-multisig-sign.md        [requirement-analysis | 6-axis Risk evaluation, Multi-Sig Quorum ← SCN-006]
    │   │   │   ├── UC-010-open-pr-resync-drift.md               [requirement-analysis | PR merged → recalculate Drift → teardown ← SCN-007]
    │   │   │   ├── UC-011-curate-episodic-memory.md             [requirement-analysis | Curate Post-Mortem into Memory Bank ← SCN-008]
    │   │   │   └── UC-012-profile-system-performance.md         [requirement-analysis | SRE Observer Flame Graph, Trace ← SCN-009]
    │   │   ├── use-case-matrix.md                            [derived | 6 roles × 12 UCs × REQ matrix — GENERATED from UC-* frontmatter, never hand-typed]
    │   │   ├── activities/                                   [diagram · per_use_case · 12 diagrams | EACH branching use case gets ONE activity diagram (Section 19.5)]
    │   │   │   ├── UC-005-resolve-3way-merge-conflict/uml-activity-diagram.md  [activity-diagram (07) | FCFS fork/join, version conflict guard]
    │   │   │   ├── UC-008-approve-dag-run-sandbox/uml-activity-diagram.md      [activity-diagram (07) | Human Gate, reject / BLOCKED_BUDGET branch]
    │   │   │   ├── UC-009-evaluate-risk-multisig-sign/uml-activity-diagram.md  [activity-diagram (07) | Hard Veto, missing-role Quorum branch]
    │   │   │   └── {UC-…}/uml-activity-diagram.md            [activity-diagram (07) | ONE folder per UC — NO LONGER a single diagram for the whole system]
    │   │   ├── processes/                                    [diagram · per_process · 5 diagrams | ONE BPMN diagram per business process]
    │   │   │   ├── onboarding/bpmn-2-0-process-diagram.md       [business-process-modeling (02)]
    │   │   │   ├── spec-lifecycle/bpmn-2-0-process-diagram.md   [business-process-modeling (02)]
    │   │   │   ├── agent-execution/bpmn-2-0-process-diagram.md  [business-process-modeling (02)]
    │   │   │   ├── governance-approval/bpmn-2-0-process-diagram.md [business-process-modeling (02)]
    │   │   │   └── post-merge-sync/bpmn-2-0-process-diagram.md  [business-process-modeling (02)]
    │   │   ├── business-capability-map.md                   [capability-mapping (02) | Business capabilities × owning modules]
    │   │   ├── value-stream-specification.md                [value-stream-mapping (02)]
    │   │   └── 00-index.md [derived]
    │   ├── 03-structure/                                     [diagram | Which deployable unit invokes which unit]
    │   │   ├── c4-container-diagram-mermaid-plantuml.md      [container-diagram (07) | C4 L2 — ONE for the whole system: Web, Telemetry, Gateway, DBs, MicroVM]
    │   │   ├── components/                                   [diagram · per_container | C4 L3 — ONE component diagram PER container]
    │   │   │   ├── workspace-web/c4-component-diagram-mermaid-plantuml.md       [component-diagram (07)]
    │   │   │   ├── api-gateway/c4-component-diagram-mermaid-plantuml.md         [component-diagram (07)]
    │   │   │   ├── agent-orchestrator/c4-component-diagram-mermaid-plantuml.md  [component-diagram (07)]
    │   │   │   └── {container}/c4-component-diagram-mermaid-plantuml.md         [component-diagram (07) | one folder per container declared in c4-container]
    │   │   ├── classes/                                      [diagram · per_context · 8 diagrams | UML class diagram PER bounded context — replaces singleton uml-domain-class-diagram.md]
    │   │   │   ├── spec-resolver/uml-class-diagram.md          [class-diagram (07)]
    │   │   │   ├── code-intelligence/uml-class-diagram.md      [class-diagram (07)]
    │   │   │   ├── agent-orchestrator/uml-class-diagram.md     [class-diagram (07)]
    │   │   │   └── {context}/uml-class-diagram.md             [class-diagram (07) | one folder per bounded context]
    │   │   ├── service-boundary-map.md                      [microservice-style (04)]
    │   │   ├── logical-l2-submodules.md                     [derived]
    │   │   ├── container-module-mapping.md                  [derived | Container ↔ 8 bounded contexts mapping]
    │   │   └── 00-index.md [derived]
    │   ├── 04-deployment/                                    [diagram · per_environment | Target infrastructure — Docker Dual-Mode = 2 environments]
    │   │   ├── environments/
    │   │   │   ├── test-seed/uml-deployment-diagram.md         [deployment-diagram (07) | Test Seed Mode, single-host]
    │   │   │   ├── test-seed/network-architecture-diagram.md   [network-diagram (07)]
    │   │   │   ├── prod-zero-trust/uml-deployment-diagram.md   [deployment-diagram (07) | Prod Mode K8s + Firecracker gVisor]
    │   │   │   └── prod-zero-trust/network-architecture-diagram.md [network-diagram (07) | mTLS, isolated dual Frontend domains]
    │   │   └── 00-index.md [derived]
    │   ├── 05-information/                                   [data_entity · diagram | FIFTH VIEW — missing from legacy ULTIMATE tree]
    │   │   ├── erd-diagram-mermaid-plantuml.md              [erd-diagram (07) | System-wide ERD across 7 table groups M1–M7]
    │   │   ├── entity-attribute-spec.md                     [erd-diagram (07) | Keys, types, and constraints per entity]
    │   │   ├── index-candidate-list.md                      [erd-diagram (07) | Candidate database indexes & rationale]
    │   │   └── 00-index.md [derived]
    │   ├── 06-runtime/                                       [runtime_scenario · diagram | Execution order across components and failure branches]
    │   │   ├── 00-scenario-index.md [derived]
    │   │   ├── SCN-000-onboarding-and-workflow-definition.md   [01-system-architect | Flow 0: Member invitation, RBAC & Workflow setup]
    │   │   ├── SCN-001-spec-change-github-webhook-push.md      [01-system-architect | Flow 1: GitHub push → Spec Ingestion]
    │   │   ├── SCN-002-spec-change-web-ui-crdt-and-merge.md    [01-system-architect | Flow 2: Web UI CRDT → Branch → 3-Way Merge]
    │   │   ├── SCN-003-ast-scan-symbol-graph-and-evidence.md   [01-system-architect | Flow 3: AST Scan, Symbol Graph & Evidence]
    │   │   ├── SCN-004-memory-preparation-and-dag-plan.md      [01-system-architect | Flow 4A: LOCKED Spec → Memory Prep → DAG]
    │   │   ├── SCN-005-human-gated-execution-and-sandbox.md    [01-system-architect | Flow 4B: Plan Approval → Human Gate → Sandbox]
    │   │   ├── SCN-006-governance-six-axis-risk-multisig.md    [01-system-architect | Flow 5: 6-axis Risk, Multi-Sig, PR]
    │   │   ├── SCN-007-post-merge-sync-drift-and-teardown.md   [01-system-architect | Flow 6: PR merged → Drift → teardown]
    │   │   ├── SCN-008-episodic-memory-auto-curation.md        [01-system-architect | Flow 7: Post-Mortem → Memory Bank]
    │   │   ├── SCN-009-system-observer-deep-profiling.md       [01-system-architect | SRE Flow: Flame Graph & Trace Export]
    │   │   ├── sequences/                                    [diagram · per_scenario · 10 diagrams | ONE sequence diagram PER SCN]
    │   │   │   ├── SCN-002/uml-sequence-diagram.md            [sequence-diagram (07) | CRDT → Branch → 3-Way Merge]
    │   │   │   ├── SCN-005/uml-sequence-diagram.md            [sequence-diagram (07) | Human Gate → gVisor Sandbox]
    │   │   │   ├── SCN-006/saga-step-sequence-diagram.md      [saga-design (03) | Multi-Sig → PR creation & compensating saga]
    │   │   │   └── SCN-{NNN}/uml-sequence-diagram.md          [sequence-diagram (07) | one folder per SCN]
    │   │   ├── state-machines/                               [diagram · per_aggregate · 4 diagrams | ONE state machine PER aggregate]
    │   │   │   ├── spec-document/uml-state-diagram.md         [state-diagram (07) | DRAFT→IN_REVIEW→CONFLICT→LOCKED→SUBMITTED→UNLOCKED/IMPLEMENTED]
    │   │   │   ├── task-dag/uml-state-diagram.md              [state-diagram (07) | PROPOSED→APPROVED→RUNNING→AWAITING_HUMAN_GATE→CHECKPOINT→BLOCKED_BUDGET]
    │   │   │   ├── concurrency-lock/uml-state-diagram.md      [state-diagram (07) | FREE→ACQUIRED→EXTENDED→EXPIRED→FORCE_RELEASED]
    │   │   │   └── approval-gate/uml-state-diagram.md         [state-diagram (07) | PENDING→PARTIALLY_SIGNED→APPROVED(Quorum≥2)→REJECTED→VETOED]
    │   │   └── 00-index.md [derived]
    │   ├── visual-source-map.md                             [01-system-architect | Visual Source Map feeding system modelers]
    │   └── generated/                                        [rendered images — disposable and regenerable]
    │
    ├── 01-global-strategy/                                   [arc42 §1 §2 §4 §9 §10 §11 §12 | Global Strategy, 13 Core Technical Decisions & Master Gaps]
    │   ├── 00-context/
    │   │   ├── assumptions.md                                [01-system-architect | Architectural assumptions A1–A14 (GitHub OAuth, Quorum, Lock TTL...)]
    │   │   ├── glossary.md                                   [01-system-architect | Ubiquitous Language glossary (CRDT, AST, Drift, WORM, HITL)]
    │   │   ├── goals-non-goals.md                            [01-system-architect | Goals manifesto & MVP In-Scope vs Out-of-Scope boundaries]
    │   │   └── problem-brief.md                              [01-system-architect | Core problem statement: Doc-Code Drift, Collab Conflict, Uncontrolled Code]
    │   ├── 01-requirements/
    │   │   ├── atomic-requirements-register.md               [01-system-architect | Atomic requirements ledger extracted from CLR-001..035]
    │   │   ├── constraints.md                                [01-system-architect | Technical, legal & Zero-Trust constraints]
    │   │   ├── quality-attributes.md                         [01-system-architect | Non-functional quality metrics NFR-001..030]
    │   │   ├── requirements.md                               [01-system-architect | System functional requirements specification REQ-001..050]
    │   │   ├── urd-coverage-ledger.md                        [01-system-architect | User requirement coverage verification ledger]
    │   │   └── requirements-traceability-matrix.md           [01-system-architect | End-to-end Requirements Traceability Matrix RTM (SRS Chapter 14)]
    │   ├── 02-strategy/
    │   │   ├── architecture-principles.md                    [01-system-architect | 13 system-wide architecture design principles]
    │   │   ├── solution-strategy.md                          [01-system-architect | 4-Tier Clean Architecture Modular Monolith strategy]
    │   │   ├── technology-selection.md                       [01-system-architect | Technology stack: Postgres, Redis, Qdrant, Tree-sitter, gVisor]
    │   │   └── clean-architecture-guidelines.md              [01-system-architect | 3 layering rules & inter-module boundary guidelines]
    │   ├── 03-standards/
    │   │   ├── standards-register.md                         [01-system-architect | Technical standards registry STD-001..020]
    │   │   ├── api-standards.md                              [01-system-architect | RESTful API, WebSocket JSON-RPC & gRPC-Ready standards]
    │   │   ├── security-standards.md                         [01-system-architect | Zero-Trust, Secret Scanning, KMS & Hash-chain WORM standards]
    │   │   ├── data-standards.md                             [01-system-architect | Schema Migration, RLS Isolation & Multi-Tenancy standards]
    │   │   └── coding-and-linting-standards.md               [01-system-architect | Code style, linters (ESLint, Ruff) & boundary linter standards]
    │   ├── 04-risks/
    │   │   ├── risk-register.md                              [01-system-architect | Risk register ledger RSK-001..015]
    │   │   ├── technical-debt.md                             [01-system-architect | Technical debt tracking: In-App limits & local MicroVM constraints]
    │   │   └── blast-radius-containment-policy.md            [01-system-architect | AI code execution blast-radius containment policy]
    │   ├── 05-governance/
    │   │   ├── gap-register/                                 [36 Gaps extracted from Requirements_Gap_Analysis_Report.md]
    │   │   │   ├── 00-master-gap-register.md                 [01-system-architect | Master register of all 36 GAPs & closure status]
    │   │   │   ├── GAP-AUTH-01-to-03-identity-gaps.md        [01-system-architect | Resolution for Auth, System Actor & Role Assignment Scope GAPs]
    │   │   │   ├── GAP-BUDGET-01-to-02-token-budget-gaps.md  [01-system-architect | Resolution for Token Budget Exhaustion & Safe Checkpoint GAPs]
    │   │   │   ├── GAP-SPEC-01-to-04-spec-lifecycle-gaps.md  [01-system-architect | Resolution for Spec Unlock, FCFS Concurrency & Clean Archive GAPs]
    │   │   │   ├── GAP-AST-01-to-04-code-intelligence-gaps.md[01-system-architect | Resolution for Tree-sitter Syntax Error & Qdrant Fallback GAPs]
    │   │   │   ├── GAP-DAG-01-to-04-agent-orchestrator-gaps.md[01-system-architect| Resolution for Org Default Agent Fallback & Memory Context GAPs]
    │   │   │   ├── GAP-LCK-01-to-03-concurrency-lock-gaps.md [01-system-architect | Resolution for Zombie Lock, Heartbeat & Wait Queue GAPs]
    │   │   │   ├── GAP-GOV-01-to-04-governance-risk-gaps.md  [01-system-architect | Resolution for Hard Veto Formula, Missing-Role Quorum & CI GAPs]
    │   │   │   └── GAP-OBS-01-to-02-observability-gaps.md    [01-system-architect | Resolution for Frontend Domain Isolation & Profiler Dumps GAPs]
    │   │   ├── decisions/                                    [13 Dedicated ADRs for the 13 Core Technical Decisions in SRS §1.3 & extracted_text.txt]
    │   │   │   ├── 0000-deferred-register.md                 [01-system-architect | Decisions deferred to v2 (Multi-Channel Notifications)]
    │   │   │   ├── 0001-dynamic-hierarchical-rbac.md         [01-system-architect | ADR-1: 4-tier Dynamic RBAC, Master Catalog & Custom Roles]
    │   │   │   ├── 0002-system-observer-frontend-isolation.md[01-system-architect | ADR-2: System Observer Role & Frontend Domain Isolation]
    │   │   │   ├── 0003-mvp-scope-m1-m7-full-collaboration.md[01-system-architect | ADR-3: MVP Scope M1-M6 + M7 Realtime & Profiler]
    │   │   │   ├── 0004-org-byok-multi-key-budget-gateway.md [01-system-architect | ADR-4: Org BYOK Multi-Key Pool & 3-Tier Budget Gateway]
    │   │   │   ├── 0005-workspace-customization-hub.md       [01-system-architect | ADR-5: Centralized Workspace Hub: MCP, Skills, Rules, Sidecars]
    │   │   │   ├── 0006-workspace-agent-memory-hub.md        [01-system-architect | ADR-6: 4-Tier Memory Hub, 3 Engines & Pre-seeding Curation]
    │   │   │   ├── 0007-dynamic-workflow-org-default-agent.md[01-system-architect | ADR-7: Dynamic Workflow & JIT Org Default Agent Fallback]
    │   │   │   ├── 0008-plan-first-locked-spec-memory-prep.md[01-system-architect | ADR-8: Plan-First Architecture, Locked Spec, Memory Prep Phase]
    │   │   │   ├── 0009-six-axis-composite-risk-hard-veto.md [01-system-architect | ADR-9: 6-Axis Multi-Dimensional Risk Engine & Hard Veto]
    │   │   │   ├── 0010-zero-loss-state-artifact-snapshot.md [01-system-architect | ADR-10: Snapshot Diff, Logs, ThoughtState for Retry/Resume]
    │   │   │   ├── 0011-fcfs-visual-3way-spec-merge.md       [01-system-architect | ADR-11: First-Come-First-Served Visual 3-Way Spec Merge]
    │   │   │   ├── 0012-four-tier-cascading-dynamic-config.md[01-system-architect | ADR-12: Eliminate Hardcoding, 4-Tier Cascading Dynamic Config]
    │   │   │   └── 0013-docker-compose-dual-mode-strategy.md [01-system-architect | ADR-13: Dual-Mode Docker Compose: Test Seed vs Prod Zero-Trust]
    │   │   ├── routing/                                      [Router D-1 Dispatch Basis for the 8 Modules]
    │   │   │   ├── 10-auth-workspace.md                      [01-system-architect | Routing Basis for Module M1]
    │   │   │   ├── 11-collaborative-gateway.md               [01-system-architect | Routing Basis for Module M7 Core]
    │   │   │   ├── 60-spec-resolver.md                       [01-system-architect | Routing Basis for Module M2]
    │   │   │   ├── 61-code-intelligence.md                   [01-system-architect | Routing Basis for Module M3]
    │   │   │   ├── 62-agent-orchestrator.md                  [01-system-architect | Routing Basis for Module M4]
    │   │   │   ├── 70-sandbox-lock.md                        [01-system-architect | Routing Basis for Module M5]
    │   │   │   ├── 71-governance-safety.md                   [01-system-architect | Routing Basis for Module M6]
    │   │   │   └── 80-observability-profiler.md              [01-system-architect | Routing Basis for Module M7-OBS]
    │   │   └── compliance-log.md                             [01-system-architect | Architecture standards compliance verification report]
    │   ├── architecture.md                                   [01-system-architect | System-wide topology blueprint & network zone boundaries]
    │   └── composition-root.md                               [01-system-architect | DI Container wiring, factories & service bootstrapping]
    │
    ├── 02-domains/                                           [arc42 §5 | DDD Bounded Contexts, 4 State Machines, Data & Integration]
    │   ├── 00-overview/
    │   │   ├── context-map.md                                [01-system-architect | Context Map relationships across all 8 Bounded Contexts]
    │   │   ├── domains-index.md                              [01-system-architect | Bounded Contexts catalog & responsibility decomposition]
    │   │   └── segments.md                                   [01-system-architect | TOGAF domain segment partitioning table]
    │   │
    │   ├── _shared-contracts/                                [Shared contracts — EACH API/entity/message/aggregate is an OWNED DIRECTORY (Section 4.3)]
    │   │   ├── 00-core/                                      [data_entity | shared primitives: identifiers, invariants, mutation authority]
    │   │   │   ├── tenant-context.md                         [01-system-architect | OrgId, WorkspaceId, ProjectId Context & RLS Token]
    │   │   │   ├── principal-identity.md                     [01-system-architect | UserId, Master Permission Catalog, RoleAssignment]
    │   │   │   ├── shared-enums.md                           [01-system-architect | Spec, Task, RiskTier, Lock, and Budget Enums]
    │   │   │   └── base-audit-types.md                       [01-system-architect | Timestamp, VersionId, SHA-256 Hash, SignatureBlock]
    │   │   ├── 01-data/                                      [data_entity · per_entity · 11 folders | entities read/written across multiple contexts]
    │   │   │   ├── spec-document/                            [Entity: spec_documents, branches, versions, conflict_sessions]
    │   │   │   │   ├── spec-document-entity.md               [data-modeling (09) | identity, grain, invariants, write owner]
    │   │   │   │   └── 00-index.md [derived]
    │   │   │   ├── code-symbol-and-evidence/                 [Entity: ast_symbols, call_graph_edges, code_evidences]
    │   │   │   │   ├── code-symbol-and-evidence-entity.md    [data-modeling (09)]
    │   │   │   │   └── 00-index.md [derived]
    │   │   │   └── {entity}/                                 [9 additional entity folders with identical shape: task-dag, agent-snapshot, task-memory-package,
    │   │   │                                                  concurrency-lock, risk-assessment-and-gate, audit-ledger-record,
    │   │   │                                                  agent-customization-hub, memory-bank-item, dynamic-configuration-parameter]
    │   │   ├── 02-apis/                                      [api_contract · per_api · 7 folders | EACH API has 11 contract files, replacing single *-service-api.md]
    │   │   │   ├── auth-workspace-service/                   [M1 API — FULL 11-file exemplar (Section 4.3)]
    │   │   │   │   ├── 00-index.md [derived]                 [renderer | contents, write owner, and completeness status]
    │   │   │   │   ├── openapi-3-1-specification.md          [rest-api-design (08) | ValidateUser, CheckPermission, AllocateBudget]
    │   │   │   │   ├── api-endpoint-catalog.md               [rest-api-design (08) | Org, Workspace, Project, User, Role, Key, Hub]
    │   │   │   │   ├── error-code-registry.md                [rest-api-design (08) | ERR-xxx & HTTP/WS status codes]
    │   │   │   │   ├── rfc-7807-error-spec.md                [error-handling-design (08)]
    │   │   │   │   ├── api-versioning-policy.md              [api-versioning-design (08)]
    │   │   │   │   ├── api-security-middleware-spec.md       [api-auth-design (08) | Dynamic RBAC enforcement]
    │   │   │   │   ├── idempotency-spec.md                   [idempotency-design (08)]
    │   │   │   │   ├── pagination-standard-spec.md           [pagination-design (08)]
    │   │   │   │   ├── api-filtering-spec.md                 [api-filtering-design (08)]
    │   │   │   │   └── webhook-architecture-spec.md          [webhook-design (08) | GitHub Webhook HMAC-SHA256]
    │   │   │   ├── spec-resolver-service/                    [M2 API — identical 11-file shape | GetLockedSpec, DetectConflict, SubmitToAI]
    │   │   │   ├── code-intelligence-service/                [M3 API | QueryAST, GetCallGraph, CalculateDriftScore]
    │   │   │   ├── agent-orchestrator-service/               [M4 API | ProposePlan, ApproveCheckpoint, ResumeTask]
    │   │   │   ├── sandbox-lock-service/                     [M5 API | AcquireFileLock, ReleaseLock, SpawnWorktree]
    │   │   │   ├── governance-safety-service/                [M6 API | EvaluateRisk, SubmitSignature, AppendAudit]
    │   │   │   └── collaborative-gateway-service/            [M7 API | BroadcastEvent, PushNotification, SyncPresence]
    │   │   ├── 03-messages/                                  [event_message · per_message · 7 folders | ONE folder per event stream family]
    │   │   │   ├── spec-lifecycle/                           [Events: SpecCreated, SpecLocked, SpecUnlocked, SpecMerged]
    │   │   │   │   ├── spec-lifecycle-events.md              [domain-event-design (03) | producer, consumer, schema, ordering, deduplication]
    │   │   │   │   └── 00-index.md [derived]
    │   │   │   └── {message}/                                [6 additional folders: ast-and-drift, agent-execution, sandbox-and-lock,
    │   │   │                                                  governance-risk, collaborative-stream, llm-gateway-budget]
    │   │   ├── 04-external/                                  [api_contract · per_system · 6 folders | conformist vs. ACL boundary & failure handling]
    │   │   │   ├── github-app/github-app-webhook-integration.md      [01-system-architect | Installation, Webhook HMAC, PR API]
    │   │   │   ├── multi-provider-llm/multi-provider-llm-gateways.md [01-system-architect | OpenAI, Anthropic, DeepSeek, Gemini, vLLM]
    │   │   │   ├── qdrant/qdrant-vector-database-client.md          [01-system-architect | Vector Search & fallback text query]
    │   │   │   ├── redis/redis-pubsub-and-cache-cluster.md         [01-system-architect | Lock Engine, Presence, Event Pub/Sub]
    │   │   │   ├── postgresql/postgresql-rls-database-cluster.md    [01-system-architect | PG16, per-Org Row-Level Security]
    │   │   │   └── opentelemetry/opentelemetry-and-pyroscope-daemons.md [01-system-architect | OTel, Prometheus, Pyroscope eBPF]
    │   │   └── 05-state-machines/                            [mechanism · per_aggregate · 4 folders | CONTRACT of valid transitions; diagrams live in 06-runtime]
    │   │       ├── spec-document/state-machine-contract.md      [01-system-architect | Section 1.1 valid state transitions & guards]
    │   │       ├── task-dag/state-machine-contract.md          [01-system-architect | Section 1.2 PROPOSED..BLOCKED_BUDGET]
    │   │       ├── concurrency-lock/state-machine-contract.md   [01-system-architect | Section 1.3 Heartbeat 30s, TTL 1800s]
    │   │       └── approval-gate/state-machine-contract.md      [01-system-architect | Section 1.4 Quorum ≥2, Hard Veto]
    │   │
    │   ├── 03_application_architecture/                      [Business Application Architecture Cluster]
    │   │   ├── 10-auth-workspace/                            [Module M1: Auth, Multi-Tenancy, Hub & LLM Gateway]
    │   │   │   └── workflow-orchestration-architect/
    │   │   │       ├── 00-overview/
    │   │   │       │   └── workflow-orchestration-architect-overview.md
    │   │   │       ├── 01-M1/
    │   │   │       │   ├── 11-api/
    │   │   │       │   │   └── M1-api.md                 [REST Endpoints: Org, Workspace, Project, User, Role, Key, Hub API]
    │   │   │       │   ├── 12-events/
    │   │   │       │   │   └── M1-events.md              [Event Handling: OrgCreated, KeyFailover, BudgetAlarm]
    │   │   │       │   ├── 13-clients/
    │   │   │       │   │   └── M1-clients.md             [Clients: GitHub OAuth App, OpenAI, Anthropic, DeepSeek, vLLM]
    │   │   │       │   ├── 14-data/
    │   │   │       │   │   └── M1-data.md                [Data Schema Section 8.1: orgs, users, roles, permissions, key_pools, budgets]
    │   │   │       │   ├── 15-customization-hub/
    │   │   │       │   │   └── M1-customization-hub.md   [Design Section 5.1.4: 6 Hub Pillars (MCP, Skills, Rules, Plugins, Hooks, Sidecars)]
    │   │   │       │   ├── 16-memory-hub/
    │   │   │       │   │   └── M1-memory-hub.md          [Design Section 5.1.5: 4 Memory Tiers, 3 Engines & Pre-seeding/Curation]
    │   │   │       │   ├── 20-security/
    │   │   │       │   │   └── M1-security.md            [Dynamic RBAC Enforcement, Master Permission Catalog 35+ permissions]
    │   │   │       │   ├── 21-observability/
    │   │   │       │   │   └── M1-observability.md       [Metrics: Token Consumption, Key Failure Rate, Budget Saturation]
    │   │   │       │   ├── 22-resilience/
    │   │   │       │   │   └── M1-resilience.md          [Multi-Key Priority/Weight Failover, Safe Checkpoint at 100% Budget]
    │   │   │       │   └── M1-design.md                  [Module 1 Overall 4-Tier Clean Architecture Design]
    │   │   │       ├── tests/
    │   │   │       │   └── submodule.feature             [BDD Tests: RLS Isolation, Multi-Key Failover & Pre-seeding Memory]
    │   │   │       ├── verification/
    │   │   │       │   └── fitness-self-check.md         [Module M1 Fitness Self-Check]
    │   │   │       ├── README.md
    │   │   │       ├── self-audit.md
    │   │   │       └── source-map.yml
    │   │   │
    │   │   └── 11-collaborative-gateway/                     [Module M7: Realtime Collaborative Gateway Core]
    │   │       └── event-driven-architect/
    │   │           ├── 00-overview/
    │   │           │   └── event-driven-architect-overview.md
    │   │           ├── 01-M7/
    │   │           │   ├── 11-api/
    │   │           │   │   └── M7-api.md                 [WS Handshake /ws/collab, Ticket Auth, Room Endpoints]
    │   │           │   ├── 12-events/
    │   │           │   │   └── M7-events.md              [WS Streams: CursorMoved, KeystrokeCRDT, ThoughtTreeStep]
    │   │           │   ├── 13-clients/
    │   │           │   │   └── M7-clients.md             [Clients: Redis Pub/Sub Cluster, Browser WebSocket Channel]
    │   │           │   ├── 14-data/
    │   │           │   │   └── M7-data.md                [Data Schema Section 8.7: collab_sessions, live_presences, notifications]
    │   │           │   ├── 15-crdt-sync/
    │   │           │   │   └── M7-crdt-sync.md           [Design Section 5.7.4: Monaco Editor + Yjs CRDT real-time sync <200ms]
    │   │           │   ├── 16-presence-engine/
    │   │           │   │   └── M7-presence-engine.md     [Design Section 5.7.2: Live Presence, User Cursors, Heartbeat & 60s Timeout]
    │   │           │   ├── 17-thought-visualizer/
    │   │           │   │   └── M7-thought-visualizer.md  [Design Section 5.7.3: Agent Thought-Tree Stream, ThoughtNode rendering <200ms]
    │   │           │   ├── 18-notifications/
    │   │           │   │   └── M7-notifications.md       [Design Section 5.7.5: In-App Notification Center, Unread Badges & Triggers]
    │   │           │   ├── 20-security/
    │   │           │   │   └── M7-security.md            [WebSocket Auth Tokens, Cross-Site WebSocket Hijacking Protection]
    │   │           │   ├── 21-observability/
    │   │           │   │   └── M7-observability.md       [Metrics: Active WS Connections, Event Fan-out Latency <200ms]
    │   │           │   ├── 22-resilience/
    │   │           │   │   └── M7-resilience.md          [Auto-reconnect with Exponential Backoff, Message Deduplication]
    │   │           │   └── M7-design.md                  [Module 7 Core Overall 4-Tier Clean Architecture Design]
    │   │           ├── tests/
    │   │           │   └── submodule.feature             [BDD Tests: Yjs CRDT Conflict-free Editing & Presence Heartbeat]
    │   │           ├── verification/
    │   │           │   └── fitness-self-check.md         [Module M7 Fitness Self-Check]
    │   │           ├── README.md
    │   │           ├── self-audit.md
    │   │           └── source-map.yml
    │   │
    │   ├── _frontend-apps/                                  [archetype `frontend` (Section 5) | 2 frontend modules — rehomes legacy 03-frontend-views to proper owners]
    │   │   ├── workspace-web/
    │   │   │   └── frontend-architect/
    │   │   │       ├── 00-overview/
    │   │   │       │   └── frontend-architect-overview.md    [frontend | apps/workspace-web: boundaries and non-goals]
    │   │   │       ├── 01-workspace-web/
    │   │   │       │   ├── 11-ui-surface/
    │   │   │       │   │   ├── monaco-crdt-collaborative-editor-ui.md    [frontend | Spec editor, Yjs CRDT, Live Cursors]
    │   │   │       │   │   ├── visual-3way-merge-conflict-resolver-ui.md [frontend | Visual 3-Way Merge & Human Choice Modal]
    │   │   │       │   │   ├── agent-thought-tree-and-dag-canvas-ui.md   [frontend | Task DAG Canvas, ThoughtNode streaming, Human Gates]
    │   │   │       │   │   └── workspace-customization-hub-ui.md         [frontend | Hub: MCP, Skills, Rules, Plugins, Sidecars]
    │   │   │       │   ├── 12-state/
    │   │   │       │   │   └── workspace-web-state.md        [frontend | Client state, optimistic UI, reconnect backoff]
    │   │   │       │   ├── 13-api-consumption/
    │   │   │       │   │   └── workspace-web-api-consumption.md [frontend | Consumes M1–M7 APIs & WS /ws/collab]
    │   │   │       │   ├── 20-accessibility/
    │   │   │       │   │   └── workspace-web-accessibility.md
    │   │   │       │   └── 21-performance/
    │   │   │       │       └── workspace-web-performance.md  [frontend | Keystroke → render < 200ms]
    │   │   │       ├── tests/
    │   │   │       │   └── submodule.feature
    │   │   │       ├── verification/
    │   │   │       │   └── fitness-self-check.md
    │   │   │       ├── README.md
    │   │   │       ├── self-audit.md
    │   │   │       └── source-map.yml
    │   │   └── telemetry-console/
    │   │       └── frontend-architect/
    │   │           ├── 00-overview/
    │   │           │   └── frontend-architect-overview.md    [frontend | apps/telemetry-console: isolated domain, independent auth]
    │   │           ├── 01-telemetry-console/
    │   │           │   ├── 11-ui-surface/
    │   │           │   │   └── system-observer-telemetry-console-ui.md  [frontend | Flame Graphs, APM, SRE Golden Signals]
    │   │           │   ├── 13-api-consumption/
    │   │           │   │   └── telemetry-console-api-consumption.md     [frontend | ONLY calls Profiler/OTel export, forbidden from calling business APIs]
    │   │           │   ├── 20-accessibility/
    │   │           │   │   └── telemetry-console-accessibility.md
    │   │           │   └── 21-performance/
    │   │           │       └── telemetry-console-performance.md
    │   │           ├── tests/
    │   │           │   └── submodule.feature
    │   │           ├── verification/
    │   │           │   └── fitness-self-check.md
    │   │           ├── README.md
    │   │           ├── self-audit.md
    │   │           └── source-map.yml
    │   │
    │   ├── 04_ai_architecture/                               [AI Cluster — archetype `ai-system` (Section 5) replacing `backend-service`; M4 demonstrates 7 AI slots, M3 retains `data-platform` (vector)]
    │   │   ├── 60-spec-resolver/                             [Module M2: Doc & Spec Conflict Resolver]
    │   │   │   └── ai-system-architect/
    │   │   │       ├── 00-overview/
    │   │   │       │   └── ai-system-architect-overview.md
    │   │   │       ├── 01-M2/
    │   │   │       │   ├── 11-api/
    │   │   │       │   │   └── M2-api.md                 [REST API: Spec Branch, Lock, Unlock, 3-Way Merge, Ingestion API]
    │   │   │       │   ├── 12-events/
    │   │   │       │   │   └── M2-events.md              [Events: SpecConflictDetected, SpecLocked, MergeApproved, SpecUnlocked]
    │   │   │       │   ├── 13-clients/
    │   │   │       │   │   └── M2-clients.md             [Clients: GitHub App Installation Client, Webhook Receiver]
    │   │   │       │   ├── 14-data/
    │   │   │       │   │   └── M2-data.md                [Data Schema Section 8.2: spec_documents, branches, versions, conflicts]
    │   │   │       │   ├── 15-3way-merge-engine/
    │   │   │       │   │   └── M2-3way-merge-engine.md   [Design Section 5.2.4: Visual 3-Way Merge, Conflict Detection <=3s, FCFS]
    │   │   │       │   ├── 16-lock-freeze-lifecycle/
    │   │   │       │   │   └── M2-lock-lifecycle.md      [Design Section 5.2.5-5.2.6: Branch Spec Lock, Submit to AI, Unlock DAG Freeze]
    │   │   │       │   ├── 20-security/
    │   │   │       │   │   └── M2-security.md            [Authorization: Only Tech Lead/Admin permitted for spec:lock, spec:unlock]
    │   │   │       │   ├── 21-observability/
    │   │   │       │   │   └── M2-observability.md       [Metrics: Conflict detection latency <=3s, Merge success rate]
    │   │   │       │   ├── 22-resilience/
    │   │   │       │   │   └── M2-resilience.md          [FCFS Version Id Check: Automatic alert & reload on stale submission]
    │   │   │       │   └── M2-design.md                  [Module 2 Overall 4-Tier Clean Architecture Design]
    │   │   │       ├── tests/
    │   │   │       │   └── submodule.feature             [BDD Tests: Visual 3-Way Merge FCFS, Spec Lock & Unlock DAG Freeze]
    │   │   │       ├── verification/
    │   │   │       │   └── fitness-self-check.md         [Module M2 Fitness Self-Check]
    │   │   │       ├── README.md
    │   │   │       ├── self-audit.md
    │   │   │       └── source-map.yml
    │   │   │
    │   │   ├── 61-code-intelligence/                         [Module M3: AST Parsing & Code Intelligence]
    │   │   │   └── vector-search-architect/
    │   │   │       ├── 00-overview/
    │   │   │       │   └── vector-search-architect-overview.md
    │   │   │       ├── 01-M3/
    │   │   │       │   ├── 11-ingest/
    │   │   │       │   │   └── M3-ingest.md              [Design Section 5.3.1: Tree-sitter AST Engine across 7 languages <=15s/100K LOC]
    │   │   │       │   ├── 12-storage/
    │   │   │       │   │   └── M3-storage.md             [Data Schema Section 8.3: ast_symbols, call_graph_edges, Qdrant vectors]
    │   │   │       │   ├── 13-serving/
    │   │   │       │   │   └── M3-serving.md             [Design Section 5.3.3-5.3.4: Semantic Vector Search, Code Evidence Extraction]
    │   │   │       │   ├── 14-lineage/
    │   │   │       │   │   └── M3-lineage.md             [Design Section 5.3.2: Symbol Graph & Cross-module Caller-Callee Call Graph]
    │   │   │       │   ├── 15-drift-engine/
    │   │   │       │   │   └── M3-drift-engine.md        [Design Section 5.3.5: Doc-Code Drift Metric D, Cosine + Coverage, Dual Gates]
    │   │   │       │   ├── 20-retention/
    │   │   │       │   │   └── M3-retention.md           [Vector Index Lifecycle Management, Incremental Re-scan after PR Merge]
    │   │   │       │   ├── 21-quality/
    │   │   │       │   │   └── M3-quality.md             [AST parsing quality control, fault-tolerant syntax error skipping]
    │   │   │       │   └── M3-design.md                  [Module 3 Overall 4-Tier Clean Architecture Design]
    │   │   │       ├── tests/
    │   │   │       │   └── submodule.feature             [BDD Tests: AST Scan Latency, Semantic Search & Drift Score Gates]
    │   │   │       ├── verification/
    │   │   │       │   └── fitness-self-check.md         [Module M3 Fitness Self-Check]
    │   │   │       ├── README.md
    │   │   │       ├── self-audit.md
    │   │   │       └── source-map.yml
    │   │   │
    │   │   └── 62-agent-orchestrator/                        [Module M4: Dynamic Agent DAG & Orchestrator]
    │   │       └── agent-architect/
    │   │           ├── 00-overview/
    │   │           │   └── agent-architect-overview.md
    │   │           ├── 01-M4/                             [archetype ai-system (Section 5) — replaces backend-service slots; M4 now HAS prompt/eval/guardrail/token-budget (closes Section 2.4)]
    │   │           │   ├── 11-model-invocation/
    │   │           │   │   └── M4-model-invocation.md    [ai-system | LLM invocation via Gateway Resolver: routing, retry, ThoughtNode streaming]
    │   │           │   ├── 12-prompt-assets/
    │   │           │   │   └── M4-prompt-assets.md       [ai-system | Section 5.4.1 DAG synthesis Meta-Prompt & versioned Output Contract prompt templates]
    │   │           │   ├── 13-retrieval/
    │   │           │   │   └── M4-retrieval.md           [ai-system | Section 5.4.2 Discovery Agent RAG: AST context + Memory Bank → Task Context]
    │   │           │   ├── 14-memory/
    │   │           │   │   └── M4-memory.md              [ai-system | Section 5.4.2 Task Memory Context Package, pre-seeding, 4 memory tiers]
    │   │           │   ├── 20-guardrails/
    │   │           │   │   └── M4-guardrails.md          [ai-system | Section 5.4.3/5.4.5 Human Gate is_human_gate, Output Contract Validation, HITL]
    │   │           │   ├── 21-evaluation/
    │   │           │   │   └── M4-evaluation.md          [ai-system | Section 5.4.5 Reflection ≤3 rounds, SubTask Success Rate, output-contract eval oracle]
    │   │           │   ├── 22-token-budget/
    │   │           │   │   └── M4-token-budget.md        [ai-system | Section 5.4.4 3-tier Budget, BLOCKED_BUDGET, Safe Checkpoint at 100%]
    │   │           │   └── M4-design.md                  [mechanism | Plan-First DAG: workflow engine, DAG planner, zero-loss checkpoint/resume]
    │   │           ├── tests/
    │   │           │   └── submodule.feature             [BDD Tests: Plan-First Submission, Fallback Agent DAG & Snapshot Resume]
    │   │           ├── verification/
    │   │           │   └── fitness-self-check.md         [Module M4 Fitness Self-Check]
    │   │           ├── README.md
    │   │           ├── self-audit.md
    │   │           └── source-map.yml
    │   │
    │   ├── 07_security_architecture/                         [Security, Isolation & Governance Cluster]
    │   │   ├── 70-sandbox-lock/                              [Module M5: MicroVM Sandbox & Concurrency Lock]
    │   │   │   └── zero-trust-architect/
    │   │   │       ├── 00-overview/
    │   │   │       │   └── zero-trust-architect-overview.md
    │   │   │       ├── 01-M5/
    │   │   │       │   ├── 11-authn/
    │   │   │       │   │   └── M5-authn.md               [MicroVM Daemon Token & Internal Container Runner Authentication]
    │   │   │       │   ├── 12-authz/
    │   │   │       │   │   └── M5-authz.md               [In-Sandbox Zero-Trust Network Policy, Unauthorized Outbound Egress Block]
    │   │   │       │   ├── 13-session/
    │   │   │       │   │   └── M5-session.md             [Git Worktree Session Management, Automated Cleanup (24h retention / PR merge)]
    │   │   │       │   ├── 14-data/
    │   │   │       │   │   └── M5-data.md                [Data Schema Section 8.5: git_worktrees, sandboxes, concurrency_locks, streams]
    │   │   │       │   ├── 15-sandbox-engine/
    │   │   │       │   │   └── M5-sandbox-engine.md      [Design Section 5.5.1: gVisor / Firecracker MicroVM, Cgroup Limits, Sidecars]
    │   │   │       │   ├── 16-lock-engine/
    │   │   │       │   │   └── M5-lock-engine.md         [Design Section 5.5.2: Dynamic Lock repo_id:file_path, TTL 1800s, Heartbeat 30s]
    │   │   │       │   ├── 17-terminal-stream/
    │   │   │       │   │   └── M5-terminal-stream.md     [Design Section 5.5.3: Adaptive Terminal Streaming WebSocket, Buffer <200ms]
    │   │   │       │   ├── 20-secrets/
    │   │   │       │   │   └── M5-secrets.md             [Ephemeral Secret Injection into Sandbox Env, Secure Wipe on Teardown]
    │   │   │       │   ├── 21-audit/
    │   │   │       │   │   └── M5-audit.md               [Full Audit Logging of All Bash Terminal Commands Executed in MicroVM]
    │   │   │       │   └── M5-design.md                  [Module 5 Overall 4-Tier Clean Architecture Design]
    │   │   │       ├── tests/
    │   │   │       │   └── submodule.feature             [BDD Tests: Zombie Lock Release, Dynamic Lock Contention & Worktree Cleanup]
    │   │   │       ├── verification/
    │   │   │       │   └── fitness-self-check.md         [Module M5 Fitness Self-Check]
    │   │   │       ├── README.md
    │   │   │       ├── self-audit.md
    │   │   │       └── source-map.yml
    │   │   │
    │   │   └── 71-governance-safety/                         [Module M6: Risk Engine, Multi-Sig & Audit Ledger]
    │   │       └── secret-management-architect/
    │   │           ├── 00-overview/
    │   │           │   └── secret-management-architect-overview.md
    │   │           ├── 01-M6/
    │   │           │   ├── 11-authn/
    │   │           │   │   └── M6-authn.md               [Cryptographic Multi-Sig Signatures & Security Officer / Tech Lead Authentication]
    │   │           │   ├── 12-authz/
    │   │           │   │   └── M6-authz.md               [Approval Authorization: Medium (1 signature) vs High/Critical (Quorum of 2 signatures)]
    │   │           │   ├── 13-session/
    │   │           │   │   └── M6-session.md             [Approval Gate Session Lifecycle & Quorum Timeout]
    │   │           │   ├── 14-data/
    │   │           │   │   └── M6-data.md                [Data Schema Section 8.6: risk_assessments, approval_gates, signatures, audit_ledger]
    │   │           │   ├── 15-risk-engine/
    │   │           │   │   └── M6-risk-engine.md         [Design Section 5.6.1: 6-Axis Composite Risk Engine & 4 Hard Veto Triggers]
    │   │           │   ├── 16-multisig-gate/
    │   │           │   │   └── M6-multisig-gate.md       [Design Section 5.6.2: Multi-Sig Quorum, Missing-Role Block, Anti-Self-Approval]
    │   │           │   ├── 17-secret-scanner/
    │   │           │   │   └── M6-secret-scanner.md      [Design Section 5.6.3: 100% Git Diff Secret Scanning (Gitleaks/TruffleHog), PR Blocker]
    │   │           │   ├── 18-audit-ledger/
    │   │           │   │   └── M6-audit-ledger.md        [Design Section 5.6.4: Append-Only Hash-Chain WORM Audit Ledger, SHA-256 Tamper-proof]
    │   │           │   ├── 19-enterprise-pr-sync/
    │   │           │   │   └── M6-enterprise-pr.md       [Design Section 5.6.5: Automated GitHub PR Creation After Quorum & CI Status Polling]
    │   │           │   ├── 20-secrets/
    │   │           │   │   └── M6-secrets.md             [Multi-Sig Signing Key Protection & Secret Scan Rule Governance]
    │   │           │   ├── 21-audit/
    │   │           │   │   └── M6-audit.md               [Independent Audit Verification Workflow on the WORM Ledger]
    │   │           │   └── M6-design.md                  [Module 6 Overall 4-Tier Clean Architecture Design]
    │   │           ├── tests/
    │   │           │   └── submodule.feature             [BDD Tests: Hard Veto Elevation, Multi-Sig Quorum & Secret Leak Blocker]
    │   │           ├── verification/
    │   │           │   └── fitness-self-check.md         [Module M6 Fitness Self-Check]
    │   │           ├── README.md
    │   │           ├── self-audit.md
    │   │           └── source-map.yml
    │   │
    │   └── 08_quality_attribute_architecture/                 [SRE & System Quality Attributes Cluster]
    │       └── 80-observability-profiler/                    [Module M7-OBS: Advanced Observability & Continuous Profiler]
    │           └── observability-architect/
    │               ├── 00-overview/
    │               │   └── observability-architect-overview.md
    │               ├── 01-M7-OBS/
    │               │   ├── 11-signals/
    │               │   │   └── M7-OBS-signals.md         [Design Section 5.7.6: OpenTelemetry Traces, Prometheus Metrics, eBPF Profiler]
    │               │   ├── 12-slo/
    │               │   │   └── M7-OBS-slo.md             [Design Section 5.7.6: SLO/SLI Measurement (AST <=15s, Merge <=3s, CRDT <200ms)]
    │               │   ├── 13-frontend-isolation/
    │               │   │   └── M7-OBS-frontend-iso.md    [Design Section 4.3: Isolated Host telemetry.*, Independent SPA Bundle, Separate Auth]
    │               │   ├── 14-continuous-profiler/
    │               │   │   └── M7-OBS-profiler.md        [Design Section 5.7.6: CPU/Memory Flame Graphs (Pyroscope/Parca), Goroutine Dumps]
    │               │   ├── 15-sre-dashboard/
    │               │   │   └── M7-OBS-sre-dashboard.md   [Design Section 5.7.6: System Observer Dashboard: Golden Signals & Cgroups]
    │               │   ├── 16-telemetry-export/
    │               │   │   └── M7-OBS-telemetry-export.md[Design Section 5.7.6: Raw Telemetry Export API: OTel OTLP, pprof dumps, Prometheus]
    │               │   ├── 20-alerting/
    │               │   │   └── M7-OBS-alerting.md        [SRE Alerting: CPU/RAM Saturation, Zombie Lock Spikes, Error Budget Burn]
    │               │   ├── 21-retention/
    │               │   │   └── M7-OBS-retention.md       [Telemetry Retention Policy: Traces 30 days, Flame Graphs 90 days]
    │               │   └── M7-OBS-design.md              [Module M7-OBS Overall 4-Tier Clean Architecture Design]
    │               ├── tests/
    │               │   └── submodule.feature             [BDD Tests: Frontend Domain Isolation & Continuous Flame Graph Extraction]
    │               ├── verification/
    │               │   └── fitness-self-check.md         [Module M7-OBS Fitness Self-Check]
    │               ├── README.md
    │               ├── self-audit.md
    │               └── source-map.yml
    │
    ├── 03-cross-cutting/                                     [arc42 §8 | Shared Technical Mechanisms, Security, Infrastructure & Exceptions]
    │   ├── 00-overview.md                                    [01-system-architect | Cross-Cutting Concerns Strategy Overview]
    │   ├── 01-mechanisms/                                    [Detailed specifications of shared mechanisms spanning all 8 modules]
    │   │   ├── plan-first-locked-spec-submission.md          [01-system-architect | Plan-First Mechanism: LOCKED Spec -> Submit to AI -> DAG]
    │   │   ├── agent-memory-preparation-phase.md             [01-system-architect | Discovery Agent Mechanism synthesizing Task Memory Package before coding]
    │   │   ├── dynamic-agent-workflow-fallback-org-default.md[01-system-architect | JIT Workflow Auto-Synthesis Mechanism when Project config is absent]
    │   │   ├── four-tier-cascading-dynamic-configuration.md  [01-system-architect | 4-Tier Cascading Configuration Inheritance across 19 dynamic parameters]
    │   │   ├── three-tier-llm-budget-enforcement.md          [01-system-architect | 3-Tier LLM Budget Enforcement: Key -> Project -> Task]
    │   │   ├── microvm-sandbox-git-worktree-lifecycle.md     [01-system-architect | Provisioning, Isolation, and Auto-Teardown of MicroVM Sandbox Worktrees]
    │   │   ├── fcfs-spec-merge-concurrency-control.md        [01-system-architect | First-Come-First-Served Concurrent Write Conflict Resolution]
    │   │   ├── post-merge-ast-drift-recalculation.md         [01-system-architect | Post-PR Merge AST Re-Scan and Drift Score D Recalculation]
    │   │   ├── episodic-memory-auto-curation-pipeline.md     [01-system-architect | Post-Mortem Lesson Extraction and Memory Bank Curation Pipeline]
    │   │   └── dual-frontend-domain-isolation-enforcement.md [01-system-architect | Ingress Routing, mTLS, and Session Isolation Between Dual Frontends]
    │   ├── 02-security/
    │   │   ├── ai-token-masking-strategy.md                  [01-system-architect | PII & sensitive token masking before outbound LLM requests]
    │   │   ├── secrets-and-key-management.md                 [01-system-architect | Secret Management, Org API Key Pool & Encryption-at-Rest]
    │   │   ├── security-and-auth.md                          [01-system-architect | Authentication Architecture, GitHub OAuth App & Session Tokens]
    │   │   ├── threat-model.md                               [01-system-architect | Platform-wide STRIDE Threat Model across the Multi-Agent system]
    │   │   └── zero-trust-sandbox-perimeter.md               [01-system-architect | Zero-Trust Security Perimeter for AI Code Execution Sandboxes]
    │   ├── 03-infrastructure/
    │   │   ├── docker-dual-mode-setup.md                     [01-system-architect | Dual-Mode Docker Compose Strategy: Test Mode vs Prod Mode (SRS Chapter 13)]
    │   │   ├── seed-data-test-fixtures-catalog.md            [01-system-architect | Seed Data Catalog covering 100% of test scenarios in Test Mode]
    │   │   └── cloud-native-k8s-microvm-deployment.md        [01-system-architect | Production Deployment Blueprint on Kubernetes & Firecracker]
    │   ├── 04-fitness-functions/                             [Automated architectural fitness functions enforcing NFRs]
    │   │   ├── 00-overview.md                                [01-system-architect | Architectural Fitness Functions Overview]
    │   │   ├── FIT-001-doc-code-drift-gate.md                [01-system-architect | Drift Score Gate Thresholds: D <= 0.3 In-Sync, D > 0.7 Blocked]
    │   │   ├── FIT-002-ast-scan-latency-bound.md             [01-system-architect | AST Scan Latency Bound: <= 15s per 100K LOC]
    │   │   ├── FIT-003-crdt-presence-latency-bound.md        [01-system-architect | CRDT Keystroke & Presence Latency Bound: < 200ms]
    │   │   ├── FIT-004-multisig-quorum-enforcement.md        [01-system-architect | Mandatory Minimum 2-Signature Quorum for High/Critical Changes]
    │   │   ├── FIT-005-system-observer-domain-isolation.md   [01-system-architect | Forbid Observer from calling Business APIs and Workspace from calling Profiler]
    │   │   ├── FIT-006-lock-ttl-heartbeat-enforcement.md     [01-system-architect | Dynamic Lock Bounds: TTL 1800s, Heartbeat 30s, Wait Timeout 60s]
    │   │   └── FIT-007-zero-loss-snapshot-integrity.md       [01-system-architect | 100% State & Artifact Snapshot Integrity on Agent Interruption]
    │   ├── 05-exceptions/                                    [Complete Alternate & Exception Flow Analysis per Alternate_Flows_Analysis.md]
    │   │   ├── 00-exception-catalog.md                       [01-system-architect | Master Catalog of All Exception Codes and Scenarios EX-xxx]
    │   │   ├── EX-ONB-onboarding-exceptions.md               [01-system-architect | EX-ONB-01..04: Expired 72h invite link, OAuth denial, duplicate email]
    │   │   ├── EX-SPC-spec-exceptions.md                     [01-system-architect | EX-SPC-01..05: CRDT disconnect, FCFS conflict, Spec lock failure]
    │   │   ├── EX-AST-ast-exceptions.md                      [01-system-architect | EX-AST-01..03: Unrecognized syntax error, oversized file >100K LOC]
    │   │   ├── EX-AGT-agent-exceptions.md                    [01-system-architect | EX-AGT-01..06: Budget exhaustion BLOCKED_BUDGET, crash snapshot, infinite loop]
    │   │   ├── EX-LCK-lock-exceptions.md                     [01-system-architect | EX-LCK-01..04: Zombie Lock, Heartbeat timeout, Tech Lead Force Release]
    │   │   ├── EX-GOV-governance-exceptions.md               [01-system-architect | EX-GOV-01..05: Hard Veto triggered, missing approver role, CI failure]
    │   │   └── EX-OBS-observability-exceptions.md            [01-system-architect | EX-OBS-01..03: Unauthorized Observer Web App access, profiler dump failure]
    │   └── 06-reference-library/
    │       ├── clean-architecture-modular-monolith.md        [01-system-architect | 4-Tier Clean Architecture Modular Monolith Reference Pattern & Boundary Rules]
    │       ├── model-context-protocol-mcp-integration.md     [01-system-architect | Model Context Protocol (MCP) Integration Specification (stdio, SSE, HTTP)]
    │       └── graph-rag-causality-ledger.md                 [01-system-architect | Graph RAG Reference Pattern Combining AST Call Graph & Causality Ledger]
    │
    └── 04-delivery/                                          [arc42 §11 | Delivery, Implementation Roadmap, Acceptance & Operations]
        ├── 00-planning/
        │   ├── mvp-implementation-roadmap.md                 [downstream | Sprint 0 through Sprint 4 Implementation Roadmap per MVP_Requirements.md]
        │   ├── delivery-milestones.md                        [downstream | Acceptance Milestones: M1..M6 + M7 Full Collab + Observer Console]
        │   └── work-breakdown-structure.md                   [downstream | Detailed Work Breakdown Structure (WBS) Across All 8 Modules]
        ├── 01-quality/
        │   ├── e2e-testing-strategy.md                       [downstream | E2E Testing Strategy: MicroVM Sandbox, WebSockets & Multi-Sig]
        │   ├── security-compliance-acceptance-matrix.md      [downstream | Information Security Acceptance Matrix, Secret Scan & WORM Ledger]
        │   └── performance-benchmark-criteria.md             [downstream | Performance Benchmark Criteria: AST <=15s, Merge <=3s, CRDT <200ms]
        ├── 02-audit/
        │   ├── requirement-traceability-matrix.md            [downstream | End-to-End Traceability Matrix: CLR -> REQ -> Design -> Code -> Test]
        │   ├── architecture-completeness-audit.md            [downstream | Phase 1 Architecture Completeness Self-Assessment Report]
        │   └── e2e-gap-closure-verification.md               [downstream | Verification Report Confirming Closure of All 36 Master Register Gaps]
        └── 03-ops/
            ├── deployment-runbook.md                         [downstream | Dual-Mode Docker Compose Deployment Runbook (Test vs Prod)]
            ├── disaster-recovery-and-backup.md               [downstream | Disaster Recovery Playbook: API Key Exhaustion, Redis Outage, WORM Ledger Restore]
            └── operational-troubleshooting-playbook.md       [downstream | Operations Troubleshooting Playbook: Zombie Lock Release, Quorum Bypass, AST Fix]
```

---

## 3. COMPLETENESS SUMMARY (100% COVERAGE GUARANTEE)

1. **Total Document Tree Scale:** With P8 cardinality (Section 19) applied, file count scales proportionally with actual architectural instances rather than remaining fixed — the `00-system-views/` branch alone now materializes **12 use cases + 12 activities + 10 sequences + 4 state machines + 8 class diagrams + per-container component diagrams** in place of the 3 singleton diagrams of the legacy layout, all governed under the `maximal` profile.
2. **Complete Closure Across All 9 Source Analysis Documents:**
   - **`Requirements_Gap_Analysis_Report.md`:** Dedicated `architecture/01-global-strategy/05-governance/gap-register/` directory covering all 36 GAPs across Auth, Budget, Spec, AST, DAG, Lock, Governance, and Observability.
   - **`RBAC_Permission_Matrix.md`:** Full coverage of 35+ atomic permissions, 6 default roles, Custom Roles, and 4-tier hierarchical inheritance.
   - **`Business_Rules_Analysis.md`:** All 4 concrete state machines, the 6-axis composite Blast Radius Risk scoring model, and state transition guard matrices.
   - **`Data_Integration_Analysis.md`:** Complete entity specifications across all 7 database table groups, 6 external system integrations, and real-time WebSocket/Redis synchronization protocols.
   - **`Dynamic_Configuration_And_Docker_Compose_Strategy.md`:** All 19 dynamic parameters, 4-tier cascading resolution, and Dual-Mode Docker Compose architecture (Test Seed vs Prod).
   - **`Alternate_Flows_Analysis.md`:** Every `EX-xxx` exception code across all 6 core operational subsystems.
   - **`MVP_Requirements.md`:** Complete In-Scope / Out-of-Scope boundaries, 12 use case pages `UC-001..012`, and 10 E2E runtime scenarios `SCN-000..009`.
   - **`extracted_text.txt`:** All 13 Core Technical Decisions formalized as 13 independent ADR files.
3. **V3 Compliance (Acceptance Criteria, Not Merely Aspirational):**
   - **Grouped by Concern:** `00-system-views/` = 6 views (`01-context` → `06-runtime`), adding `05-information/`.
   - **P8 Cardinality (Section 19):** No diagram remains a singleton when the system has multiple instances — `activities/{use-case}/`, `sequences/{scenario}/`, `state-machines/{aggregate}/`, `components/{container}/`, `classes/{context}/`.
   - **Subject as Directory (Section 4.3):** `02-apis/{api}/` carries 11 contract files; `01-data/{entity}/`, `03-messages/{message}/`, `04-external/{system}/`, `05-state-machines/{aggregate}/`.
   - **Domain-Accurate Archetypes (Section 5):** The AI cluster uses `ai-system` — M4 includes prompt/eval/guardrail/retrieval/memory/token-budget slots; frontend apps reside under the `frontend` archetype.
   - **Page Class + Provenance per Slot (Section 7, P7):** Annotated as `[page_class | producer | scope]`.
   - **Cardinality Matrix:** 12 UCs · 12 activities · 10 sequences · 4 state machines · 8 class diagrams · 7 API folders · 5 BPMN processes · 2 deployment environments.

---

## 4. UML NOTATION COVERAGE — DELIBERATE BY DESIGN, NOT OMISSION

A fair question: UML 2.x defines **14 diagram types**, so why does the tree use only a subset? Answer: the tree materializes diagrams according to **the architectural concerns that must be answered**, not to check off every box in the UML specification (matching C4's principle of "draw only what adds value" and arc42's "representative selection"). More importantly, **a diagram slot is valid only when a concrete skill produces it** (Section 9b) — the tree never creates a slot for a diagram type that `exported_skills/tasks/07_system_modeling/` does not produce. Below are all 14 UML 2.x diagram types measured against the 12 actual modeling skills, with the exact rationale for each.

| # | UML 2.x Diagram | Category | In Tree? | Location / Producer Skill | Rationale |
|:--:|---|:--:|:--:|---|---|
| 1 | Class | Structural | ✅ | `03-structure/classes/{context}/` ← `class-diagram` | One class diagram per bounded context |
| 2 | Component | Structural | ✅ | `03-structure/components/{container}/` ← `component-diagram` | C4 L3, one per container |
| 3 | Deployment | Structural | ✅ | `04-deployment/environments/{env}/` ← `deployment-diagram` | One per deployment environment |
| 4 | **Package** | Structural | ⭕ Indirect | Directory tree itself + `logical-l2-submodules.md`, `container-module-mapping.md` | The directory hierarchy **is** the package structure; redrawing it is redundant |
| 5 | **Object** | Structural | ❌ Deliberate | — | Instance snapshot of a Class diagram; concrete examples belong in use-case/test pages rather than a separate diagram |
| 6 | **Composite Structure** | Structural | ❌ Deliberate | — | Internal parts/ports/connectors — duplicates C4 component + UML class diagrams and rarely carries distinct architectural weight |
| 7 | **Profile** | Structural | ❌ Deliberate | — | Meta-model / stereotype extension mechanism for **building UML tooling**, not a system architecture artifact |
| 8 | Use Case | Behavioral | ✅ **Textual** | `02-functional/use-cases/UC-{NNN}` (Section 8) | V3 decision: one structured page per use case (actor → flow → exceptions → acceptance) instead of oval bubble diagrams — clearer and deterministically verifiable |
| 9 | Activity | Behavioral | ✅ | `02-functional/activities/{use-case}/` ← `activity-diagram` | One activity diagram per branching use case |
| 10 | State Machine | Behavioral | ✅ | `06-runtime/state-machines/{aggregate}/` ← `state-diagram` | 4 core aggregates |
| 11 | Sequence | Behavioral | ✅ | `06-runtime/sequences/{scenario}/` ← `sequence-diagram` | One sequence diagram per `SCN-*` |
| 12 | **Communication** | Behavioral | ❌ Deliberate | — | Formally **isomorphic to Sequence diagrams** in UML (same interactions, different layout) → already covered by Sequence |
| 13 | **Interaction Overview** | Behavioral | ❌ Deliberate | — | Activity diagram whose nodes are interactions → already covered by Activity + Sequence |
| 14 | **Timing** | Behavioral | ⚠️ **TRUE GAP** | No producer skill yet | This system has **hard** real-time SLO bounds (CRDT <200ms, heartbeat 30s, lock TTL 1800s) — warrants adding a `timing-diagram` skill |

**Takeaway from the table:** 6 diagram types drawn directly + Use Case (structured prose) + Package (directory hierarchy) = **8/14 represented**; **5 types deliberately excluded with clear rationale** (Object, Composite Structure, Profile, Communication, Interaction Overview) because they duplicate existing views or carry no architectural load; and **exactly 1 genuine gap is Timing** — acknowledged transparently because the system has measurable real-time timing constraints.

> **Follow-up Action Item (Open Proposal):** Add a `timing-diagram` skill under `07_system_modeling`, then open the slot family `06-runtime/timings/{constraint}/uml-timing-diagram.md` `[diagram · per_timing_constraint]` for hard timing SLOs (CRDT keystroke latency, presence heartbeat, lock TTL/heartbeat, budget checkpoint). Until that producer skill exists, **do not** add the slot — upholding Section 9b's rule of "one producer skill per slot". This remains open decision #6 for V3.

In short, the tree **has zero silent omissions** — it covers the exact diagram types produced by the 12 modeling skills, documents why 5 types are excluded, and explicitly names the single type (Timing) worth adding next. "Complete" here means **complete to answer every stakeholder concern**, not filling 14 boxes of a notation catalog.
