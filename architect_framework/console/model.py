"""Current registered-artifact navigation and document graph model. No workspace-plan reader or authority."""
from __future__ import annotations
from collections.abc import Iterable
import posixpath
import re
from typing import Any
import unicodedata


_RETIRED_TOKENS = {
    "consumesApi": "calls API of",
    "providesApi": "provides API to",
    "api_contract": "API contract",
    "required_seam": "required obligation",
}

_BAND_META = {
    "00-plan": ("b00", "00 · Planning & Coverage Ledgers"),
    "00-system-views": ("b00", "00 · System Views"),
    "01-global-strategy": ("b01", "01 · Global Strategy"),
    "02-domains": ("b02", "02 · Domains & Bounded Contexts"),
    "03-cross-cutting": ("b03", "03 · Cross-Cutting"),
    "04-delivery": ("b04", "04 · Delivery & Verification"),
    "requirements": ("b01", "Requirements & Strategy"),
}

_DERIVED_NAMES = frozenset({
    "index.md",
    "00-index.md",
    "00-scenario-index.md",
    "00-runtime-scenario-index.md",
    "use-case-matrix.md",
    "use-case-map.md",
    "container-module-mapping.md",
    "c3-component-and-module-map.md",
    "viewpoint-catalogue.md",
    "atomic-requirements-register.md",
    "traceability-matrix.md",
    "requirements-traceability-matrix.md",
    "urd-coverage-ledger.md",
    "domains-index.md",
})

_SEAM_SEGMENTS = re.compile(r"^(?:1[1-9]|2[0-9])-[a-z0-9-]+$")


def clean_display_label(value: str) -> str:
    text = str(value or "")
    for token, replacement in _RETIRED_TOKENS.items():
        text = text.replace(token, replacement)
    text = re.sub(r"^(\d{2})_([a-z0-9_]+)$", lambda m: f"{m.group(1)} · {m.group(2).replace('_', ' ')}", text)
    text = text.replace("_application_", " application ")
    return text


def fold(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c)).replace('đ','d')


def infer_v3_slot_metadata(path: str, kind: str = "") -> dict[str, Any]:
    """Classify a document path across both compact core workspaces and Full Maximal V3 trees."""
    raw_parts = [p for p in str(path or "").strip("/").split("/") if p]
    parts = list(raw_parts)
    if parts and parts[0] == "documents":
        parts = parts[1:]
    if parts and parts[0] == "architecture":
        parts = parts[1:]

    band_key = "root"
    if parts:
        first = parts[0]
        if first in _BAND_META:
            band_key = first
        elif first.startswith("00-"):
            band_key = "00-system-views"
        elif first.startswith("01-") or first == "requirements":
            band_key = "01-global-strategy"
        elif first.startswith("02-") or first == "domains":
            band_key = "02-domains"
        elif first.startswith("03-"):
            band_key = "03-cross-cutting"
        elif first.startswith("04-"):
            band_key = "04-delivery"

    band_color, band_label = _BAND_META.get(band_key, ("accent", "Workspace Root"))
    domain_family = ""
    bounded_context = ""
    architect_skill = ""
    if band_key == "02-domains" and len(parts) >= 2:
        domain_family = clean_display_label(parts[1])
        if len(parts) >= 3 and not parts[1].startswith(("00-", "_")):
            bounded_context = parts[2]
        elif len(parts) >= 2 and not parts[1].startswith(("00-", "_")) and not parts[1].endswith("_architecture"):
            bounded_context = parts[1]
        for seg in parts[2:]:
            if seg.endswith("-architect") or seg.endswith("-architecture"):
                architect_skill = clean_display_label(seg)
                break

    basename = raw_parts[-1] if raw_parts else ""
    template_params = re.findall(r"\{([^{}]+)\}", str(path or ""))

    if basename in _DERIVED_NAMES or "generated" in raw_parts:
        slot_code = "D"
        slot_label = "Derived"
    elif any(_SEAM_SEGMENTS.match(seg) for seg in parts) or "02-security" in parts or "00-planning" in parts:
        slot_code = "S"
        slot_label = "Required Obligation"
    elif (
        any(
            seg in {
                "activities",
                "processes",
                "classes",
                "components",
                "environments",
                "05-information",
                "sequences",
                "style-assessments",
                "change-requests",
                "gap-register",
                "reviews",
                "routing",
                "_shared-adapters",
                "_shared-contracts",
                "_shared-kernel",
                "01-mechanisms",
                "03-infrastructure",
                "04-fitness-functions",
                "05-exceptions",
                "05-reference-library",
                "06-reference-library",
                "04-audit",
                "tickets",
                "02-release",
                "03-ops",
            }
            for seg in parts
        )
        or basename.startswith(("SCN-", "UC-", "CR-", "FIT-", "TKT-"))
        or basename in {"uml-overview.md", "cost-model.md", "technical-debt.md", "composition-root.md"}
    ):
        slot_code = "C"
        slot_label = "Conditional"
    else:
        slot_code = "M"
        slot_label = "Mandatory"

    return {
        "band": band_key,
        "band_color": band_color,
        "band_label": band_label,
        "domain_family": domain_family,
        "bounded_context": bounded_context,
        "architect_skill": architect_skill,
        "slot_code": slot_code,
        "slot_label": slot_label,
        "is_parametric": bool(template_params),
        "template_params": template_params,
    }


