# Template Standard (Markdown Formatting Specification)

This specification defines the strict layout, section formatting, and quality guidelines for all Markdown template files (.md) and generated document instances.

---

## 1. Unified Page Structure (Coherent Layout)

Every generated Markdown document must adhere to the following 9-part vertical hierarchy:

```
┌────────────────────────────────────────────────────────┐
│ # 1. Document Title [Stable-ID]                        │
├────────────────────────────────────────────────────────┤
│ Backlink Line (e.g. [← Table of Contents](../index.md)) │
├────────────────────────────────────────────────────────┤
│ ## Table of Contents (Anchor list of sections)         │
├────────────────────────────────────────────────────────┤
│ ## Summary (Scope, responsibility, business context)   │
├────────────────────────────────────────────────────────┤
│ ## Diagram (Styled Mermaid block - sequence/flow/ERD)  │
├────────────────────────────────────────────────────────┤
│ ## Detailed Tables (Contracts, attributes, payload)   │
├────────────────────────────────────────────────────────┤
│ ## Assumptions & Open Questions (Fact tracking)        │
├────────────────────────────────────────────────────────┤
│ ## Self-Check (Compliance verification table)          │
├────────────────────────────────────────────────────────┤
│ ## Related Docs (Relative markdown file hyperlinks)    │
└────────────────────────────────────────────────────────┘
```

### Formatting Detail of Sections:
1. **Title & stable ID:** Use exactly one H1 header (`#`). If it is a catalog-level or instance page, include the stable ID (e.g., `# API-001 - GET /orders/{id}`).
2. **Backlink:** Must reside directly below the H1 title. Use the format `[← text](path.md)`.
3. **Table of Contents:** Must use `## Table of Contents` (or translated header) with relative anchors (e.g., `- [Summary](#summary)`).
4. **Summary:** A 2-3 sentence overview describing the role of the component/API.
5. **Diagram:** Optional. Must be wrapped in a code fence containing Mermaid code.
6. **Detailed Tables:** No raw HTML tables. Use standard Markdown syntax (`| Header |`).
7. **Assumptions & Open Questions:** List any assumptions made using `ASSUMPTION: [detail]` and unresolved questions.
8. **Self-Check:** A checklist verification table confirming validation criteria are met.
9. **See Also (Interlinking):** A "See Also" matrix linking to related concepts via stable IDs.
10. **Related Docs:** Relative links to other files. Do not use backticks around filenames in links.

---

## 2. Authoring Standards & Quality Control

* **Alert Blocks:** Use standardized GitHub-style alert blocks (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!CAUTION]`, `> [!WARNING]`).
* **No Smart Quotes:** Strictly ban typographic/smart quotes (use standard straight quotes `"` and `'`).
* **HTML Entities:** Encode raw angle brackets as HTML entities (`&lt;placeholder&gt;`) outside code blocks.
* **Localization Safety (`no-loc`):** Terms that must not be translated (brand names, API identifiers) must be marked. Canonical syntax is placing `no_loc_terms: [term1, term2]` in the YAML front-matter, and using inline code spans (`term`) for identifiers in text.
* **Submodule Tagging:** Any cross-cutting document that mentions a submodule in prose must include the machine metadata `submodules: [<CODE>]` in its YAML front-matter.
* **No Placeholders:** Never output raw brackets like `[Insert text here]` or `TODO`. Use `unspecified` if information is missing, or list the exact question in the Open Questions section.
* **No Code in Text Links:** Never wrap the file name in backticks inside a link's text; write the link text as plain text so IDE link navigation is not broken.
* **Prose Language:** Match the language requested by the user. If unspecified, match the language of their prompt. Keep IDs, class names, path names, and filenames in ASCII.

---

## 3. Table Column Standards

To ensure clarity and coherence across all generated tables:

### A. API Endpoints Table Layout
| Field | Type | Description | Required | Validation Rule |
|---|---|---|---|---|
| `order_id` | UUID | Unique identifier of the order | Yes | Must be a valid UUIDv4 |

### B. Event Message Table Layout
| Property | Type | Description | Sample Value |
|---|---|---|---|
| `event_time` | Timestamp | ISO 8601 creation time | `2026-07-11T23:20:00Z` |

---

## 4. Unified Document Skeletons

To enforce structural consistency across the SDD lifecycle, all generated core deliverables must strictly follow these structural skeletons:

### A. EARS Specification (`clarified-requirements.md` / `requirements.md`)
```markdown
# Requirements Specification [REQ-001]
[← Table of Contents](index.md)

## Table of Contents
- [Summary](#summary)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)

## Summary
Core functional requirements defined under EARS (Easy Approach to Requirements Syntax) formatting.

## Functional Requirements
| ID | Syntax Pattern | Requirement Text | Priority | Covers |
|---|---|---|---|---|
| REQ-001 | **WHEN** [Trigger] **WHERE** [State] **THE** [System] **SHALL** [Action] | When an order is placed, the system shall emit an OrderCreated event. | Must | CLR-001 |

## Non-Functional Requirements
- **NFR-001 (Latency):** The system shall process API requests with a p95 response time ≤ 200ms under a load of 1000 RPS.
```

### B. API Spec (`apis/<api-slug>.md`)
```markdown
# GET /orders/{id} [API-001]
[← Table of Contents](../index.md)

## Summary
Retrieve Order details by UUID.

## Request Specification
- **Path Parameter:** `id` (UUIDv4, Required)
- **Headers:** `Authorization: Bearer <token>`

## Response Specification (200 OK)
| Field | Type | Description | Required | Validation Rule |
|---|---|---|---|---|
| `order_id` | UUID | Unique order identifier | Yes | Valid UUIDv4 |
| `status` | String | Current lifecycle status | Yes | One of: pending, shipped, done |
```

### C. Change Request (`architecture/01-global-strategy/05-governance/change-requests/CR-{NNN}-{slug}.md`)
```markdown
# Change Request [CR-001]

## Summary
Add customer notes field to order requests.

## Impact Map
- **Touched Specs:** [API-002](apis/post-orders.md), [requirements.md](requirements.md)

## Downstream Regeneration Checklist
| Step | Action Item | Target File | Responsible Skill | Status |
|---|---|---|---|---|
| 1 | Update API post orders schema | [API-002](apis/post-orders.md) | `system-architect` | complete |
| 2 | Regenerate the derived order-flow diagram | [sequence-diagram](apis/post-orders.md) | `sequence-diagram` | pending |
```
