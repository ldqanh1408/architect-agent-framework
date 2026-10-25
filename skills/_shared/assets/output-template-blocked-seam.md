---
generated: true
primary_layer: content
skill: {{SKILL_ID}}
seam_id: {{SEAM_ID}}
source_hashes: []
---

# {{SEAM_ID}} — Blocked seam: {{NODE}}

The page at `{{NODE}}` cannot be authored yet. It is a sealed gap, not an absent
one: the seam ledger records the missing evidence, the clause that would supply
it, and the owner who owes it. Rendering this page did not close
the seam — only the evidence that named token actually appeared in the evidence
ledger can do that. Authored content replacing this banner on a later run is
kept; the banner is regenerated if it is ever removed by hand while the ledger
row is still open.

## Summary

`{{NODE}}` is an `unmet-obligation` seam (`{{OBLIGATION}}`). The owning skill is
`{{OWNER}}`; approval rests with `{{APPROVER}}`. The page was planned but its
`when:` condition did not hold because `{{MISSING_EVIDENCE}}` evidence was not
routed to this module. The seam is checked by `{{GATE}}`. Its stable id in the
ledger is `{{SEAM_ID}}`, and it remains `open` until the missing evidence fires.

## Detailed Description

The gap is defined by the ledger entry, not by prose: `missing_evidence =
{{MISSING_EVIDENCE}}`, `would_be_supplied_by = {{SUPPLIED_BY}}`. Writing content
here asserts a page exists; it does not make the underlying claim true. Until
the requirement or the evidence ledger supplies the missing token, this page's
contents would be guessed, and a guessed architecture is the failure the seam
ledger exists to prevent. The owning skill should author this page only when the
evidence that supplies the gap has actually appeared and the ledger row flips to
`closed`.

### Interface

| Operation | Direction | Inbound type | Outbound type | Error contract |
|---|---|---|---|---|
| (blocked) | (blocked) | (blocked) | (blocked) | the seam is open; author after evidence |

### Fields / Payload

| Field | Type | Required | Invariant |
|---|---|---|---|
| seam | `{{SEAM_ID}}` | yes | resolves in `sdd-workspace.yml` |
| state | open / closed | yes | computed from the evidence ledger |

## Contracts and Invariants

State the invariants the seam holds, each numbered so the rest of the system can
be checked against it. A blocked seam is honest about what it is: the page is a
placeholder until the evidence appears.

    SEAM-{{SEAM_NUM}} [{{SEAM_ID}}-1]
      the page stays rendered until evidence supplies {{MISSING_EVIDENCE}}; the
      ledger state, not this page's presence, decides whether the seam is open.

## Ownership and Handoffs

| Concern | Owner | Handoff payload | Blocked until |
|---|---|---|---|
| author this page | `{{OWNER}}` | evidence for {{MISSING_EVIDENCE}} | ledger flips to `closed` |
| approve | `{{APPROVER}}` | authored, evidence-backed page | evidence appears |

## Traceability

| Claim | Classification | Source | Freshness |
|---|---|---|---|
| `{{NODE}}` is an open seam | derived | `sdd-workspace.yml` | ledger digest current |
| evidence missing | observed | `{{GATE}}` | current plan digest |

## Verification

The seam is verified by running the ledger gate and confirming its state:

    architect-cli gate run {{GATE}} <workspace> --check
    architect-cli seam explain <workspace> {{SEAM_ID}}

This page passes `check_output_docs.py --strict` as a legal page class because
it carries a `SEAM-` stable id, the executable spine headings, provenance, and a
verification oracle. The bonus contract within the template is rendered from the
ledger entry, never composed by hand: deleting this banner and writing content
regenerates it until the ledger row is closed.
