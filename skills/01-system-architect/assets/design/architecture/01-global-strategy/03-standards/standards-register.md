---
primary_layer: content
---
# Standards Register

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Standards › Register*

## Table of Contents

- [Summary](#summary)
- [Lifecycle](#lifecycle)
- [Register](#register)
- [Exemptions](#exemptions)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

TOGAF's Standards Library, kept as one table. A standard is anything a new piece
of this system must conform to: a protocol, a library, a coding rule, a
regulatory obligation.

The column that earns this page its keep is **status**. Without it, "we use
gRPC", "we are trialling gRPC" and "gRPC is on its way out" are the same
sentence — and `03-cross-cutting/04-fitness-functions/` has no way to tell which
standards it may enforce as hard gates and which it must not.

## Lifecycle

| Status | Meaning | May a fitness rule enforce it? |
|---|---|---|
| `proposed` | identified, not yet evaluated | no |
| `provisional` | being trialled under named pilot conditions | only inside the pilot's scope |
| `standard` | the approach of choice for new work | yes |
| `phasing-out` | existing use may continue; new use discouraged | enforce the *ban on new use*, not the standard |
| `retired` | no longer valid; remediation planned | no — a rule citing a retired standard is a finding |

Standards move through these stages; a register whose rows are all `standard`
usually means the status column is being filled in reflexively.

## Register

| ID | Standard | Domain | Status | Scope | Owner | Source |
|---|---|---|---|---|---|---|
| STD-001 | {{NAME_AND_VERSION}} | business \| data \| application \| technology | standard | {{which contexts it binds}} | {{ROLE}} | legal \| industry \| organisational |
| STD-002 | {{...}} | {{...}} | provisional | {{pilot scope}} | {{ROLE}} | {{...}} |

Domain follows TOGAF's four architecture domains. `Source` matters because the
three classes behave differently: legal and regulatory obligations are not
negotiable, industry standards sit outside our control and must be watched, and
organisational standards need an exemption process.

## Exemptions

| ID | Standard | Who is exempt | Why | Expires |
|---|---|---|---|---|
| EXM-1 | STD-00x | {{CONTEXT}} | {{REASON}} | {{DATE_OR_TRIGGER}} |

An organisational standard with no exemption path becomes a standard people
route around silently, which is worse than one with a documented exception.

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every FIT rule cites a non-retired STD or no STD at all | VERIFIED-BY-SCRIPT: V-MAN-5 / COR-7 |
| Every `provisional` row names its pilot scope | VERIFIED-BY-SCRIPT: non-empty scope column |
| Every technology named in `technology-selection.md` appears here or is out of scope | VERIFIED-BY-GATE: `architect-runtime sdd check <workspace> --full` |
| The status values are current | UNVERIFIABLE-AT-PHASE-1: standards need periodic review; set the cadence here |

## Related Docs

- [Technology Selection](../02-strategy/technology-selection.md)
- [Fitness Functions](../../03-cross-cutting/04-fitness-functions/00-overview.md)
- [Decisions](../05-governance/decisions/)
