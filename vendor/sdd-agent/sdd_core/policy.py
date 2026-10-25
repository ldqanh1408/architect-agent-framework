from __future__ import annotations

import uuid

from .model import SddError, Status, digest, instant, utc_now
from .review import make_packet, obligations_for_review, verify_evidence
from .schema import EVIDENCE, validate

DECISION_KINDS = {"accept", "change_obligation", "false_positive", "waiver", "manual_review", "confirm_source", "transfer_owner"}
_CURRENT_BASE = object()


def effective_policy(snapshot, before=None):
    # A candidate cannot grant itself new approval powers before acceptance.
    return (before or snapshot).config["policy"]


def prepare_decision(store, snapshot, payload, before=None, now=None, base_acceptance=_CURRENT_BASE):
    now = now or utc_now()
    baseline = store.baseline()
    current_base = baseline["acceptance_id"] if baseline else None
    if base_acceptance is not _CURRENT_BASE and base_acceptance != current_base:
        raise SddError("DECISION_BASE_CONFLICT", "Baseline changed since the decision context was read", Status.STALE)
    if before is not None and (not baseline or before.digest != baseline["snapshot_digest"]):
        raise SddError("DECISION_BASE_CONFLICT", "Decision authority does not match the accepted baseline", Status.STALE)
    if before is None and baseline:
        before = store.load_snapshot(baseline["snapshot_digest"])
    required = {"kind", "actor", "reason", "scope", "snapshot_digest"}
    allowed = required | {"decision_id", "expires_at", "evidence", "finding_ids", "packet_digest", "observed_digest", "source_version", "observation_id", "attestation"}
    if not required <= payload.keys() or payload.keys() - allowed:
        raise SddError("DECISION_SCHEMA", "Decision fields do not match the versioned contract")
    if payload["kind"] not in DECISION_KINDS or not isinstance(payload["scope"], list) or not payload["scope"]:
        raise SddError("DECISION_SCHEMA", "A supported kind and nonempty scope are required")
    if payload["snapshot_digest"] != snapshot.digest:
        raise SddError("DECISION_STALE", "Decision targets a different snapshot", Status.STALE)
    policy = effective_policy(snapshot, before)
    if payload["actor"] not in policy["reviewers"] or payload["actor"] in snapshot.config.get("skills", {}):
        raise SddError("DECISION_ACTOR_DENIED", "Actor must be an explicitly configured human reviewer")
    if not isinstance(payload["reason"], str) or not payload["reason"].strip():
        raise SddError("DECISION_REASON_REQUIRED", "Record the decision rationale")
    if "expires_at" in payload:
        try:
            if instant(payload["expires_at"]) <= instant(now):
                raise ValueError("already expired")
        except ValueError as exc:
            raise SddError("DECISION_EXPIRY_INVALID", str(exc)) from exc
    kind = payload["kind"]
    if kind == "waiver" and (not policy.get("allow_waivers", False) or "expires_at" not in payload):
        raise SddError("WAIVER_DENIED", "Waivers require enabled policy and an expiry")
    if kind in {"manual_review", "false_positive"}:
        if not payload.get("evidence"):
            raise SddError("DECISION_EVIDENCE_REQUIRED", kind)
        obligations = {o["id"]: o for o in obligations_for_review(snapshot, before)}
        for scope in payload["scope"]:
            if scope not in obligations:
                raise SddError("DECISION_SCOPE_INVALID", scope)
            packet = make_packet(snapshot, obligations[scope], before)
            for evidence in payload["evidence"]:
                validate(evidence, EVIDENCE, "DECISION_EVIDENCE_INVALID")
                verify_evidence(evidence, packet)
            current = {(d["artifact_id"], d["revision"]) for d in packet["documents"] if d["side"] in {"candidate", "both"}}
            cited = {e["artifact_id"] for e in payload["evidence"] if (e["artifact_id"], e["revision"]) in current}
            if not set(packet["required_evidence_ids"]) <= cited:
                raise SddError("DECISION_EVIDENCE_REQUIRED", f"Cite every required source/consumer for {scope}")
            if not {tuple(p) for p in packet["required_baseline_pairs"]} <= {(e["artifact_id"], e["revision"]) for e in payload["evidence"]}:
                raise SddError("DECISION_EVIDENCE_REQUIRED", "Cite the previous accepted guarantee")
        if kind == "false_positive" and (not payload.get("finding_ids") or not payload.get("packet_digest")):
            raise SddError("DISPOSITION_FINDING_REQUIRED", "Bind false-positive disposition to finding IDs and packet")
    if kind == "confirm_source" and not all(payload.get(k) for k in ("observed_digest", "source_version", "observation_id")):
        raise SddError("SOURCE_EVIDENCE_REQUIRED", "Confirm the exact observation, content digest and pinned version")
    record = {**payload, "decision_id": payload.get("decision_id", "DEC-" + uuid.uuid4().hex), "created_at": now,
              "base_acceptance": current_base,
              "authority_policy_digest": digest(policy), "origin": "explicit-human-decision"}
    if kind == "confirm_source":
        from .freshness import confirmation_binding, source_binding
        if len(payload["scope"]) != 1:
            raise SddError("DECISION_SCOPE_INVALID", "Confirm one registered source per decision")
        source = next((s for s in snapshot.config.get("external_sources", []) if s["id"] == payload["scope"][0]), None)
        observation = store.read("observations", payload["observation_id"])
        if source is None or observation is None or observation.get("status") != "OBSERVED" or observation.get("source_binding") != source_binding(source) or observation.get("content_digest") != payload["observed_digest"] or source["version"] != payload["source_version"]:
            raise SddError("SOURCE_EVIDENCE_INVALID", "Confirmation must bind a successful observation of the registered source")
        record["confirmation_context_digest"] = confirmation_binding(snapshot, source)
        record["observation_sequence"] = observation.get("sequence", 0)
    return record


