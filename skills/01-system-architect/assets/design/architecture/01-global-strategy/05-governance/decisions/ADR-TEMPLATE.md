---
primary_layer: workflow
---
# ADR NNNN — {{DECISION_TITLE}}

[← Table of Contents]({{INDEX_PATH}}) · *Architecture / Decisions*

## Table of Contents

- [Status](#status)
- [Context & Problem Statement](#context--problem-statement)
- [Research Insights](#research-insights)
- [Solution Hypothesis](#solution-hypothesis)
- [Options Considered](#options-considered)
- [Decision](#decision)
- [Consequences](#consequences)
- [Enforcement](#enforcement)
- [Related Docs](#related-docs)
- [Change Log](#change-log)

## Status

| Field | Value |
|---|---|
| Status | `PROPOSED` \| `ACCEPTED` \| `SUPERSEDED-BY-NNNN` \| `DEPRECATED` |
| Decision date | `YYYY-MM-DD` |
| Decision owner | {{DECISION_OWNER}} |
| Supersedes | ADR-NNNN (if any) |
| Superseded by | ADR-NNNN (if any) |
| Bounded contexts affected | {{AFFECTED_CONTEXTS}} |

An `ACCEPTED` ADR is **immutable**. To change a decision, author a new ADR whose `Supersedes` field points at this one, and set this ADR's status to `SUPERSEDED-BY-NNNN`. Never rewrite the body of an accepted ADR.

## Context & Problem Statement

State the forces that made this decision necessary:

- Business / product constraint that surfaced the problem.
- Technical constraint the system now hits (scale, safety, licence, timeline).
- Why deferring is worse than deciding now.

Keep this section factual — no advocacy. Advocacy belongs in **Options Considered** and **Decision**.

## Research Insights

State what was investigated to solve this problem:

- Internal capability assessment (what tools/libraries we already use).
- Environment assessment (cloud limits, security constraints).
- *Why this specific domain/tech fits our team's current trajectory.*

## Solution Hypothesis

State the expected outcome or benefit of resolving this problem:

- The hypothesis of how the system will improve.
- The measurable benefit we expect to gain.

## Options Considered

Enumerate every option that survived initial triage. Each option gets its own table row.

| # | Option (What) | Why | Benefit | Downside | Cost / Effort | Risk | Reversibility |
|---|---|---|---|---|---|---|---|
| A | {{OPTION_A}} | {{WHY_A}} | {{BENEFIT_A}} | {{DOWNSIDE_A}} | {{COST_A}} | {{RISK_A}} | {{REVERSIBILITY_A}} |
| B | {{OPTION_B}} | {{WHY_B}} | {{BENEFIT_B}} | {{DOWNSIDE_B}} | {{COST_B}} | {{RISK_B}} | {{REVERSIBILITY_B}} |
| C | {{OPTION_C}} | {{WHY_C}} | {{BENEFIT_C}} | {{DOWNSIDE_C}} | {{COST_C}} | {{RISK_C}} | {{REVERSIBILITY_C}} |

For each option include a paragraph of "**Why not**" text listing the specific reasons the option was rejected. If you cannot write "Why not" for the chosen option, the analysis is incomplete.

## Decision

State the chosen option in **one sentence**. Then list the concrete reasons — not a re-statement of the option, but the causal chain from *option* → *system property we gain*.

> Chosen: **Option {{CHOSEN_LETTER}} — {{CHOSEN_TITLE}}**.

Reasons:

1. {{REASON_1}}
2. {{REASON_2}}
3. {{REASON_3}}

## Consequences

Positive and negative in the same list; do not hide the negatives.

| Consequence | Kind | Mitigation |
|---|---|---|
| {{CONSEQUENCE_1}} | positive | — |
| {{CONSEQUENCE_2}} | negative | {{MITIGATION_2}} |
| {{CONSEQUENCE_3}} | trade-off | {{MITIGATION_3}} |

## Enforcement

How the decision is prevented from silent regression:

- **Architecture-fitness test** — {{FITNESS_TEST_RULE}} in [Fitness Functions catalog](../../../03-cross-cutting/04-fitness-functions/00-overview.md).
- **Code-review checklist item** — {{REVIEW_ITEM}}.
- **CI gate** — {{CI_GATE}}.

An ADR without an enforcement mechanism is aspirational, not architectural.

## Related Docs

- {{RELATED_MECHANISM_PAGES}}
- {{RELATED_ADRS}}
- {{RELATED_REQUIREMENTS}}

## Change Log

| Date | Change | Author |
|---|---|---|
| `YYYY-MM-DD` | Proposed | {{AUTHOR}} |
| `YYYY-MM-DD` | Accepted | {{AUTHOR}} |
