# Shape-specific review

Read the applicable rows before reviewing those flows. These are investigation questions, not mandatory technologies.

| Shape | Review obligations |
|---|---|
| Bidirectional sync | overlap/cadence, diff granularity, conflict detection, resolution authority, preservation of fields/annotations, delete versus update |
| User auth plus upstream service auth | separate credentials/storage/lifetimes, rotation/revocation, access scope, trust boundary; match storage properties to threat model |
| Webhooks | provider signature contract, replay/deduplication, durable acknowledgement, duplicates and ordering, retry/failure outcomes; UI notification only if needed |
| External agent/CLI edits data | copied workspace, exact write scope, process limits/environment, evidence and review gate, concurrency and rollback |
| File/env configuration | key/type/default/required scope, malformed input, environments, precedence, secret source, version and overrides |
| Money/stock/points/balance | canonical ledger, all mutation paths, concurrent change, reconciliation, compensation and auditability |
| Offline clients | durability across tab/process/device loss, queued ordering, stable idempotency key and retention, re-entry conflicts and user-visible status |
| Critical third-party API | sourced current contract, auth/request/response, deadline, rate limit, malformed/outage handling, safe fallback and quota/cost implications |
