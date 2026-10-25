"""Deterministic, one-way projections. Sources are never reconstructed from output."""
from __future__ import annotations

from copy import deepcopy

from .changes import propose
from .graph import build_graph
from .model import SddError, Status, digest
from .validation import subject_artifact, subject_revision
from .workspace import capture


def projection_input_digest(snapshot, artifact_id):
    """Bind all recipe inputs, including upstream graph and contract metadata."""
    artifact = snapshot.artifacts[artifact_id]
    graph = build_graph(snapshot)
    sources = sorted(e[1] for e in graph.edges if e[0] == artifact_id and e[2] == "derived_from")
    scope = graph.upstream(set(sources)) - {artifact_id}
    return digest({"recipe_version": 1, "projection": artifact.metadata.get("projection"),
                   "sources": sources, "scope": sorted(scope),
                   "revisions": {s: {"subject": subject_revision(snapshot, s),
                                     "artifact": getattr(subject_artifact(snapshot, s), "revision", None)} for s in sorted(scope)},
                   "relationships": [list(e) for e in sorted(graph.edges) if e[0] in scope and e[1] in scope],
                   "obligations": [o for o in snapshot.config["obligations"] if o.get("active", True) and o["source"] in scope]})


def derive(store, root, artifact_id, operation_id=None, skill=None):
    snapshot = capture(root)
    artifact = snapshot.artifacts.get(artifact_id)
    if artifact is None or not artifact.metadata.get("generated"):
        raise SddError("PROJECTION_UNKNOWN", artifact_id)
    graph = build_graph(snapshot)
    sources = sorted(e[1] for e in graph.edges if e[0] == artifact_id and e[2] == "derived_from")
    if not sources or any(subject_revision(snapshot, s) is None for s in sources):
        raise SddError("PROJECTION_SOURCE_MISSING", artifact_id, Status.INCOMPLETE)
    projection = artifact.metadata.get("projection")
    header = f"---\nartifact_id: {artifact_id}\n---\n# Derived {projection}\n\n"
    scope = graph.upstream(set(sources)) - {artifact_id}
    if projection == "dependency-mermaid":
        nodes = {identifier: f"n{index}" for index, identifier in enumerate(sorted(scope))}
        lines = ["```mermaid", "flowchart TD"]
        lines += [f'  {node}["{identifier}"]' for identifier, node in nodes.items()]
        lines += [f"  {nodes[a]} -->|{relation}| {nodes[b]}" for a, b, relation in sorted(graph.edges) if a in nodes and b in nodes]
        content = header + "\n".join(lines) + "\n```\n"
    elif projection == "obligation-index":
        lines = ["| Obligation | Source | Consumers | Owner |", "| --- | --- | --- | --- |"]
        lines += [f'| {o["id"]} | {o["source"]} | {", ".join(o["consumers"])} | {o["owner"].replace("|", " ")} |'
                  for o in snapshot.config["obligations"] if o.get("active", True) and o["source"] in scope]
        content = header + "\n".join(lines) + "\n"
    else:
        raise SddError("PROJECTION_UNSUPPORTED", "Choose dependency-mermaid or obligation-index; custom generators require an adapter", Status.INCOMPLETE)
    metadata = deepcopy(artifact.metadata)
    metadata.update({"source_revisions": {s: subject_revision(snapshot, s) for s in sources},
                     "projection_input_digest": projection_input_digest(snapshot, artifact_id),
                     "output_digest": digest(content.encode("utf-8"))})
    return propose(store, root, [{"action": "update", "artifact_id": artifact_id, "expected_revision": artifact.revision,
                                 "content": content, "metadata": metadata}], operation_id, skill, snapshot.digest)