def document_tree(artifacts):
    return tree_of([{'rel':row['path']} for row in artifacts])


def tree_of(docs: Iterable[dict], prefix: str = "") -> dict[str, Any]:
    """specification: the folders under a node, single-child chains collapsed, full path kept.

    A folder with exactly one subfolder and no page merges into that subfolder:
    the label joins the names, `path` stays the deepest one, and `segments` keeps
    every name so a deep link still spells the whole path (decision 2 of the plan).
    """
    root: dict[str, Any] = {"name": prefix or "/", "path": prefix, "segments": [], "dirs": {}, "files": []}
    for d in docs:
        rel = d["rel"]
        sub = rel[len(prefix):].lstrip("/") if prefix and rel.startswith(prefix) else rel
        parts = sub.split("/")
        cur = root
        walked = prefix
        for part in parts[:-1]:
            walked = f"{walked}/{part}" if walked else part
            cur = cur["dirs"].setdefault(part, {"name": part, "path": walked, "segments": [part],
                                                "dirs": {}, "files": []})
        cur["files"].append(rel)
    return _finish(root)


def _finish(node: dict[str, Any]) -> dict[str, Any]:
    dirs = [_finish(d) for _, d in sorted(node["dirs"].items())]
    while len(dirs) == 1 and not node["files"]:
        only = dirs[0]
        name = f"{node['name']} / {only['name']}" if node["segments"] else only["name"]
        node = {**node, "name": name, "path": only["path"],
                "segments": node["segments"] + only["segments"], "files": only["files"]}
        dirs = only["dirs_list"]
    deep = len(node["files"]) + sum(d["deep"] for d in dirs)
    return {"name": node["name"], "path": node["path"], "segments": node["segments"],
            "files": sorted(node["files"]), "dirs_list": dirs, "deep": deep}


def single_child_chains(tree: dict[str, Any]) -> int:
    """How many folders still hold one folder and no page — 0 after specification."""
    own = 1 if (len(tree["dirs_list"]) == 1 and not tree["files"]) else 0
    return own + sum(single_child_chains(d) for d in tree["dirs_list"])



def _extract_h1_title(text: str, fallback_path: str) -> str:
    from architect_framework.console import markdown as md
    _, body = md.split_frontmatter(text or "")
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# ") and len(s) > 2:
            return s[2:].strip()
    base = posixpath.basename(fallback_path or "spec.md")
    stem = base[:-3] if base.endswith(".md") else base
    return clean_display_label(stem.replace("-", " ").replace("_", " ").title())

