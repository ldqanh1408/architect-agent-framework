from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch

from .model import Finding, Snapshot, SddError, Status
from .parsing import resolve_link


@dataclass
class Graph:
    # Edges point from consumer to authority/source.
    edges: set[tuple[str, str, str]] = field(default_factory=set)
    findings: list[Finding] = field(default_factory=list)

    def downstream(self, subjects: set[str]) -> set[str]:
        reached = set(subjects)
        while True:
            extra = {consumer for consumer, source, _ in self.edges if source in reached}
            if extra <= reached:
                return reached
            reached |= extra

    def upstream(self, subjects: set[str]) -> set[str]:
        reached = set(subjects)
        while True:
            extra = {source for consumer, source, _ in self.edges if consumer in reached}
            if extra <= reached:
                return reached
            reached |= extra


def build_graph(snapshot: Snapshot) -> Graph:
    graph = Graph()
    by_path = {a.path: a for a in snapshot.artifacts.values()}
    subjects = set(snapshot.artifacts)
    for artifact in snapshot.artifacts.values():
        subjects.update(artifact.clauses)
        for clause in artifact.clauses:
            graph.edges.add((clause, artifact.id, "references"))
    for artifact in snapshot.artifacts.values():
        for edge in artifact.metadata.get("depends_on", []):
            graph.edges.add((artifact.id, edge["target"], edge["relation"]))
            if edge["target"] not in subjects:
                graph.findings.append(Finding("DANGLING_DEPENDENCY", f"{artifact.id} requires {edge['target']}", (artifact.id, edge["target"])))
        for href in artifact.links:
            try:
                resolved = resolve_link(artifact.path, href)
            except SddError as exc:
                graph.findings.append(Finding(exc.code, str(exc), (artifact.id,)))
                continue
            if resolved is None:
                continue
            path, anchor = resolved
            target = by_path.get(path)
            if path not in snapshot.files:
                graph.findings.append(Finding("BROKEN_LINK", f"{artifact.path}: {href}", (artifact.id,)))
            elif target:
                graph.edges.add((artifact.id, target.id, "references"))
                if anchor and anchor not in target.anchors:
                    graph.findings.append(Finding("BROKEN_ANCHOR", f"{artifact.path}: {href}", (artifact.id, target.id)))
    for obligation in snapshot.config["obligations"]:
        if not obligation.get("active", True):
            continue
        ids = [obligation["source"], *obligation["consumers"]]
        for identifier in ids:
            if identifier not in subjects:
                graph.findings.append(Finding("MISSING_RELATIONSHIP_EVIDENCE", f"{obligation['id']} requires {identifier}",
                                              (identifier,), Status.INCOMPLETE, obligation_id=obligation["id"]))
        for consumer in obligation["consumers"]:
            graph.edges.add((consumer, obligation["source"], "satisfies"))
    # Reference cycles are allowed. Only derived_from must be acyclic.
    visited, visiting, stack = set(), set(), []
    adjacency = {}
    for consumer, source, relation in graph.edges:
        if relation == "derived_from":
            adjacency.setdefault(consumer, []).append(source)

    def visit(node):
        if node in visiting:
            cycle = stack[stack.index(node):] + [node]
            graph.findings.append(Finding("DERIVATION_CYCLE", " -> ".join(cycle), tuple(cycle)))
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for target in sorted(adjacency.get(node, [])):
            visit(target)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)
    return graph


def affected(old: Snapshot | None, new: Snapshot, changed: set[str]) -> set[str]:
    before = build_graph(old) if old else Graph()
    after = build_graph(new)
    return Graph(before.edges | after.edges).downstream(changed)


def full_impact_oracle(old: Snapshot | None, new: Snapshot, changed: set[str]) -> set[str]:
    # Separate traversal/selection, deliberately no incremental state or cache.
    edges = build_graph(new).edges | (build_graph(old).edges if old else set())
    impacted = set(changed)
    candidates = {edge[0] for edge in edges}
    for candidate in candidates:
        queue, seen = [candidate], set()
        while queue:
            node = queue.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in changed:
                impacted.add(candidate)
                break
            queue.extend(b for a, b, _ in edges if a == node)
    return impacted


def expand_legacy_glob(pattern: str, old: Snapshot | None, new: Snapshot) -> set[str]:
    artifacts = list(new.artifacts.values()) + (list(old.artifacts.values()) if old else [])
    return {a.id for a in artifacts if fnmatch.fnmatchcase(a.path, pattern)}
