# Current core output contract

Read the current workspace marker, source revisions, accepted baseline, and effective
skill grant before authoring. Use `sdd-workspace.yml` for registered artifacts,
obligations, and optional `document_coverage` basis references. A proposed grant is not write authority.

## Coverage policy, layout profile, and execution budget

Keep three concepts strictly separate:

- **Coverage and depth policy (`maximal` | `standard` | `minimal` | `seed`):** determines which source concerns must be accounted for and how deeply each mechanism, contract, state machine, and flow must be specified.
- **Layout and catalog profile:** organizes paths and reference families without dropping applicable concerns that lack a pre-named slot.
- **Execution budget:** governs task batching, turn count, token windows, and runtime limits. Never shrink the target document tree to fit a single model call or review packet.

**Maximal definition:** cover every applicable concern derived from the frozen, reconciled source inventory and design each mechanism to implementation depth. Use KISS only to remove redundant prose after full coverage and depth witnesses are preserved.

## Source accounting and completeness metrics

Never use generated pages as the denominator of their own completeness. Reconcile an independent source manifest and concern inventory (`U`) where every item carries an explicit disposition:

- `covered`: has a canonical owner, body witness spans, and required depth dimensions.
- `gap`: applicable and required by source, but design or evidence is missing or conflicting.
- `deferred`: explicitly postponed by an authorized decision with owner and review trigger (accounted, not covered).
- `not_applicable`: excluded with source-grounded rationale and applicability evidence.

Report six metrics separately: **accounting completeness**, **design coverage**, **critical coverage**, **depth completeness**, **exclusion/defer count**, and **source intake completeness**. Never collapse accounting 100% into a claim of 100% design coverage.

## Paths and ownership

Use paths relative to the selected spec workspace. Follow the accepted grant and each
artifact's owner. Register each new source artifact with a stable ID, path, kind, and
owner through an isolated proposal. Use configuration capability for registry changes.
Ask the coordinator when the required capability or owner is absent.

Split a page whenever a mechanism, contract, state machine, technology integration, ADR,
or end-to-end journey has an independent lifecycle, guard set, failure/recovery model,
or consumer boundary. Merge only when all source obligations, canonical ownership,
body witnesses, and bounded review scopes are preserved.

Give readers a title, purpose, source references, applicable contracts, unresolved
questions, and links to related registered documents. Use a short contents list when
the document needs one. Preserve stable anchors and IDs during reorganization.

## Facts, depth witnesses, and review evidence

Keep confirmed facts, proposed assumptions, unknowns, and human decisions distinct.
Trace normative behavior to source clauses and exact revisions. State the owner and
reversal trigger for each assumption. Record missing evidence as a question or gap.
Do not invent a measured value, approved decision, resolved question, or passing check.

For each applicable mechanism or contract, provide body witnesses covering:
(1) authority, purpose, boundary, and owner; (2) trigger, actor, input, precondition, and tenant/permission scope;
(3) exact API/message/schema/command contract and versioning; (4) algorithm/sequence, states, guards, invariants, and transitions;
(5) side effects, transaction/consistency boundary, ordering, and concurrency; (6) failure/unknown outcomes, cancellation, retry/idempotency, and recovery;
(7) configuration keys, defaults, units, limits, or explicit UNKNOWN status; (8) observable signals, audit trail, and verification scenarios;
(9) consumers and dependent artifacts. Mentioning an ID in frontmatter or an RTM table does not satisfy depth coverage.

Preserve values, units, routes, IDs, code, normative words, negation, and UNKNOWN.
Read the writing profile before repair. Use bounded repair and retain the last safe
draft. Short technical English is the goal; partial checks do not certify ASD-STE100.

Reference exact source and consumer revisions in review. Use code-point spans and
literal quotes. Do not replace missing evidence with a numeric score or confident prose.
Send findings and repairs to the artifact owner. A reviewer does not write a human decision.

## Candidate and handoff

Author with an isolated core proposal and the expected source revision. Check the
returned candidate ID. Run deterministic checks and regression readiness on that
candidate. Preserve actual results, including incomplete review and stale input.

Report the candidate, changed IDs, affected consumers, coverage metrics, omissions/gaps,
actual checks, remaining questions, and next owner. Task completion creates a checked candidate.
Obtain independent review and separate signed human acceptance before publication.

Use the core task plan, lease, and event store for execution. Do not create a second
phase ledger, write engine state, or reuse approval from an imported workspace.
Process old input through the separate migration tool and review its mapping first.
