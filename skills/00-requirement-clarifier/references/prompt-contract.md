# Prompt Contract

This contract defines the minimum prompt, context, and output rules every SDD skill must obey. It is shared infrastructure: edit this master copy, then run `python scripts/compile_foundation_contracts.py` from the framework root.

## 1. Intake Schema

Before drafting, identify the current workspace containing `sdd-workspace.yml`,
the active skill, accepted author grant and write scope, task objective, exact
source artifact IDs and revisions, candidate origin, required outputs and human
questions. Read every required method reference. Preserve stable IDs, source
facts, assumptions, unresolved questions and defer reasons distinctly.

## 2. Required Preflight

1. Inspect the current core workspace. Initialize a new empty destination explicitly;
   migrate old input into a separate destination. Repair malformed markers.
2. Read the active SKILL.md, workflow contract, required and applicable conditional
   references completely, including the selected child skill's method.
3. Confirm accepted capabilities and scope. A package contract cannot grant itself
   authority. Bind proposals to the exact origin snapshot and artifact revisions.
4. Route requirement sources to the clarifier and authored architecture plans to
   the architect. Generated projections do not become source authority.
5. Before architecture drafting, select and document the smallest sufficient tree.
   Record planning metadata in a registered planning artifact; only supported core
   fields belong in the workspace configuration.
6. Submit isolated candidate operations. Engine state and human decisions are
   written through their respective APIs and human channel.

Missing inputs produce a blocking finding. A checked candidate still requires
independent review and separate signed human acceptance before publication.

## 3. Allowed Context

Use registered source artifacts with current revisions, confirmed decisions,
accepted grants, shared contracts and the skill's method and templates. Cite
upstream stable IDs and paths. Keep assumptions and future proposals distinct
from confirmed authority. Route requirement deltas through the clarifier and
cross-context decisions through the architect.

## 4. Output Rubric

Every generated or changed artifact must satisfy this rubric:

| Criterion | Pass condition |
|---|---|
| Traceability | Cites upstream source paths and stable IDs. |
| Ownership | Is written only under the active skill's allowed output root. |
| Completeness | Covers the requested scope or records explicit blocking reasons. |
| Source coverage | Shows which upstream artifacts are covered by this output. |
| Executable detail | Provides concrete contracts, defaults, commands, schemas, or boilerplate when the skill owns implementation guidance. |
| Self-check | Includes a self-check or validator evidence appropriate to the artifact type. |

## 4.1 Output Root Rule

When operating inside another project repository, write SDD artifacts only under
the configured output root, default `documents/`. Do not create
`sdd-workspace.yml`, architecture folders, `tickets/`, `uml/`, `clarified-requirements.md`,
`delivery-log.md`, or `change-request.md` directly at the project root. Treat
paths in registry/contract files as relative to the SDD output root.

## 5. Blocking Behavior

Return a blocking finding instead of guessing when:

- Required source paths are missing.
- The workspace, candidate origin, source revision or accepted grant is stale.
- Skill intake evidence is missing after preflight.
- A child skill needs to write outside its subtree.
- A visual child lacks usable SSoT source paths.
- A shared GitHub, git, or remote state action lacks explicit user confirmation.

## 6. Request Payload

When a child skill needs an orchestrator-owned decision, return this payload:

```yaml
kind: adr | contract | handoff | req | taxonomy | classify
raised_by: <skill-name>
request_id: <stable hash of kind + motivation + blocked files>
motivation: |
  <why the missing decision is load-bearing>
recommendation: |
  <preferred resolution>
alternatives:
  - <option with pros and cons>
blocked_files:
  - path: <owned output path>
    reason: BLOCKED-ON <kind>
resolution_status: pending | accepted | rejected | superseded
```

Repeated identical request payloads must reuse the prior resolution instead of creating duplicate work.

The orchestrator resolves request payloads through a single revision-bound decision loop:

1. Locate any existing request with the same `request_id`.
2. Reuse accepted or rejected resolutions instead of creating a duplicate.
3. If no resolution exists, add one orchestrator-owned response with `resolved_by`, `resolution_status`, `resolution_summary`, and touched stable IDs.
4. Re-run the blocked child only after the resolution is accepted or superseded.

## 7. Deterministic Naming

Generated identifiers and files must be deterministic from their source scope:

| Artifact | Naming rule |
|---|---|
| Requirements | `REQ-###`, allocated append-only in source order. |
| Clarifications and assumptions | `CLR-###` and `ASM-###`, allocated append-only in clarification order. |
| APIs, messages, entities, ADRs | `API-###`, `MSG-###`, `ENTITY-###`, `ADR-####-<slug>.md`. |
| Diagrams | `<stable-context-slug>-<diagram-kind>.md`, with diagram node IDs derived from stable IDs or context slugs. |
| Gates | `GATE-###`, allocated append-only in finding order. |
| Request payloads | `REQP-<short-hash>`, where the hash is over kind, motivation, and blocked files. |
| Source maps | `SMAP-<short-hash>`, where the hash is over source path, stable ID, and derived artifact. |

Names must not depend on model phrasing, wall-clock time, random numbers, or sibling artifact scan order except where the schema explicitly calls for a run ID.

