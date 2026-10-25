# Template Standard

## Page Classes

Every page declares its class: overview, mechanism, contract, data, decision, diagram, catalogue, or verification. The class determines semantics; a generic checklist cannot substitute for them.

- Overview: scope, owner, topology, navigation, key decisions, and status.
- Mechanism: trigger, preconditions, ordered algorithm, state, defaults, failures, recovery, and observability.
- Contract: operations/fields, invariants, errors, idempotency, compatibility, and examples.
- Data: grain, owner, lifecycle, constraints, migration, retention, and reconciliation.
- Decision: context, forces, options, choice, consequences, reversal trigger, and evidence.
- Verification: risk, fixture, oracle, command, expected diagnostic, actual result, and freshness.

## Anti-Padding Rules

One fact has one owner page. Do not inflate depth with repeated generic prose, synthetic IDs, renamed nouns, or empty folders. Lists and tables require a surrounding normative explanation. Explicit unknowns are preferable to plausible invention.

## Placeholders

`{{...}}`, `TODO`, `TBD`, `FIXME`, and unclassified `unknown` fail final validation. An accepted unknown must include owner, decision route, affected artifacts, and safe interim behavior.
