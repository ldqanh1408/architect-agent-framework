---
page_class: viewpoint
---

# Runtime viewpoint

## Concerns

Whether a flow meets its latency and availability targets, and what the system does when one hop in that flow
fails. These need their own view because the structure views answer "what exists", never "what happens, in
what order, and how long it takes".

## Audience

The on-call engineer sizing an incident, and the architect defending a quality goal at review. Both read a
sequence of hops; neither reads a component inventory to answer these questions.

## Notation

UML sequence diagrams for step order, plus prose scenarios carrying the measured numbers. Notation is not the
organising principle — a BPMN drawing answering a runtime concern belongs to this viewpoint too.

## Realising views

`00-system-views/06-runtime/` — the `SCN-{NNN}` pages and the per-scenario sequence diagrams under
`sequences/{scenario}/`.

## Correspondence rules

Every participant named in a runtime scenario must exist as a container in `03-structure/` under the same
stable id. Every neighbour in `01-context/` must appear in at least one runtime scenario, or be recorded as
deliberately unexercised.
