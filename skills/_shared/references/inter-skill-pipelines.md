# Inter-Skill Pipeline

## Producer Contract

A producer handoff includes artifact path, stable IDs, source hash, artifact hash, owner, validator argv/exit/time, and status. `complete` without fresh gate evidence is invalid.

## Consumer Contract

A consumer verifies identity, ownership, status, hash freshness, and required diagnostics before use. Missing or stale authority blocks execution; the consumer must not reconstruct it from README prose.

## Revision Route

When a source hash changes, mark derived artifacts stale, identify the impacted set, and re-run only affected owners. Contract changes route to the canonical owner through a deterministic request payload. Cross-skill retries have a bounded attempt count and escalate unresolved conflicts.

## Side Effects

File generation is idempotent for equal registry input. External side effects require explicit user authority and idempotency keys; resume never repeats an already evidenced effect.
