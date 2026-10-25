---
document_role: glossary
status: implementation-candidate
updated_at: 2026-10-14
---

# Current core concepts

The release candidate is NOT_QUALIFIED. These terms describe its current boundaries.

| Term | Meaning |
|---|---|
| Artifact | A registered document with a stable ID, path, kind, owner, and exact revision |
| Clause | A stable statement identity inside a source document; order does not define identity |
| Obligation | A source requirement and its declared consumers, checks, owner, criticality, and review rubric |
| Snapshot | A digest of captured source and configuration |
| Candidate | An isolated proposed revision; it grants no acceptance |
| Accepted baseline | A historical snapshot with a valid acceptance certificate |
| Skill grant | The accepted capability and write scope for a skill |
| Task plan | A bounded dependency graph with outputs, scopes, gates, and attempt limits |
| Attempt lease | A private token that binds one worker result to a current task attempt |
| Dispatch gate | A human decision for one exact attempt scope and its current questions |
| Independent review | Evidence-based review of the exact source and consumer revisions |
| Document acceptance | A separate signed human decision before publication |
| Observation | Task state and redacted events; host tool usage and cost remain unknown |
| Frozen labels | Immutable source cases and proposed labels for independent human review |
| Qualification | Separate evidence for a pinned model, workload, corpus, and implementation |

Routing selects a skill. It does not authorize writes. A candidate can change proposed grants,
but those grants become authority only through accepted policy.

A deterministic PASS means that declared mechanical checks passed. It does not prove meaning,
complete review, human acceptance, or model quality. A skip means NOT_APPLICABLE. It is not PASS.

A global deadline fences new dispatch, signatures, heartbeats, and result commits.
A checked prefix remains available. The host worker can continue outside the scheduler;
its stopped state and cost remain unknown until separate evidence is available.

The writing profile aims for short technical English. Protected facts include IDs, values,
units, normative words, negation, code, links, and UNKNOWN. The partial checker does not
certify ASD-STE100 or 80% full-profile compliance.

See [the task guide](GUIDE-CORE-RUNS.md), [CLI reference](REFERENCE-CLI.md), and
[troubleshooting](TROUBLESHOOTING.md) for current actions.
