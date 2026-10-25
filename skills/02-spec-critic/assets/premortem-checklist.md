# Pre-Mortem Checklist

Prompts for the pre-mortem pass. Frame: **"It is 6 months after launch and the project has failed. Why?"** Work each category; keep only causes that have a spec-level remedy, and convert those into RISK-xxx findings.

## 1. Load & Scale

- The main flow collapsed at real traffic — which NFR number was fiction, or never specified?
- One table/queue grew unbounded — where is retention/archival specified?
- A hot spot (single lock, single partition, single instance) serialized everything — is it visible in architecture.md?

## 2. External Dependencies

- A third-party API changed or died — which integration has no versioning or degradation behavior specified?
- Payment/email/auth provider had an outage during peak — what does the user see, per spec?
- A dependency's rate limit was hit — is backoff behavior specified anywhere?

## 3. Data & Consistency

- Two services disagreed about the same fact — where is the source of ownership declared for each entity?
- A migration corrupted or stranded data — is rollback/backfill behavior specified?
- Duplicate events / retries created double effects — which flows are specified as idempotent?

## 4. Security & Compliance

- A data leak came from the least-reviewed surface — which endpoint carries PII with no access rule in the spec?
- An internal admin tool was the breach vector — is admin auth specified to the same standard?
- A compliance audit failed — which regime (PII/PCI/...) is named in requirements but never mapped to controls?

## 5. People & Process

- The one person who understood module X left — which component has no spec beyond its name?
- Implementers interpreted a vague spec two different ways — which requirement wording allows both readings?
- Scope creep buried the MVP — are Won't-have items explicitly recorded?

## Conversion Rules

| Pre-mortem outcome | Action |
|---|---|
| Plausible cause + spec-level remedy exists | Convert to RISK-xxx with suggested direction |
| Plausible cause, remedy is operational (not spec) | Record in Pre-Mortem Notes as `dismissed: operational` |
| Implausible for this system's scale | Record as `dismissed: out of profile` — do not pad findings |