def verify_authority(store, record, policy):
    if policy.get("decision_authority", "local") == "external":
        verifier = getattr(store, "decision_verifier", None)
        if verifier is None:
            raise SddError("DECISION_VERIFIER_REQUIRED", "Use the configured host to verify signed decisions", Status.INCOMPLETE)
        problem = verifier(record)
        if problem:
            raise SddError("DECISION_SIGNATURE_INVALID", str(problem))


def record_decision(store, snapshot, payload, before=None, now=None, base_acceptance=_CURRENT_BASE):
    record = prepare_decision(store, snapshot, payload, before, now, base_acceptance)
    if before is None and store.baseline():
        before = store.load_snapshot(store.baseline()["snapshot_digest"])
    verify_authority(store, record, effective_policy(snapshot, before))
    with store.lock():
        baseline = store.baseline()
        if (baseline["acceptance_id"] if baseline else None) != record["base_acceptance"]:
            raise SddError("DECISION_BASE_CONFLICT", "Baseline changed while recording the decision", Status.STALE)
        store.write("decisions", record["decision_id"], record, immutable=True)
    return record


def valid_decisions(store, snapshot, before=None, now=None, base_acceptance=_CURRENT_BASE):
    now = instant(now or utc_now())
    policy = effective_policy(snapshot, before)
    if base_acceptance is _CURRENT_BASE:
        baseline = store.baseline()
        base_acceptance = baseline["acceptance_id"] if baseline else None
    if policy.get("decision_authority", "local") == "external" and getattr(store, "decision_verifier", None) is None:
        raise SddError("DECISION_VERIFIER_REQUIRED", "Use the configured host to verify signed decisions", Status.INCOMPLETE)
    output = []
    for decision in store.decisions():
        if decision.get("snapshot_digest") != snapshot.digest or decision.get("authority_policy_digest") != digest(policy):
            continue
        if "base_acceptance" not in decision or decision["base_acceptance"] != base_acceptance:
            continue
        if decision.get("actor") not in policy["reviewers"]:
            continue
        if "expires_at" in decision and instant(decision["expires_at"]) <= now:
            continue
        try:
            verify_authority(store, decision, policy)
        except SddError:
            continue  # a planted/modified row never acquires authority
        output.append(decision)
    return output


def covering(decisions, kind, subject):
    return [d for d in decisions if d["kind"] == kind and subject in d["scope"]]
