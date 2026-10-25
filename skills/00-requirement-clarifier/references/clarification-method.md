# Clarification method

Read this guide before interpreting a new brief or requirement delta. It is active in both workspace modes.

## Contents

- Conversation and evidence
- Four clarification layers
- EARS and priority
- Atomic source coverage
- Supplement mode
- Output and exit evidence

## Conversation and evidence

Act as a plain-spoken requirements partner. Explain the consequence of an uncertainty or sketch a concrete scenario before asking about it. Follow the user's vocabulary, restate decisions accurately, and do useful work with evidence already available. Ask a small coherent group, normally one to three material questions. Avoid re-asking resolved questions or imposing a minimum number of turns.

Use the four layers as a depth map, not a questionnaire to dump on the user. Stop interviewing when the load-bearing ambiguities are resolved or explicitly assigned, rather than when a turn quota is met. If the user does not know, propose an assumption with alternatives, impact and a falsifiable reversal trigger. Keep it `assumed` until confirmed. Never turn silence into confirmation.

Do not promise commercial pricing, implementation dates or operational guarantees on the user's behalf. Budget and timeline are expectations unless a stakeholder explicitly makes them technical constraints.

## Four clarification layers

| Layer | Establish | Destination |
|---|---|---|
| Business scope/value | problem, current pain, beneficiary, measurable outcome, goals/non-goals | problem brief |
| System boundary/actors | human roles, external systems, who initiates/receives each interaction, primary journeys | actors, boundaries, scenarios |
| Features/priorities | capabilities, sources of data, MVP and later scope, acceptance criteria | stable clauses and MoSCoW |
| Quality/operation | relevant latency/throughput/availability, retention, security, locale, recovery and operating constraints | quality scenarios, assumptions and questions |

A layer may be not applicable only with a scope-grounded explanation. A vague number such as “fast” is a question cue, not proof of a violated requirement. Record a latency target only if provided, derived from explicit inputs, or visibly proposed for confirmation. Include workload, percentile, measurement point and conditions when those determine the meaning.

## EARS and priority

Normalize agreed behavior into a testable form; keep the user's language where useful. Use the five EARS forms to separate behavior shapes:

| Shape | Form | Example without an invented numeric target |
|---|---|---|
| Ubiquitous | The system shall response. | The service shall retain the source identifier with each imported record. |
| Event-driven | When trigger, the system shall response. | When an order is submitted, the service shall return its order identifier. |
| State-driven | While state, the system shall response. | While disconnected, the client shall show which orders remain pending. |
| Unwanted event | If condition, then the system shall response. | If the same event is delivered again, the service shall avoid a second debit. |
| Optional feature | Where feature is enabled, the system shall response. | Where export is enabled, the service shall offer the agreed export format. |

Describe the actor, trigger/state, observable response, relevant exception and verification method. EARS English keywords are not a semantic quality test; an equivalent Vietnamese statement may be complete. Split independently verifiable behaviors while preserving related conditions. Do not split by an arbitrary action-count threshold.

Use **Must / Should / Could / Won't this release**. Record who set priority and the value/dependency behind it. Do not silently make all clauses Must. “Won't” is an explicit scope boundary, not a requirement deleted from the inventory.

## Atomic source coverage

1. Read the complete source and any accepted baseline. Inventory source clauses before restructuring them. Preserve existing FR/NFR/BR/URD identifiers; create stable source identifiers where absent.
2. Assign stable `CLR-*` identifiers. Insertion, reordering and rename do not renumber them. Changes in meaning change the revision; split/merge record lineage.
3. For each clause record source artifact/path, revision, anchor or line span, exact excerpt and origin IDs. A paraphrase is the requirement, not the excerpt. Do not move a quote to a nearby matching line after a source change without revisiting the binding.
4. Keep confirmed requirements, proposed `ASM-*` assumptions and unresolved `OQ-*` questions distinct. Every assumption has a reversal trigger; every material question has an owner and consequence of no answer.
5. Check the denominator against **all source clauses**, not only the clauses already emitted. Each is covered, explicitly deferred with authority, excluded with a reason, or an open gap. One sentence can contain multiple obligations; one obligation can have multiple witnesses.
6. Do not invent thresholds, quantities, API names or scope from templates. A derived estimate includes its inputs and derivation and remains an assumption until decided.

Example coverage row:

`URD-14 → CLR-008 / source brief.md, revision <observed hash>, lines 21–22, exact excerpt / confirmed`

The hash and lines come from the actual artifact. Placeholders in this example are not evidence for a real run.

## Supplement mode

Use this mode when an existing specification or accepted requirement baseline receives new intent.

- Read current requirements, relevant contracts, traceability and baseline decisions without editing them.
- Classify each delta as **new-requirement**, **modify-existing**, **remove-or-deprecate** or **clarification-only**.
- Ask only about missing acceptance criteria, affected actors, NFRs, compatibility and migration consequences of the delta.
- Produce a scoped delta (normally `clarified-requirements-delta.md`) with stable `CLR-D*` IDs and references to affected `REQ`, `API`, `ENTITY`, `ADR` and source clauses.
- Preserve the superseded requirement and its history. A request to remove behavior is not proof all downstream consumers were removed.
- Hand the delta to the architect with impact and unresolved questions. Let the selected lifecycle record change approval; do not change the architecture or record approval yourself.

## Output and exit evidence

Use `assets/clarified-requirements-template.md` as a content template. Produce the problem brief, sourced clauses with MoSCoW, source coverage, assumptions and questions. Follow the workspace's output contract for paths; do not invent a second ledger beside engine state.

The handoff lists what was confirmed, what is still assumed, blocking questions, changed IDs, affected consumers and actual checks run. A draft may be useful while incomplete. Do not label it accepted or phase-complete because the prose looks polished.
