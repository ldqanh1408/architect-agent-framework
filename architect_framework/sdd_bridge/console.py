"""Read packets and verify human decisions against the same core revision."""
from __future__ import annotations

import difflib
import uuid
from pathlib import Path

from . import BridgeError, engine_for, inspect


def model(workspace, change_id=None, *, include_evidence=True):
    from sdd_core.workspace import capture
    from sdd_core.model import digest
    from architect_framework.console import attest
    engine = engine_for(workspace)
    live = capture(Path(workspace))
    baseline = engine.store.baseline()
    base_id = baseline["acceptance_id"] if baseline else None
    candidates = [c for c in engine.store.list("changes") if c.get("base_acceptance") == base_id
                  and c.get("origin_snapshot") == live.digest]
    candidates.sort(key=lambda c: (c.get("created_at", ""), c["change_id"]))
    if change_id is None and candidates:
        change_id = candidates[-1]["change_id"]
    report = inspect(workspace, change_id)
    if change_id:
        change, snapshot, before = engine.context(change_id)
    else:
        snapshot = live
        before = engine.store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
    summary = {"mode": "core", "workspace": snapshot.config["workspace_id"], "change_id": change_id,
               "document_basis": "candidate" if change_id else "live",
               "artifacts": [{"id": a.id, "path": a.path, "kind": a.kind, "owner": a.owner, "revision": a.revision} for a in sorted(snapshot.artifacts.values(), key=lambda a:a.path)],
               "candidates": [{"change_id": c["change_id"], "snapshot_digest": c["snapshot_digest"]} for c in candidates],
               "report": report, "reviewers": [{"name": r.name} for r in attest.load_reviewers(Path(workspace))],
               "decision_authority": snapshot.config["policy"].get("decision_authority", "local")}
    from sdd_core.graph import build_graph
    from architect_framework.console.model import document_graph, document_tree
    shared_graph = build_graph(snapshot)
    summary["document_tree"] = document_tree(summary["artifacts"])
    summary["document_graph"] = document_graph(snapshot, before, graph=shared_graph)
    summary["coverage_metrics"] = report.get("check", {}).get("details", {}).get("coverage_metrics")
    summary["readiness"] = report.get("regression")
    from .language import latest
    summary["language_review"] = latest(engine, change, snapshot) if change_id else None
    from sdd_core.adapters.facade import resolve_provider_config
    resolved_judge = resolve_provider_config(snapshot.config.get("provider"), Path(workspace))
    summary["judge"] = {key: value for key, value in resolved_judge.items() if key in {"type", "model", "max_cost_usd"}}
    from .skill_ui import workspace_ui_adaptation_profile
    summary["skill_adaptation"] = workspace_ui_adaptation_profile(snapshot)
    if not include_evidence:
        return summary | {"surface": "workbench"}
    previous = before.files if before else {}
    from sdd_core.review import make_packet, obligations_for_review
    from sdd_core.freshness import latest_observations
    from sdd_core.model import SddError
    review_packets = []
    obs = latest_observations(engine.store, snapshot)
    for obligation in obligations_for_review(snapshot, before):
        try:
            review_packets.append(make_packet(snapshot, obligation, before, obs, graph=shared_graph))
        except SddError as exc:
            review_packets.append({"obligation_id": obligation["id"], "error": exc.to_dict()})
    diffs = {}
    for path in sorted(set(previous) | set(snapshot.files)):
        old, new = previous.get(path, ""), snapshot.files.get(path, "")
        if old != new:
            diffs[path] = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                      fromfile="accepted/" + path, tofile="candidate/" + path))
    binding = {"snapshot_digest": snapshot.digest, "base_acceptance": base_id,
               "change_id": change_id, "report": report, "diffs": diffs, "review_packets": review_packets,
               "language_review": summary["language_review"]}
    return summary | {"diffs": diffs, "packet_digest": digest(binding), "review_packets": review_packets,
                      "surface": "review"}


def prepare(workspace, body, now):
    from sdd_core.policy import prepare_decision, effective_policy
    change_id = body.get("change_id")
    if not change_id:
        raise BridgeError("CHANGE_REQUIRED", "Select a captured candidate before signing")
    packet = model(workspace, change_id)
    if packet["packet_digest"] != body.get("packet_digest"):
        raise BridgeError("PACKET_CHANGED", "Review the updated packet before signing", "STALE")
    engine = engine_for(workspace)
    change, snapshot, before = engine.context(change_id)
    if effective_policy(snapshot, before).get("decision_authority") != "external":
        raise BridgeError("SIGNED_POLICY_REQUIRED", "This workspace needs an external decision authority policy before console acceptance")
    kind = body.get("kind", "accept")
    payload = {"kind": kind, "actor": body.get("actor", ""), "reason": body.get("reason", ""),
               "scope": body.get("scope") or [snapshot.config["workspace_id"]],
               "snapshot_digest": snapshot.digest, "decision_id": "DEC-" + uuid.uuid4().hex}
    if kind == "accept":
        payload["packet_digest"] = packet["packet_digest"]
    for field in ("expires_at", "evidence", "finding_ids", "packet_digest", "observed_digest", "source_version", "observation_id"):
        # Review packet digest differs from a false-positive finding's engine packet.
        value = (body.get("details") or {}).get(field)
        if value is not None:
            payload[field] = value
    if kind == "accept":
        blockers = [f for f in packet["report"]["regression"]["findings"]
                    if f["severity"] == "blocker" and f["code"] != "HUMAN_ACCEPTANCE_REQUIRED"]
        if blockers:
            raise BridgeError("ACCEPTANCE_BLOCKED", "Resolve the displayed review/regression findings before acceptance", "INCOMPLETE")
    record = prepare_decision(engine.store, snapshot, payload, before, now, change["base_acceptance"])
    return {"record": record, "payload": payload, "created_at": now, "change_id": change_id,
            "packet_digest": packet["packet_digest"]}


def commit(workspace, draft, attestation):
    from sdd_core.policy import record_decision
    if model(workspace, draft["change_id"])["packet_digest"] != draft["packet_digest"]:
        raise BridgeError("PACKET_CHANGED", "The candidate or review changed; inspect and sign again", "STALE")
    engine = engine_for(workspace)
    change, snapshot, before = engine.context(draft["change_id"])
    record = record_decision(engine.store, snapshot, {**draft["payload"], "attestation": attestation},
                             before, draft["created_at"], change["base_acceptance"])
    if record["kind"] == "accept":
        from .publication import prepare, publish
        journal = prepare(engine, change, record)
        accepted = engine.accept(change["change_id"], snapshot.digest, "console-" + record["decision_id"])
        publication = publish(workspace, journal["publication_id"])
        return {**accepted, "publication": publication}
    return {"status": "RECORDED", "decision_id": record["decision_id"]}