def document_graph(snapshot: Any, before: Any = None, *, graph: Any = None) -> dict[str, Any]:
    """Build deterministic artifact, clause, and obligation graph metadata without including document bodies."""
    from sdd_core.graph import build_graph

    graph = graph or build_graph(snapshot)
    clause_to_artifact: dict[str, str] = {}
    clause_nodes: list[dict[str, Any]] = []
    for artifact in sorted(snapshot.artifacts.values(), key=lambda a: a.path):
        for clause_id, clause_meta in sorted(artifact.clauses.items()):
            clause_to_artifact[clause_id] = artifact.id
            clause_nodes.append({
                "id": clause_id,
                "node_type": "clause",
                "artifact_id": artifact.id,
                "path": artifact.path,
                "anchor": str(clause_meta.get("anchor", "") if isinstance(clause_meta, dict) else ""),
                "owner": clean_display_label(artifact.owner),
                "kind": "clause",
                "upstream": sorted(graph.upstream({clause_id}) - {clause_id}),
                "downstream": sorted(graph.downstream({clause_id}) - {clause_id}),
            })

    raw_edges = [
        {"from": consumer, "to": source, "relation": clean_display_label(relation)}
        for consumer, source, relation in sorted(graph.edges)
    ]

    # Roll up edges to artifact-to-artifact connections while preserving clause intermediaries.
    rolled_map: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in raw_edges:
        src_node = edge["from"]
        dst_node = edge["to"]
        rel = edge["relation"]
        from_art = src_node if src_node in snapshot.artifacts else clause_to_artifact.get(src_node)
        to_art = dst_node if dst_node in snapshot.artifacts else clause_to_artifact.get(dst_node)
        if not from_art or not to_art or from_art == to_art:
            continue
        key = (from_art, to_art)
        entry = rolled_map.setdefault(key, {
            "from": from_art,
            "to": to_art,
            "relations": [],
            "via_clauses": [],
        })
        if rel not in entry["relations"]:
            entry["relations"].append(rel)
        if src_node in clause_to_artifact and src_node not in entry["via_clauses"]:
            entry["via_clauses"].append(src_node)
        if dst_node in clause_to_artifact and dst_node not in entry["via_clauses"]:
            entry["via_clauses"].append(dst_node)

    artifact_edges = sorted(
        (
            {
                **item,
                "relations": sorted(item["relations"]),
                "via_clauses": sorted(item["via_clauses"]),
                "primary_relation": sorted(item["relations"])[0] if item["relations"] else "references",
            }
            for item in rolled_map.values()
        ),
        key=lambda e: (e["from"], e["to"]),
    )

    # Compute topological rank (layer) for each artifact node (0 = authority/root, higher = downstream consumer)
    ranks: dict[str, int] = {a.id: 0 for a in snapshot.artifacts.values()}
    for _ in range(len(ranks) + 1):
        changed_rank = False
        for edge in artifact_edges:
            consumer, authority = edge["from"], edge["to"]
            if authority in ranks and consumer in ranks:
                candidate_rank = ranks[authority] + 1
                if candidate_rank > ranks[consumer] and candidate_rank <= len(ranks):
                    ranks[consumer] = candidate_rank
                    changed_rank = True
        if not changed_rank:
            break

    nodes: list[dict[str, Any]] = []
    clusters_map: dict[str, dict[str, Any]] = {}
    bands_map: dict[str, dict[str, Any]] = {}
    slot_counts = {"M": 0, "C": 0, "D": 0, "S": 0}

    for artifact in sorted(snapshot.artifacts.values(), key=lambda a: a.path):
        folder = posixpath.dirname(artifact.path) or "root"
        raw_parts = [p for p in artifact.path.split("/") if p]
        rel_parts = list(raw_parts)
        if rel_parts and rel_parts[0] == "documents":
            rel_parts = rel_parts[1:]
        if rel_parts and rel_parts[0] == "architecture":
            rel_parts = rel_parts[1:]
        top_group = clean_display_label(rel_parts[0]) if len(rel_parts) > 1 else "root"
        v3_meta = infer_v3_slot_metadata(artifact.path, artifact.kind)
        slot_counts[v3_meta["slot_code"]] = slot_counts.get(v3_meta["slot_code"], 0) + 1
        changed = bool(before and before.files.get(artifact.path) != snapshot.files.get(artifact.path))
        up_all = sorted(graph.upstream({artifact.id}) - {artifact.id})
        down_all = sorted(graph.downstream({artifact.id}) - {artifact.id})
        up_artifacts = sorted({ (u if u in snapshot.artifacts else clause_to_artifact.get(u, "")) for u in up_all } - {"", artifact.id})
        down_artifacts = sorted({ (d if d in snapshot.artifacts else clause_to_artifact.get(d, "")) for d in down_all } - {"", artifact.id})
        in_deg = sum(1 for e in artifact_edges if e["to"] == artifact.id)
        out_deg = sum(1 for e in artifact_edges if e["from"] == artifact.id)
        h1_title = _extract_h1_title(getattr(artifact, "text", ""), artifact.path)
        node_info = {
            "id": artifact.id,
            "node_type": "artifact",
            "path": artifact.path,
            "label": posixpath.basename(artifact.path),
            "title": h1_title,
            "display_title": h1_title,
            "kind": clean_display_label(artifact.kind),
            "owner": clean_display_label(artifact.owner),
            "revision": artifact.revision,
            "folder": clean_display_label(folder),
            "group": top_group,
            "band": v3_meta["band"],
            "band_color": v3_meta["band_color"],
            "band_label": v3_meta["band_label"],
            "domain_family": v3_meta["domain_family"],
            "bounded_context": v3_meta["bounded_context"],
            "architect_skill": v3_meta["architect_skill"],
            "slot_code": v3_meta["slot_code"],
            "slot_label": v3_meta["slot_label"],
            "is_parametric": v3_meta["is_parametric"],
            "template_params": v3_meta["template_params"],
            "rank": ranks.get(artifact.id, 0),
            "clauses": [
                {"id": cid, "anchor": str(cmeta.get("anchor", "") if isinstance(cmeta, dict) else "")}
                for cid, cmeta in sorted(artifact.clauses.items())
            ],
            "anchors": sorted(artifact.anchors),
            "changed": changed,
            "upstream": up_all,
            "downstream": down_all,
            "upstream_artifacts": up_artifacts,
            "downstream_artifacts": down_artifacts,
            "in_degree": in_deg,
            "out_degree": out_deg,
        }
        nodes.append(node_info)
        cluster = clusters_map.setdefault(top_group, {
            "id": top_group,
            "label": "Workspace Root" if top_group == "root" else top_group,
            "node_ids": [],
            "changed_count": 0,
        })
        cluster["node_ids"].append(artifact.id)
        if changed:
            cluster["changed_count"] += 1

        band_entry = bands_map.setdefault(v3_meta["band"], {
            "id": v3_meta["band"],
            "label": v3_meta["band_label"],
            "color": v3_meta["band_color"],
            "node_ids": [],
            "changed_count": 0,
        })
        band_entry["node_ids"].append(artifact.id)
        if changed:
            band_entry["changed_count"] += 1

    obligations: list[dict[str, Any]] = []
    for obl in snapshot.config.get("obligations", []):
        if not obl.get("active", True):
            continue
        src = obl.get("source", "")
        src_art = src if src in snapshot.artifacts else clause_to_artifact.get(src, src)
        obligations.append({
            "id": obl.get("id", ""),
            "source": src,
            "source_artifact": src_art,
            "consumers": list(obl.get("consumers", [])),
            "owner": clean_display_label(obl.get("owner", "")),
            "criticality": obl.get("criticality", "standard"),
            "checks_count": len(obl.get("checks", [])),
        })

    return {
        "nodes": nodes,
        "clause_nodes": clause_nodes,
        "edges": raw_edges,
        "artifact_edges": artifact_edges,
        "obligations": obligations,
        "clusters": list(clusters_map.values()),
        "bands": list(bands_map.values()),
        "stats": {
            "artifacts": len(nodes),
            "clauses": len(clause_nodes),
            "edges": len(raw_edges),
            "artifact_edges": len(artifact_edges),
            "obligations": len(obligations),
            "changed": sum(1 for n in nodes if n["changed"]),
            "slot_counts": slot_counts,
            "kinds": sorted({n["kind"] for n in nodes}),
            "owners": sorted({n["owner"] for n in nodes}),
            "relations": sorted({e["relation"] for e in raw_edges}),
        },
    }
