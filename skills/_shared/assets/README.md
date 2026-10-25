# Assets

Three starting shapes, because the catalog produces three kinds of artifact and one generic skeleton served none of them well:

| Template | Use for |
|---|---|
| `output-template-domain.md` | a domain skill's `00-overview/<skill>-overview.md` — the architecture decision and its invariants |
| `output-template-fitness.md` | a domain skill's `verification/fitness-self-check.md` — what was probed and what it showed |
| `output-template-task.md` | a task skill's registry deliverable — the named artifact, usually a comparison |

All three carry the four sections `check_output_docs.py` requires (`Summary`, `Detailed Description`, `Traceability`, `Verification`); what differs is the middle, which is where the artifacts actually differ.

The remaining `output-template-*.md` files are the per-page-class B-templates. Each skill's `references/output-contract.md` names one per page class in its `## Output Modules` section, so a concern module never has to invent a shape.

A template is a starting shape, not evidence. Replace every placeholder with sourced content or an explicit unknown before validation — the validator rejects any `{{...}}` left behind.