Deterministic text is not automatically a stable identifier. Path hashes, page ordinals, page slugs, and vocabulary-by-page products such as `SPEC_<hash>_*`, `60-06-CONVERSION_ERRORS`, or `provider_reference_conversion_errors` are forbidden as traceability unless a canonical registry declares the family, definition owner, and consumer. Never mint identifiers or repeated prose solely to satisfy density, depth, clone, or traceability gates.

## 8. Source Map Record

Derived artifacts should use this source-map shape when staleness matters:

```yaml
map_id: SMAP-<stable hash>
source_path: <upstream file>
stable_id: <REQ/API/MSG/ENTITY/ADR/etc>
source_hash: <hash at generation time>
source_skill: <skill that owns the source artifact>
derived_artifact: <output file>
owner_skill: <skill package>
regeneration_reason: initial | upstream-change | correction | manual-review
```

## 9. Runtime State

The core scheduler records planned, ready, running, notify, waiting-for-human,
complete, failed, blocked, rejected and cancelled task states. Task leases bind
an exact attempt. Heartbeats renew that lease; late results are fenced after
cancellation, expiry or retry. Source, skill input, policy and candidate changes
require a new plan. Cost is unavailable when the host supplies no usage evidence.

Human dispatch permission, independent semantic review, candidate acceptance
and publication are distinct decisions. Notify expiry is never human approval.
Task completion creates checked candidate evidence; it grants no publication.

## 10. Agentic Build Loop

Read complete skill inputs and accepted grants; preview the bounded task plan;
resolve human questions; claim the approved exact attempt; propose scoped
operations; run deterministic and historical regression checks; obtain independent
semantic review; request separate signed human acceptance; publish the accepted
candidate through the core publication API.

Process one declared scope per task. Order overlapping writers explicitly and
bound independent concurrency through the accepted runtime policy.

## 11. Depth Rubric (Anti Shallow-Listing)

Every skill must describe the how and the why, not only the what. A bullet list of capabilities is not a specification. This rubric is shared by all skills; the `01-system-architect` rules R1-R9 are the orchestrator-specific instance of it, and `architect-runtime sdd check <workspace> --full` is its executable check.

| Artifact class | A description passes only when it carries |
|---|---|
| Requirement | the rule, its rationale, and a measurable verification -- not a one-line restatement. |
| Mechanism / behavior | trigger, precondition, ordered algorithm steps, named defaults with concrete values, failure modes, and guard conditions. |
| API / contract | operation semantics, error taxonomy, idempotency, and invariants -- not only a field or endpoint list. |
| Data / entity | grain, ownership, lifecycle, and constraints -- not only column names. |
| Diagram | element traceability plus the upstream stable IDs it derives from. |

Anti-listing rules (apply to every generated page):

- Do not ship a long shallow bullet list that only states what the system does. Pair every table or list with a normative "how it works / why" prose block.
- An identifier, default, header name, or signature that a source document carries must appear verbatim in the derived artifact; paraphrase is not coverage.
- Mark an item "covered" only after a literal search for it succeeds in the target page. Self-reported coverage written from memory verifies nothing.
- Prefer the smallest concrete contract (values, schema, boilerplate) over an abstract summary when the skill owns implementation guidance.
- One fact has one owner page. Other pages cross-link its canonical stable ID rather than copying the module vocabulary into every concern page.
- A page must answer its page-class question. Mapping pages specify source-to-canonical conversion and loss/unknown behavior; invariant pages specify predicate, owner, trigger, violation, and test oracle; state pages specify legal transitions and guards; diagram pages specify source and element traceability. Generic mutation/idempotency prose cannot substitute for those semantics.
- Before expanding a repeated page role across modules, run semantic uniqueness and clone checks on a representative prototype. A red gate blocks further fan-out; do not append filler paragraphs, synthetic IDs, or renamed nouns to game it.

A page that satisfies the structural Page Contract but fails this rubric is shallow and must be revised, not accepted.

## 12. Do and Don't Checklist

Shared, cross-skill guardrails. Each tier's `tier-taxonomy.md` adds only
tier-specific rows and links back here rather than restating these.

| Do | Don't |
|---|---|
| Reference a sibling context through a `architecture/02-domains/_shared-contracts/` stable ID or port. | Traverse `../` into a sibling `architecture/02-domains/<other>/` from code or docs. |
| Use relative links; the repo-doc linter verifies them. | Use `file:///` absolute paths or root-absolute paths. |
| Cite a stable ID or a `#section-anchor` that the target actually defines. | Invent an ID or link a header that does not exist. |
| Isolate vendor SDKs in integration-adapter tier `60-`. | Import Stripe/Twilio/AWS/OpenAI in `70-` domain modules. |
| Pair every list or table with a normative "how/why" prose block (Depth Rubric). | Ship a shallow bullet list as a specification. |
| Get explicit chat confirmation before any shared-state git/GitHub action. | Execute an irreversible action and log the confirmation afterwards. |
| Consume current registered sources and confirmed decisions. | Use blocked future-phase context as design authority. |

Violations are workflow failures, not style preferences; the corresponding gates in `architect-runtime sdd check <workspace> --full` (or `architect-runtime cli gate run --scope workspace <workspace>`) enforce the machine-checkable rows.
