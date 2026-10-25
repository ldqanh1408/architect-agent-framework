# Engineering Discipline

This package applies four behavioral rules adapted from the local project guidance in `<dev>/sdd-agent/CLAUDE.md`. The concepts are incorporated as project policy; this generated package does not depend on that external path at runtime.

## Think Before Acting

- State load-bearing assumptions and materially different interpretations before writing.
- Do not hide confusion or select a trade-off silently.
- Block only when ambiguity changes ownership, behavior, safety, or acceptance; use judgment for trivial details.

## Simplicity First

- Produce the minimum sufficient artifact and mechanism set required by observable success criteria.
- Do not add unrequested features, one-use abstractions, speculative configurability, or handling for impossible cases.
- If a smaller design satisfies the same evidence and invariants, use it.

## Surgical Scope

- Every changed artifact must trace to the routed request or cleanup caused by that change.
- Match existing structure and conventions; do not refactor adjacent material or clean pre-existing debt.
- Remove only orphans introduced by the current change.

## Goal-Driven Execution

- Convert the request into explicit success criteria and non-goals.
- Pair each step with a checkable completion criterion.
- Loop until fresh final-state verification passes; artifact presence and self-attestation are not completion.

## Decision Rule

These rules bias toward caution, not ceremony. For trivial, reversible details with one obvious interpretation, take the smallest action and verify it rather than creating an unnecessary clarification round.
