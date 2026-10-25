---
primary_layer: content
---
# Runtime View

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Runtime*

## Purpose

arc42 §6. The scenarios where a quality goal stops being an adjective: a flow
described step by step across the building blocks it traverses, with at least one
failure branch.

## Contents

| File | Holds |
|---|---|
| `00-scenario-index.md` | SCN-xxx → the quality scenario it exercises → the contexts it crosses |
| `SCN-NNN-<slug>.md` | one scenario: trigger, participants by stable id, ordered steps with contracts and timing, failure branches |

## The cap is the feature

At most five scenario pages. arc42's guidance is that dozens of scenarios get
*designed* and one to five get *documented* — chosen for architectural relevance,
not coverage. A scenario per use case is a transcript, and the reason to keep the
set small is that a short set gets read.

`V-MAN-7` enforces the cap.

## Exists from

The `standard` level, and then only with evidence: a quality scenario that names
a flow, or two or more contexts cooperating in one user-visible operation.

## Related Docs

- [Quality Attributes](../../01-global-strategy/01-requirements/quality-attributes.md)
- [Viewpoints](../00-viewpoints/README.md)
